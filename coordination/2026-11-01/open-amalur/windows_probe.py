"""Run supplied PowerShell on the existing Windows SSH host; print its output."""
import base64
import subprocess
import sys

script = "$ProgressPreference='SilentlyContinue'\n[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()\n" + sys.stdin.read()
encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
result = subprocess.run(
    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "open-rune-windows",
     "powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
