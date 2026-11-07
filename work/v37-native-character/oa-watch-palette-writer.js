'use strict';
const mod=Process.mainModule;if(Process.arch!=='ia32'||mod.name.toLowerCase()!=='koa.exe')throw new Error('Wrong target');
if(Process.isDebuggerAttached())throw new Error('Existing debugger attached; leaving debug registers alone');
const address=ptr('0x3d4c4de0'),threads=Process.enumerateThreads(),armed=[];let complete=false,observed=false;
function cleanup(){for(const t of armed){try{t.unsetHardwareWatchpoint(3);}catch(e){send({kind:'cleanup-error',thread:t.id,message:String(e)});}}armed.length=0;Process.setExceptionHandler(null);}
Process.setExceptionHandler(e=>{
 const tid=Process.getCurrentThreadId();if(!armed.some(t=>t.id===tid)||!['breakpoint','single-step'].includes(e.type))return false;
 observed=true;const pc=e.context.pc;const data={kind:'draw',scope:'first write to first4bytes of one25-transform palette',watch_address:address.toString(),thread:tid,exception:e.type,pc:pc.toString(),original_pc:pc.compare(mod.base)>=0&&pc.compare(mod.base.add(mod.size))<0?'0x'+pc.sub(mod.base).add(0x400000).toUInt32().toString(16):null,registers:Object.fromEntries(['eax','ebx','ecx','edx','esi','edi','ebp','esp'].map(k=>[k,e.context[k].toString()])),fuzzy_stack_candidates:Thread.backtrace(e.context,Backtracer.FUZZY).map(x=>x.toString())};cleanup();send(data);complete=true;send({kind:'finished',complete:true,observed:true});return true;
});
try{for(const t of threads){t.setHardwareWatchpoint(3,address,4,'w');armed.push(t);}}
catch(e){cleanup();throw new Error('Write watchpoint not admitted: '+e);}
send({kind:'ready',watch_address:address.toString(),threads:armed.map(t=>t.id),duration_ms:1200});
setTimeout(()=>{if(complete)return;cleanup();complete=true;send({kind:'finished',complete:true,observed:false});},1200);
rpc.exports.status=()=>({complete,observed,armed:armed.length});rpc.exports.cleanup=()=>{cleanup();return {armed:0};};
