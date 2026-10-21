// Integration regression: isolated review may speak with an already-loaded local
// Kokoro worker; cold loading, installation, system TTS and LLM routes stay blocked.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
test('offline review permits only ready local Kokoro synthesis',async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'p3c-audio-guard-'));
 process.env.P3C_OFFLINE_TEST='1';process.env.AGENT_STANDUP_PREFS=path.join(dir,'prefs.json');
 const root=path.resolve(__dirname,'../../../artifacts/agent-standup-p3c/extension');
 const kokoro=require(path.join(root,'kokoro.js'));let ready=false,calls=0,generated;
 kokoro.status=()=>({ready});kokoro.synth=async(text,voice,speed,out)=>{calls++;generated=out;fs.writeFileSync(out,Buffer.alloc(44));};
 const app=require(path.join(root,'server.js'));const srv=app.start(0);
 await new Promise(r=>srv.once('listening',r));const base='http://127.0.0.1:'+srv.address().port;
 const request='/api/tts?engine=kokoro&voice=ff_siwis&text='+encodeURIComponent('Régression audio '+dir);
 try{
  assert.equal((await fetch(base+request)).status,403);assert.equal(calls,0);
  ready=true;const r=await fetch(base+request);assert.equal(r.status,200);await r.arrayBuffer();assert.equal(calls,1);
  for(const endpoint of ['/api/tts?engine=system','/api/warm','/api/translate','/api/kokoro/install'])assert.equal((await fetch(base+endpoint)).status,403,endpoint);
 }finally{
  await new Promise(r=>srv.close(r));app.shutdown();
  if(generated)for(const f of [generated,generated.replace(/\.part\.wav$/,'.wav')]){try{fs.unlinkSync(f)}catch{}}
  fs.rmSync(dir,{recursive:true,force:true});
 }
});
