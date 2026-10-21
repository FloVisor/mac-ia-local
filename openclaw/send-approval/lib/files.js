import fs from 'node:fs';
import path from 'node:path';
import { digest, deny, request } from './approval.js';
export function canonical(value, workspace) {
  if (typeof value !== 'string' || !value || /[\0\r\n]/u.test(value)) throw Error('Chemin invalide');
  const absolute = path.resolve(workspace, value.startsWith('~/') ? path.join(process.env.HOME, value.slice(2)) : value);
  let parent = absolute; const missing = [];
  while (!fs.existsSync(parent)) {
    // existsSync returns false for dangling symlinks: never treat one as a missing file.
    try { if (fs.lstatSync(parent).isSymbolicLink()) throw Error('Lien symbolique pendant'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
    const next = path.dirname(parent); if (next === parent) throw Error('Racine absente');
    missing.unshift(path.basename(parent)); parent = next;
  }
  return path.join(fs.realpathSync(parent), ...missing);
}
export const within = (file, root) => file === root || file.startsWith(`${root}${path.sep}`);
export function memoryPath(file, root) {
  return file === path.join(root, 'USER.md') || file === path.join(root, 'MEMORY.md') || within(file, path.join(root, 'memory'));
}
export function fingerprint(file) {
  if (!fs.existsSync(file)) return 'absent';
  const s = fs.lstatSync(file);
  if (!s.isFile()) return digest({ dev: s.dev, ino: s.ino, mtimeMs: s.mtimeMs, mode: s.mode });
  if (s.size > 8 * 1024 * 1024) throw Error('Préimage trop grande');
  return digest({ dev: s.dev, ino: s.ino, mode: s.mode, bytes: digest(fs.readFileSync(file)) });
}
export function filePolicy(event, ctx, workspaces, protectedRoots = []) {
  const workspace = workspaces[ctx.agentId]; if (!workspace) return deny('Workspace non reconnu');
  const root = fs.realpathSync(workspace), params = structuredClone(event.params ?? {}); const targets = [];
  if (event.toolName === 'apply_patch') {
    const key = typeof params.input === 'string' ? 'input' : 'patch'; const patch = params[key];
    if (typeof patch !== 'string' || !patch.startsWith('*** Begin Patch\n') || !patch.trimEnd().endsWith('*** End Patch')) return deny('Patch non qualifié');
    params[key] = patch.replace(/^\*\*\* (Add File|Update File|Delete File|Move to): (.+)$/gm, (_, action, value) => {
      const file = canonical(value, root); targets.push({ file, deletion: action === 'Delete File' || action === 'Move to', action });
      return `*** ${action}: ${file}`;
    });
  } else {
    const key = ['path', 'file_path', 'filePath'].find(k => typeof params[k] === 'string');
    if (!key) return deny('Chemin cible absent');
    const file = canonical(params[key], root); params[key] = file;
    targets.push({ file, deletion: false, action: event.toolName });
  }
  if (targets.some(t => fs.existsSync(t.file) && fs.lstatSync(t.file).isFile() && fs.lstatSync(t.file).nlink > 1)) return deny('Fichier avec liens physiques : cible ambiguë');
  if (!targets.length) return deny('Aucune cible vérifiable');
  const foreign = Object.entries(workspaces).filter(([id]) => id !== ctx.agentId).map(([,v]) => fs.realpathSync(v));
  if (targets.some(t => foreign.some(r => within(t.file,r)))) return deny('Écriture dans le workspace de l’autre agent interdite');
  if (targets.some(t => protectedRoots.some(r => within(t.file,r)))) return deny('Plan de contrôle protégé ; intervention opérateur requise');
  if (targets.every(t => !t.deletion && memoryPath(t.file,root))) return { params };
  return deny('Écriture/suppression native hors mémoire non qualifiée ; utiliser file_change ou system_action pour un accord lié à l’exécution');
}
