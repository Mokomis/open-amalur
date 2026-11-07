'use strict';
const game=Process.getModuleByName('koa.exe');
if(Process.arch!=='ia32')throw Error('Expected PE32');
let events=0,readers=0,stopped=false;const seen=new Set();
const wanted=new Set([230417,226948,653633,237033,669809,1407259,1424437,655629]);
function bt(ctx){return Thread.backtrace(ctx,Backtracer.ACCURATE).slice(0,12).map(x=>({address:x.toString(),game_rva:x.compare(game.base)>=0&&x.compare(game.base.add(game.size))<0?x.sub(game.base).toString():null}));}
function emit(x){if(!stopped){send(x);if(++events>=64)stop('cap');}}
function stop(reason){if(stopped)return;stopped=true;Interceptor.detachAll();send({event:'trace_stopped',reason,events});}
for(const pair of [['kernel32.dll','ExitProcess'],['ntdll.dll','RtlExitUserProcess']]){
 const addr=Process.getModuleByName(pair[0]).getExportByName(pair[1]);
 Interceptor.attach(addr,{onEnter(args){emit({event:'native_exit',function:pair[1],code:args[0].toUInt32(),backtrace:bt(this.context)});}});
}
Interceptor.attach(game.base.add(0x670b80),{onEnter(args){const id=args[0].toUInt32();if(!wanted.has(id)||seen.has(id))return;seen.add(id);emit({event:'selected_type_lookup',id,manager:this.context.ecx.toString(),backtrace:bt(this.context)});}});
Interceptor.attach(game.base.add(0xc04a20),{onEnter(args){if(readers++>=8)return;let prefix=null;try{prefix=Array.from(new Uint8Array(args[0].readByteArray(48))).map(x=>x.toString(16).padStart(2,'0')).join('');}catch(e){prefix=String(e);}emit({event:'compiled_type_read',source:args[0].toString(),length:args[1].toUInt32(),prefix,backtrace:bt(this.context)});}});
send({event:'trace_ready',base:game.base.toString(),duration_ms:45000,max_events:64,scope:'property-reader entries and native exit; game-folder CWD'});
setTimeout(()=>stop('duration'),45000);
