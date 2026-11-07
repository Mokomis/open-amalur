'use strict';
const game=Process.getModuleByName('koa.exe');
if(Process.arch!=='ia32')throw Error('Expected pinned PE32 architecture');
let stopped=false,entries=0,captures=0;
const at=va=>game.base.add(va-0x400000);
function stop(reason){if(stopped)return;stopped=true;Interceptor.detachAll();send({event:'trace_stopped',reason,entries,captures});}
function stack(ctx){return Thread.backtrace(ctx,Backtracer.ACCURATE).slice(0,10).map(x=>({address:x.toString(),rva:x.compare(game.base)>=0&&x.compare(game.base.add(game.size))<0?x.sub(game.base).toString():null}));}
function words(p,n){const a=[];for(let i=0;i<n;i++)a.push(p.add(i*4).readU32());return a;}
for(const [module,name] of [['kernel32.dll','ExitProcess'],['ntdll.dll','RtlExitUserProcess']]){
 Interceptor.attach(Process.getModuleByName(module).getExportByName(name),{onEnter(args){send({event:'native_exit',name,code:args[0].toUInt32(),stack:stack(this.context)});}});
}
function capture(source,length,obj,ctx,kind){
 if(stopped)return;entries++;
 try{
  if(length<20||length>0x1000000)return;
  const n=Math.min(14,Math.floor(length/4)),header=words(source,n);
  const compiledMatch=n>=11&&(header[6]===237033||header[6]===147)&&(header[10]===226948||header[10]===76);
  const compactMatch=header[0]===226948&&header[4]===237033;
  const match=compiledMatch||compactMatch;
  if(!match&&captures>=6)return;
  captures++;
  let size=length;
  if(n>=2&&header[0]+header[1]+8<=length&&header[0]>=48)size=header[0]+header[1]+8;
  const msg={event:'type_reader_entry',entry_kind:kind,length,record_bytes:size,header,source:source.toString(),type_object:obj.toString(),type_vtable:obj.readPointer().toString(),matches_workbench_candidate:match,compact_prefix_match:compactMatch,stack:stack(ctx),prefix_hex:Array.from(new Uint8Array(source.readByteArray(Math.min(size,96)))).map(x=>x.toString(16).padStart(2,'0')).join('')};
  if(match&&size<=65536)msg.complete_source_hex=Array.from(new Uint8Array(source.readByteArray(size))).map(x=>x.toString(16).padStart(2,'0')).join('');
  send(msg);
 }catch(e){if(captures<6)send({event:'type_capture_error',error:String(e)});}
}
Interceptor.attach(at(0x1004a20),{onEnter(args){capture(args[0],args[1].toUInt32(),this.context.ecx,this.context,'type_vtable14');}});
Interceptor.attach(at(0x1001070),{onEnter(args){
 try{const walk=args[0],offset=walk.add(0x10).readU32(),length=walk.add(0xc).readU32();if(offset<=length)capture(walk.add(8).readPointer().add(offset),length-offset,this.context.ecx,this.context,'type_datawalk');}catch(e){if(captures<6)send({event:'walk_capture_error',error:String(e)});}
}});

function snapshot(){
 if(stopped)return;
 try{
  const mgr=at(0x19f4dec).readPointer();
  if(mgr.isNull()){send({event:'type_manager_not_ready'});return;}
  const assets=mgr.add(0x18).readPointer(),count=mgr.add(0x1c).readU32(),keys=mgr.add(0x6c).readPointer(),keyCount=mgr.add(0x70).readU32();
  send({event:'manager_snapshot',manager:mgr.toString(),count,keyCount,assets:assets.toString(),keys:keys.toString()});
  if(count>50000||keyCount>50000||assets.isNull()||keys.isNull())return;
  for(let i=0;i<Math.min(count,keyCount);i++){
   const id=keys.add(i*4).readU32();if(id!==230417&&id!==226948)continue;
   const object=assets.add(i*4).readPointer();if(object.isNull()){send({event:'selected_type_not_loaded',id,index:i});continue;}
   const payload=object.add(4).readPointer();
   if(payload.isNull()){send({event:'selected_type_no_payload',id,index:i});continue;}
   const header=words(payload,12),partCount=header[10];
   const result={event:'selected_runtime_type',id,index:i,object:object.toString(),payload:payload.toString(),header,parts:[]};
   const parentIndex=header[8];if(parentIndex<keyCount)result.parent_source_key=keys.add(parentIndex*4).readU32();
   const luaMgr=at(0x19f4d34).readPointer();
   if(!luaMgr.isNull()){
    const luaCount=luaMgr.add(0x70).readU32(),luaKeys=luaMgr.add(0x6c).readPointer();
    if(luaCount<50000&&header[4]<luaCount&&!luaKeys.isNull())result.script_source_key=luaKeys.add(header[4]*4).readU32();
   }
   if(partCount<=43){
    const base=payload.add(0x24).readPointer(),offsets=payload.add(0x2c).readPointer();
    if(!base.isNull()&&!offsets.isNull())for(let j=0;j<partCount;j++){
     const relative=offsets.add(j*4).readU32();if(relative>0x100000)throw Error('Component offset cap');
     const p=base.add(relative);result.parts.push({kind:p.readU32(),offset:relative,prefix:words(p,3)});
    }
   }
   send(result);
  }
 }catch(e){send({event:'snapshot_error',error:String(e)});}
}
send({event:'trace_ready',base:game.base.toString(),reader_bytes:Array.from(new Uint8Array(at(0x1001070).readByteArray(16))).map(x=>x.toString(16).padStart(2,'0')).join(''),duration_ms:45000,scope:'native Type entry and manager observations; no gameplay input or game-data writes'});
setTimeout(snapshot,5000);setTimeout(snapshot,20000);setTimeout(()=>stop('duration'),45000);
