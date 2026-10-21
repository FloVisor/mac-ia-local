const fs=require('fs');const path=require('path');const assert=require('assert/strict');
const work=path.resolve(__dirname,'../../../artifacts/agent-standup-p3c');
const puppeteer=require(path.join(work,'browser-deps/node_modules/puppeteer-core'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const ready=path.join(work,'vscode-host.json');
 for(let n=0;n<30&&!fs.existsSync(ready);n++)await wait(1000);
 assert(fs.existsSync(ready),'VS Code host ready');const host=JSON.parse(fs.readFileSync(ready));
 const browser=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--mute-audio']});
 try {
 const page=await browser.newPage();await page.setViewport({width:1600,height:1000});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setRequestInterception(true);page.on('request',r=>r.url().startsWith(host.base)||r.url().startsWith('data:')?r.continue():r.abort());
 const url=id=>`${host.base}/?live=1&proj=_codex&pin=${id}&pproj=_codex`;
 await page.goto(url(host.nativeRoot),{waitUntil:'networkidle2'});
 await page.waitForFunction(()=>Object.values(S.agents||{}).filter(a=>a.type==='codex-native').length===3,{timeout:15000});
 await page.waitForFunction(()=>document.querySelectorAll('.p3c-meta').length>=4,{timeout:10000});
 const native=await page.evaluate(()=>Object.values(S.agents).filter(a=>a.p3c).map(a=>({id:a.id,name:a.name,type:a.type,parent:a.parent,state:a.p3c.state,model:a.p3c.model_label,visible:!!document.getElementById('t-'+a.id)?.getBoundingClientRect().height,svg:!!document.querySelector('#t-'+a.id+' svg'),model_visible:(()=>{const t=document.getElementById('t-'+a.id)?.getBoundingClientRect(),m=document.querySelector('#t-'+a.id+' .p3c-meta')?.getBoundingClientRect();return !!(t&&m&&m.top>=t.top&&m.bottom<=t.bottom);})()})));
 assert.equal(native.filter(a=>a.type==='codex-native'&&a.svg&&a.visible&&a.model_visible).length,3);
 for(const a of native.filter(a=>a.type==='codex-native'))assert.equal(a.parent,'main');
 await page.screenshot({path:path.join(work,'live-call-native.png'),fullPage:false});
 await page.evaluate(()=>{document.body.classList.add('tree');renderTree();});
 assert((await page.$eval('#tree',el=>el.textContent)).includes('Lovelace'));
 await page.screenshot({path:path.join(work,'live-call-hierarchy.png'),fullPage:false});
 await page.goto(url(host.routerRoot),{waitUntil:'networkidle2'});
 await page.waitForFunction(()=>Object.values(S.agents||{}).some(a=>a.type==='mcp-delegation'),{timeout:15000});
 await page.waitForFunction(()=>document.querySelector('[data-p3c-kind=mcp_delegation]'),{timeout:10000});
 const mcp=await page.evaluate(()=>{const a=Object.values(S.agents).find(a=>a.type==='mcp-delegation');openDetail(a.id);p3cMetadata();return {id:a.id,parent:a.parent,kind:a.p3c.category,state:a.p3c.state,executed:a.p3c.executed_label,tokens:a.p3c.usage?.total_tokens,transitions:a.p3c.history.length,meta:document.querySelector('#t-'+a.id+' .p3c-meta').textContent};});
 assert.equal(mcp.kind,'Tâche MCP · llm-router');assert.equal(mcp.state,'failed');assert.equal(mcp.executed,'inconnu');assert.equal(mcp.tokens,37);assert(mcp.transitions>=3);
 await page.screenshot({path:path.join(work,'live-call-mcp.png'),fullPage:false});
 await page.reload({waitUntil:'networkidle2'});
 await page.waitForFunction(()=>Object.values(S.agents||{}).some(a=>a.type==='mcp-delegation'),{timeout:10000});
 assert.equal(await page.evaluate(()=>Object.values(S.agents).filter(a=>a.type==='mcp-delegation').length),1);
 // Preserve existing replay and built-in demonstration in the very same renderer.
 await page.goto(host.base+'/?demo=1',{waitUntil:'networkidle2'});
 await page.waitForFunction(()=>!!document.querySelector('#stage svg'),{timeout:10000});
 const result={status:'PASS',native,mcp,reload_no_duplicates:true,existing_scene_svg:true,page_errors:errors,host_port:host.port};
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(work,'visual-done.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({status:'PASS',native:3,mcp:1,page_errors:0}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
