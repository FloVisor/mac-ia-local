// Source counters are shown on participant tiles without adding them to parent totals.
function p3cTokenBadges() {
  for (const a of Object.values(S.agents || {})) {
    if(a.id==='main' || !a.p3c) continue;
    const el=document.querySelector('#t-'+a.id+' .tk');
    if(!el) continue;
    const u=a.p3c.usage;
    const valid=n=>typeof n==='number' && Number.isFinite(n) && n>=0;
    const input=u && (u.input_tokens ?? u.prompt_tokens), output=u && (u.output_tokens ?? u.completion_tokens);
    const total=u && (valid(u.total_tokens) ? u.total_tokens : valid(input) && valid(output) ? input+output : null);
    // Preserve any existing upstream counter when the structured source has none.
    if(!valid(total)) {if(!el.textContent) el.title='Tokens inconnus';continue;}
    el.textContent='⚡'+fmtTok(total);
    el.dataset.w=L('jetons','tokens');
    el.title=`${total} ${L('jetons','tokens')} · ${L('cumul du participant','participant total')}` +
      (valid(input) ? ` · ${L('entrée','input')} ${input}` : '') +
      (valid(output) ? ` · ${L('sortie','output')} ${output}` : '');
  }
}
// Loaded by the existing Live Call page. No second scene or network source.
function p3cMetadata() {
  if (!S.agents) return;
  for (const a of Object.values(S.agents)) {
    const m=a.p3c, tile=document.getElementById('t-'+a.id);
    if(!m || !tile) continue;
    let label=tile.querySelector('.p3c-meta');
    if(!label) {label=document.createElement('div');label.className='p3c-meta';tile.appendChild(label);}
    const state=S.live && atTail() ? m.state : (S.p3cStates?.[a.id] || 'unknown');
    label.textContent=`${m.category} · ${state}\n${m.model_label}`;
    label.title=`${m.task}\nExécuté confirmé : ${m.executed_label}\nFournisseur déclaré : ${m.provider_label}\nParent : ${m.parent || 'racine'}${m.error ? '\nErreur : '+m.error : ''}`;
    tile.dataset.p3cKind=m.kind;tile.dataset.p3cState=state;
    // Completed participants stay available in this Live Call's history.
    // Visibility belongs to paintStatus/prefs.vanish; history stays in S.agents.
  }
  p3cTokenBadges();
  if(S.detail && S.agents[S.detail]?.p3c) {
    const m=S.agents[S.detail].p3c, box=document.getElementById('detail');
    let pre=box.querySelector('.p3c-detail');
    if(!pre) {pre=document.createElement('pre');pre.className='p3c-detail';box.appendChild(pre);}
    pre.textContent=JSON.stringify({type:m.category,nom:S.agents[S.detail].name,tache:m.task,etat:m.state,
      modele:m.model_label,execute_confirme:m.executed_label,fournisseur_declare:m.provider_label,
      parent:m.parent,duree_ms:m.duration_ms,tokens:m.usage,cout_usd:m.cost_usd,erreur:m.error,
      transitions:m.history,trace_partielle:m.history_partial},null,2);
  }
}
function p3cSync(agents) {
  for(const a of agents || []) {
    if(S.agents[a.id]) { Object.assign(S.agents[a.id],a.p3c ? {p3c:a.p3c} : {}); }
    else { S.agents[a.id]=persona(twinOf(a));addTile(S.agents[a.id]); }
    if(a.p3c && a.name) {S.agents[a.id].name=a.name; const b=document.querySelector('#t-'+a.id+' .tag b');if(b)b.textContent=a.name;}
  }
  p3cMetadata();
}
setInterval(()=>{if(!document.hidden)p3cMetadata();},2000);

// History is selectable, but never advertised as an active call.
function p3cSessionChoices(board, sessions) {
  const result=[...board], known=new Set(board.map(r=>r.proj+'/'+r.id));
  for(const r of sessions) if(!known.has(r.proj+'/'+r.id)) {
    result.push({...r,state:'idle',historical:true,title:r.title+L(' · historique',' · historical')});
    known.add(r.proj+'/'+r.id);
  }
  return result;
}

function p3cApplyState(ev) {
  (S.p3cStates ||= {})[ev.agent]=ev.state;
  const done=['completed','failed','cancelled'].includes(ev.state);
  S.status[ev.agent]=done?'done':['running','queued'].includes(ev.state)?'working':'idle';
  if(done) {
    if(S.doneAt[ev.agent]==null) S.doneAt[ev.agent]=S.clock;
    if(S.waitOn[ev.to]) S.waitOn[ev.to].delete(ev.agent);
  } else {
    delete S.doneAt[ev.agent]; S.gone.delete(ev.agent);
  }
}
