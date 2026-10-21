const vscode = require('vscode');
const {spawn} = require('node:child_process');
const path = require('node:path');

function forest(nodes, filter = '') {
  const byId = new Map(nodes.map(n => [n.id, n]));
  const visible = new Set();
  for (const n of nodes) {
    if (![n.id,n.task_id,n.model,n.alias,n.provider,n.kind,n.profile].some(v => String(v || '').toLowerCase().includes(filter.toLowerCase()))) continue;
    let cur = n;
    const seen = new Set();
    while (cur && !seen.has(cur.id)) { seen.add(cur.id); visible.add(cur.id); cur = byId.get(cur.parent); }
  }
  // An edge is only used if its full ancestry is acyclic.
  const parentOf = n => {
    let cur = n; const seen = new Set([n.id]);
    while (cur.parent && byId.has(cur.parent)) { if (seen.has(cur.parent)) return null; seen.add(cur.parent); cur = byId.get(cur.parent); }
    return byId.has(n.parent) ? n.parent : null;
  };
  const roots = [], children = new Map();
  for (const n of nodes.filter(n => visible.has(n.id))) {
    const parent = parentOf(n);
    if (!parent) roots.push(n);
    else { if (!children.has(parent)) children.set(parent, []); children.get(parent).push(n); }
  }
  return {roots, children};
}

function activate(ctx) {
  const changed = new vscode.EventEmitter();
  let nodes = [], filter = '', data = forest([]), pending = false, buffer = '', disposed = false;
  const output = vscode.window.createOutputChannel('P3-C Observer');
  const worker = spawn('/usr/bin/env', ['python3', path.join(ctx.extensionPath,'collector.py')], {
    stdio:['pipe','pipe','pipe'], env:{PATH:process.env.PATH, HOME:process.env.HOME, ...(process.env.CODEX_HOME ? {CODEX_HOME:process.env.CODEX_HOME} : {})}
  });
  const provider = {
    onDidChangeTreeData:changed.event,
    getChildren:n => n ? (data.children.get(n.id) || []) : data.roots,
    getTreeItem(n) {
      const title = n.kind === 'session_reference' ? 'Session référencée · trace absente' : n.kind === 'mcp_delegation' ? `llm-router / ${n.profile || 'inconnu'}` : n.kind === 'native_subagent' ? 'Sous-agent Codex natif' : `Codex · ${n.source || 'source inconnue'}`;
      const model = n.model || n.alias || 'modèle inconnu';
      const duration = n.duration_ms == null ? '?' : `${Math.round(n.duration_ms / 1000)} s`;
      const item = new vscode.TreeItem(title, data.children.has(n.id) ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None);
      item.id = n.id;
      item.description = `${n.state} · ${model} · ${duration}`;
      item.tooltip = `${n.id}\nFournisseur déclaré : ${n.provider || 'inconnu'}\nModèle exécuté confirmé : ${n.actual_model || 'inconnu'}\n${n.error || n.activity || ''}\nConnexion : inconnue${n.parent && !nodes.some(p=>p.id===n.parent) ? '\nParent hors fenêtre : '+n.parent : ''}`;
      item.iconPath = new vscode.ThemeIcon(({running:'sync~spin',completed:'pass',failed:'error',cancelled:'circle-slash',queued:'clock'})[n.state] || 'question');
      item.command = {command:'p3c.details',title:'Métadonnées',arguments:[n]};
      return item;
    }
  };
  const view = vscode.window.createTreeView('p3c.activity',{treeDataProvider:provider,showCollapseAll:true});
  const refresh = () => { if (!disposed && !pending && worker.stdin.writable) { pending = true; worker.stdin.write('refresh\n'); } };
  worker.stdout.on('data', chunk => {
    buffer += chunk.toString();
    if (buffer.length > 4*1024*1024) { buffer=''; pending=false; view.message='Réponse trop volumineuse'; return; }
    let i;
    while ((i=buffer.indexOf('\n')) >= 0) {
      const line=buffer.slice(0,i); buffer=buffer.slice(i+1); pending=false;
      try {
        const snapshot=JSON.parse(line); nodes=snapshot.nodes; data=forest(nodes,filter);
        view.message=`Codex uniquement · 5 s · ${nodes.length} objets · ${snapshot.errors.join(', ') || 'lecture seule'}${filter ? ' · filtre : '+filter : ''}`;
        changed.fire();
      } catch { view.message='Métadonnées illisibles'; }
    }
  });
  worker.stderr.on('data', () => { output.appendLine('collector_stderr (contenu masqué)'); });
  worker.on('error', () => { pending=false; view.message='Collecteur indisponible : Python 3 requis'; });
  worker.on('exit', () => { pending=false; if (!disposed) view.message='Collecteur arrêté'; });
  worker.stdin.on('error', () => { pending=false; });
  const timer=setInterval(() => { if (view.visible) refresh(); },5000);
  ctx.subscriptions.push(output,changed,view,
    view.onDidChangeVisibility(e => { if(e.visible) refresh(); }),
    vscode.commands.registerCommand('p3c.refresh',refresh),
    vscode.commands.registerCommand('p3c.filter',async () => { const v=await vscode.window.showInputBox({prompt:'Session, modèle, fournisseur déclaré ou profil ; vide pour tout afficher',value:filter}); if(v!==undefined) {filter=v;data=forest(nodes,filter);changed.fire();} }),
    vscode.commands.registerCommand('p3c.details',async n => { if(!n) return; const d=await vscode.workspace.openTextDocument({language:'json',content:JSON.stringify(n,null,2)}); await vscode.window.showTextDocument(d,{preview:true}); }),
    {dispose(){disposed=true;clearInterval(timer);worker.kill();}}
  );
  refresh();
  return {snapshot:()=>nodes,provider,refresh,forest};
}
module.exports={activate,forest};
