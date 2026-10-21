const vscode=require('vscode');
const fs=require('fs');
const path=require('path');
const assert=require('assert/strict');
const work=path.resolve(__dirname,'../../../artifacts/agent-standup-p3c');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
exports.run=async()=>{
 const ext=vscode.extensions.getExtension('local-xithi.agent-standup-p3c');assert(ext);
 await ext.activate();await vscode.commands.executeCommand('p3cStandup.open');
 const module=require(path.join(ext.extensionPath,'extension.js'));
 const {port}=await module._server();assert(port>0);
 const base='http://127.0.0.1:'+port;
 const nativeRoot='01a13a9b-ac78-7b00-86eb-a1a8ca464d78',routerRoot='01a15de3-b087-75d2-bc09-b064732582a0';
 let native,router;
 for(let i=0;i<20;i++) {
  await fetch(base+'/api/sessions');
  native=await (await fetch(base+'/api/session?proj=_codex&id='+nativeRoot)).json();
  router=await (await fetch(base+'/api/session?proj=_codex&id='+routerRoot)).json();
  if(native.agents?.filter(a=>a.type==='codex-native').length===3 && router.agents?.some(a=>a.type==='mcp-delegation'))break;
  await sleep(1000);
 }
 assert.equal(native.agents.filter(a=>a.type==='codex-native').length,3);
 assert(router.agents.some(a=>a.type==='mcp-delegation'));
 fs.writeFileSync(path.join(work,'vscode-host.json'),JSON.stringify({status:'READY',port,base,nativeRoot,routerRoot,extension:ext.id,version:ext.packageJSON.version,native:3,mcp:1,official_present:!!vscode.extensions.getExtension('doublegeste.agent-standup')},null,2));
 const deadline=Date.now()+180000;
 while(Date.now()<deadline && !fs.existsSync(path.join(work,'visual-done.json')))await sleep(500);
 assert(fs.existsSync(path.join(work,'visual-done.json')),'visual validation completed');
 const result=JSON.parse(fs.readFileSync(path.join(work,'visual-done.json')));assert.equal(result.status,'PASS');
 fs.writeFileSync(path.join(work,'vscode-result.json'),JSON.stringify({status:'PASS',native:3,mcp:1,visual:true,isolated:true},null,2));
};
