'use strict';
const wanted = new Set([230417,1407259,1424437,655629,226948,653633,237033,669809,361206,361222,361223,707989,376223,406194,1925962,1932735,1720675,1743502,1925968,459540,1937115]);
const game=Process.getModuleByName('koa.exe');let count=0,stopped=false;const seen=new Set();
function stop(reason){if(stopped)return;stopped=true;Interceptor.detachAll();send({event:'trace_stopped',reason:reason,events:count});}
if(Process.arch!=='ia32')throw Error('Expected selected PE32 game');
send({event:'trace_ready',module:'koa.exe',arch:Process.arch,base:game.base.toString(),scope:'selected asset IDs at a70b80; no gameplay input or data writes',duration_ms:45000,max_events:64});
Interceptor.attach(game.base.add(0x670b80),{onEnter(args){
 if(stopped)return;const id=args[0].toUInt32();if(!wanted.has(id))return;
 const key=id+':'+this.returnAddress.toString();if(seen.has(key))return;seen.add(key);
 const addresses=Thread.backtrace(this.context,Backtracer.ACCURATE).slice(0,12).map(a=>({address:a.toString(),game_rva:a.compare(game.base)>=0&&a.compare(game.base.add(game.size))<0?a.sub(game.base).toString():null}));
 send({event:'selected_type_lookup',id:id,caller:this.returnAddress.toString(),caller_rva:this.returnAddress.sub(game.base).toString(),manager:this.context.ecx.toString(),backtrace:addresses});
 if(++count>=64)stop('event_cap');
}});
setTimeout(()=>stop('duration'),45000);
