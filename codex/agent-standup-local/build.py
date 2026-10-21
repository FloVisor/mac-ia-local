"""Reproducible derivative from pinned upstream; fail on patch context drift."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
base=json.loads((HERE/'BASE.json').read_text())
args=argparse.ArgumentParser()
args.add_argument('--source',type=Path)
args.add_argument('--output',type=Path)
opts=args.parse_args()
work=opts.output.resolve() if opts.output else REPO/'artifacts/agent-standup-p3c'
work.mkdir(parents=True,exist_ok=True)
source=opts.source.resolve() if opts.source else work/'source'/('agent-standup-'+base['commit'])
out=work/'extension'
if out.exists():shutil.rmtree(out)
# Runtime assets kept in ignored artifacts, not duplicated in the maintained patch.
ignore=shutil.ignore_patterns('.git','node_modules','test','scripts','website','landing','desktop','plugin','.github')
shutil.copytree(source,out,ignore=ignore)
changes={}
def edit(name,fn):
 old=(source/name).read_text();new=fn(old)
 (out/name).write_text(new)
 if new!=old:changes[name]=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
def replace(s,old,new):
 if s.count(old)!=1:raise ValueError(f'Patch context drift ({s.count(old)} matches): {old[:90]}')
 return s.replace(old,new)

def server(s):
 s=replace(s,"const codex = require('./codex.js');", "const p3c = require('./p3c.js');\nconst codex = require('./codex.js');")
 s=replace(s,"const vibe = require('./vibe.js');", "p3c.install(codex);\nconst vibe = require('./vibe.js');")
 s=replace(s,"const key = proj + '/' + id, st = stamp(proj, id),", "const key = proj + '/' + id, st = stamp(proj, id) + (proj === codex.PROJ ? ':' + p3c.revision : ''),")
 s=replace(s,"const sigOf = (e) => e.kind +", "const sigOf = (e) => e.kind === 'p3cstate' ? JSON.stringify(e) : e.kind +")
 s=replace(s,"  if (!fs.existsSync(mainFile)) throw new Error('session not found');", "  if (!fs.existsSync(mainFile)) { if (proj === codex.PROJ && p3c.hasSession(id)) return p3c.enrich({id,proj,agents:[{id:'main',role:'Session référencée · trace absente',type:'main'}],events:[],durationMs:0}); throw new Error('session not found'); }")
 s=replace(s,"  return { id, proj, agents: Object.values(agents),", "  const result = { id, proj, agents: Object.values(agents),")
 s=replace(s,"...(cost ? { cost } : {}) };\n}", "...(cost ? { cost } : {}) };\n  return proj === codex.PROJ ? p3c.enrich(result) : result;\n}")
 s=replace(s,"!!guard(() => sourceOf(c.proj).fileOf(c.id), null)", "(!!guard(() => sourceOf(c.proj).fileOf(c.id), null) || (c.proj === codex.PROJ && p3c.hasSession(c.id)))")
 s=replace(s,"sourceOf(proj) ? sourceOf(proj).fileOf(sid) :", "sourceOf(proj) ? (sourceOf(proj).fileOf(sid) || (proj === codex.PROJ && p3c.hasSession(sid))) :")
 s=replace(s,"const shutdown = () => { trWorkers", "const shutdown = () => { p3c.shutdown(); trWorkers")
 s=replace(s,"return String(j.version || '');", "return String(j.p3c_upstream_version || j.version || '');")
 # Isolated smoke mode blocks inference/translation endpoints; normal features remain.
 s=replace(s,"  const readBody = (cb, max = 262144) => {", "  if (process.env.P3C_OFFLINE_TEST === '1' && ['/api/translate','/api/quips','/api/warm','/api/tts','/api/kokoro/install','/api/packs/buy','/api/packs/claim'].includes(url.pathname) && !(url.pathname === '/api/tts' && url.searchParams.get('engine') === 'kokoro' && kokoro.status().ready)) return json({error:'disabled_in_isolated_test'},403);\n  const readBody = (cb, max = 262144) => {")
 s=replace(s,"process.on('disconnect', () => { try { shutdown();", "process.on('disconnect', () => { p3c.shutdown(); try { shutdown();")
 return s

def ui(s):
 s=replace(s,"  let sel = 0, shown = [];", "  try { rows = p3cSessionChoices(rows, await (await fetch('/api/sessions')).json()); } catch {}\n  let sel = 0, shown = [];")
 s=replace(s,"  camTok(); if (S.events.length", "  p3cTokenBadges(); camTok(); if (S.events.length")
 s=replace(s,"function paintStatus() {", "function paintStatus() {\n  p3cMetadata();")
 s=replace(s,"const applyStatus = (ev) => {", "const applyStatus = (ev) => {\n  if (ev.kind === 'p3cstate') { p3cApplyState(ev); return; }")
 s=replace(s,"if (e.kind === 'report' || e.kind === 'finish') doneIdx[e.agent] = i;", "if (e.kind === 'report' || e.kind === 'finish' || (e.kind === 'p3cstate' && ['completed','failed','cancelled'].includes(e.state))) doneIdx[e.agent] = i;")
 s=replace(s,"function agentState(id, now) {", "function agentState(id, now) {\n  const m=S.agents[id]?.p3c; if(m) { const state=S.live && atTail()?m.state:(S.p3cStates?.[id] || 'unknown');return {k:state==='running'?'working':['completed','failed','cancelled'].includes(state)?'done':'idle',txt:state}; }")
 s=replace(s,"  pause(); const mine = (S.loadN", "  S.p3cStates={};\n  pause(); const mine = (S.loadN")
 s=replace(s,"S.seq = d.seq; if (d.marks)", "p3cSync(d.agents); S.seq = d.seq; if (d.marks)")
 # Do not translate/synthesize new technical metadata events.
 s=replace(s,"const baseText = (ev, max) => short(ev.text,", "const baseText = (ev, max) => ev.p3c ? '' : short(ev.text,")
 s=replace(s,"<script>", "<script src=\"/p3c-ui.js\"></script>\n<script>")
 s=replace(s,"</body>", "<style>.p3c-meta{position:absolute;z-index:6;left:4px;right:4px;bottom:25px;white-space:pre-line;font-size:10px;line-height:1.35;padding:4px 6px;border-radius:5px;background:#111827e8;color:#e5e7fa;overflow-wrap:anywhere;pointer-events:none}.tile[data-p3c-state=failed] .p3c-meta{color:#ffada3}.p3c-detail{white-space:pre-wrap;font-size:12px;padding:12px}.tile[data-p3c-state=failed]{outline:2px solid #ff7a6b}</style>\n</body>")
 return s
edit('server.js',server)
edit('public/index.html',ui)
# Namespaced commands/settings/views prevent collision. Official copy untouched.
edit('extension.js',lambda s:"process.env.AGENT_STANDUP_PREFS ||= require('path').join(require('os').homedir(), '.config', 'agent-standup-p3c', 'prefs.json');\n"+s.replace('agentStandup','p3cStandup'))
p=json.loads((source/'package.json').read_text());p=json.loads(json.dumps(p).replace('agentStandup','p3cStandup'))
p.update(name='agent-standup-p3c',publisher='local-xithi',version=base['local_version'],displayName='Agent Standup P3-C · isolé')
p['p3c_upstream_version']=base['version']
p.pop('__metadata',None)
(out/'package.json').write_text(json.dumps(p,indent=2)+'\n')
changes['package.json']=''.join(difflib.unified_diff((source/'package.json').read_text().splitlines(True),(out/'package.json').read_text().splitlines(True),fromfile='a/package.json',tofile='b/package.json'))
shutil.copy2(source/'LICENSE',out/'LICENSE.txt')
shutil.copy2(HERE/'p3c.js',out/'p3c.js');shutil.copy2(HERE/'p3c-ui.js',out/'public/p3c-ui.js')
(out/'observer').mkdir(exist_ok=True)
shutil.copy2(HERE.parent/'agent-observer/collector.py',out/'observer/collector.py')
shutil.copy2(HERE/'collector_runner.py',out/'observer/collector_runner.py')
(work/'local-changes.patch').write_text(''.join(changes.values()))
for name in ['server.js','codex.js','vibe.js','extension.js','p3c.js','public/p3c-ui.js']:
 subprocess.run(['node','--check',str(out/name)],check=True,capture_output=True)
# Check the original inline browser JS as well as the added module.
html=(out/'public/index.html').read_text();start=html.index('<script>')+8;end=html.index('</script>',start)
(work/'inline-check.js').write_text(html[start:end]);subprocess.run(['node','--check',str(work/'inline-check.js')],check=True)
manifest=f'''<?xml version="1.0"?><PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011"><Metadata><Identity Language="en-US" Id="{p['name']}" Version="{p['version']}" Publisher="{p['publisher']}"/><DisplayName>Agent Standup P3-C</DisplayName><Description xml:space="preserve">Isolated MIT derivative</Description><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.80.0"/></Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/><Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>'''
vsix=work/'agent-standup-p3c.vsix'
with zipfile.ZipFile(vsix,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('extension.vsixmanifest',manifest)
 z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="vsixmanifest" ContentType="text/xml"/><Default Extension="js" ContentType="application/javascript"/></Types>')
 for f in out.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:z.write(f,'extension/'+str(f.relative_to(out)))
print(json.dumps({'extension':str(out),'vsix':str(vsix),'patched_files':list(changes),'sha256':hashlib.sha256(vsix.read_bytes()).hexdigest()},indent=2))
