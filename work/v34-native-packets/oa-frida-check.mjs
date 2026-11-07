import {pathToFileURL} from 'node:url';
const root='C:/Users/rwill/Documents/Opem Amalur';
const frida=await import(pathToFileURL(root+'/tools/rea-frida/node_modules/frida/build/src/frida.js'));
const d=await frida.getLocalDevice();const ps=await d.enumerateProcesses();
console.log(JSON.stringify({device:d.id,game:ps.filter(x=>x.name.toLowerCase()==='koa.exe').map(x=>({pid:x.pid,name:x.name})),fridaPackage:'17.23.2'}));
