"""Sample total Windows physical RAM and total device VRAM during a bounded task."""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import threading
import time


class MemoryStatus(ctypes.Structure):
    _fields_ = [('length',wintypes.DWORD),('load',wintypes.DWORD)] + [
        (name,ctypes.c_ulonglong) for name in
        ['total_phys','available_phys','total_page','available_page','total_virtual','available_virtual','extended']]


def physical_memory():
    m = MemoryStatus()
    m.length = ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        raise ctypes.WinError()
    return {'ram_used_mib':(m.total_phys-m.available_phys)/1048576,
            'ram_available_mib':m.available_phys/1048576,
            'ram_total_mib':m.total_phys/1048576}


class Monitor:
    def __init__(self, path):
        self.path = Path(path)
        self.stop_event = threading.Event()
        self.samples = []

    def start(self):
        def collect():
            with self.path.open('w',encoding='utf-8') as f:
                while not self.stop_event.is_set():
                    row = {'unix':time.time(),**physical_memory()}
                    try:
                        r = subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.total,utilization.gpu',
                                            '--format=csv,noheader,nounits'], capture_output=True,text=True,timeout=5)
                        values = r.stdout.splitlines()[0].split(',')
                        row.update(vram_used_mib=float(values[0]),vram_total_mib=float(values[1]),gpu_util_percent=float(values[2]))
                    except Exception as e:
                        row['gpu_error'] = type(e).__name__
                    self.samples.append(row)
                    f.write(json.dumps(row)+'\n');f.flush()
                    self.stop_event.wait(1)
        self.thread = threading.Thread(target=collect,daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set();self.thread.join(timeout=7)
        if not self.samples:return {}
        return {'sampling_interval_seconds':1,'sample_count':len(self.samples),
                'measurement_scope':'whole-PC physical RAM and whole-device VRAM; not process-exclusive',
                'baseline_ram_used_mib':self.samples[0]['ram_used_mib'],
                'peak_ram_used_mib':max(x['ram_used_mib'] for x in self.samples),
                'minimum_ram_available_mib':min(x['ram_available_mib'] for x in self.samples),
                'baseline_vram_used_mib':self.samples[0].get('vram_used_mib'),
                'peak_vram_used_mib':max((x.get('vram_used_mib',0) for x in self.samples))}
