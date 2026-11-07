'use strict';
const mod=Process.mainModule;
if(Process.arch!=='ia32'||mod.name.toLowerCase()!=='koa.exe')throw new Error('Expected authorized32bit koa.exe target');
const target=mod.base.add(0xc961e0-0x400000);
const prefix=Array.from(new Uint8Array(target.readByteArray(16))).map(x=>x.toString(16).padStart(2,'0')).join('');
const expected=[0x81,0xec,0x50,1,0,0,0xa1,0x3c,0x71,0x97,1,0x33,0xc4,0x89,0x84,0x24];
const cookie=mod.base.add(0x0197713c-0x400000).toUInt32();for(let i=0;i<4;++i)expected[7+i]=(cookie>>>(i*8))&255;
if(prefix!==expected.map(x=>x.toString(16).padStart(2,'0')).join(''))throw new Error('Native entry identity differs after ASLR relocation: '+prefix);
const listeners=[];let active=null,complete=false,calls=0,eligible=0;
function event(p,data){send(p,data);}
function span(name,address,size){event({kind:'span',name,address:address.toString(),size},address.readByteArray(size));return {name,address:address.toString(),size};}
function add(slot,name,decode){
 const address=active.vtable.add(slot*4).readPointer();
 const listener=Interceptor.attach(address,{onEnter(args){
  if(!active||complete||this.threadId!==active.thread)return;
  try {
   if(name==='IASetVertexBuffers') {
    const holder=ptr(active.holder),strides=holder.add(0x2c).readPointer();
    active.spans=active.spans.filter(s=>s.name!=='holder_entry'&&s.name!=='strides_entry');
    active.spans.push(span('holder',holder,0x30),span('strides',strides,0xe0));
    active.snapshot_phase='before geometry submission, after native material/shader setup';
   }
   const record={name,implementation:address.toString(),...decode(args)};active.events.push(record);
   if(name==='DrawIndexed'||name==='Draw') {complete=true;event({kind:'draw',...active, vtable:active.vtable.toString()});}
  }catch(e){event({kind:'error',where:name,message:String(e)});}
 }});listeners.push(listener);
}
const root=Interceptor.attach(target,{
 onEnter(args){
  ++calls;if(active||complete)return;
  try{
   const begin=args[0],end=args[1],tables=args[2],state=args[3];const count=end.sub(begin).toUInt32()/8;
   if(!Number.isInteger(count)||count<1||count>20000)return;
   const packet=begin.add(4).readPointer();if(packet.isNull()||packet.readU32()!==0)return;
   const material=packet.add(8).readPointer();if(material.isNull()||material.add(0x10).readPointer().isNull())return;
   ++eligible;const holder=state.readPointer(),ctx=holder.readPointer(),geometry=packet.add(0x2c).readPointer();
   const strides=holder.add(0x2c).readPointer(),instance=tables.add(0x20).readPointer();
   if(geometry.isNull()||strides.isNull()||instance.isNull())return;
   active={thread:this.threadId,count,packet:packet.toString(),tables:tables.toString(),holder:holder.toString(),context:ctx.toString(),vtable:ctx.readPointer(),events:[],spans:[]};this.isTarget=true;
   for(const [name,address,size] of [['packet',packet,0x30],['tables',tables,0x24],['holder_entry',holder,0x30],['geometry',geometry,0x30],['strides_entry',strides,0xe0],['instance',instance,0x10]])active.spans.push(span(name,address,size));
   add(18,'IASetVertexBuffers',a=>{const n=a[2].toUInt32();if(n>16)throw new Error('Too many buffers');return {start:a[1].toUInt32(),count:n,buffers:Array.from({length:n},(_,i)=>a[3].add(i*4).readPointer().toString()),strides:Array.from({length:n},(_,i)=>a[4].add(i*4).readU32()),offsets:Array.from({length:n},(_,i)=>a[5].add(i*4).readU32())};});
   add(19,'IASetIndexBuffer',a=>({buffer:a[1].toString(),format:a[2].toUInt32(),offset:a[3].toUInt32()}));
   add(24,'IASetPrimitiveTopology',a=>({topology:a[1].toUInt32()}));
   add(12,'DrawIndexed',a=>({count:a[1].toUInt32(),first:a[2].toUInt32(),base:a[3].toInt32()}));
   add(13,'Draw',a=>({count:a[1].toUInt32(),first:a[2].toUInt32()}));
   event({kind:'armed',target:target.toString(),thread:this.threadId,count});
  }catch(e){event({kind:'error',where:'entry',message:String(e)});active=null;}
 },
 onLeave(){if(this.isTarget){if(!complete)event({kind:'no-draw',events:active.events});for(const l of listeners)l.detach();root.detach();event({kind:'finished',calls,eligible,complete});}}
});
event({kind:'ready',pid:Process.id,module:mod.path,base:mod.base.toString(),target:target.toString(),prefix,frida:Frida.version});

rpc.exports.status=()=>({calls,eligible,complete,active:!!active});
