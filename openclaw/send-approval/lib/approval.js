import { createHash } from 'node:crypto';
export const digest = value => createHash('sha256').update(typeof value === 'string' || Buffer.isBuffer(value) ? value : JSON.stringify(value)).digest('hex');
export const deny = reason => ({ block: true, blockReason: `send-approval: ${reason}` });
export function request(params, agentId, action, details, onResolution) {
  if (!['main', 'perso'].includes(agentId)) return deny('Identité agent inconnue');
  const description = `${agentId} | ${details} | SHA256=${digest(params)}`;
  if (description.length > 512 || /[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]/u.test(description)) return deny('Description ambiguë ou trop longue ; préciser une action plus petite');
  return { params: structuredClone(params), requireApproval: { title: `${agentId === 'main' ? 'Pro' : 'Perso'} : ${action}`, description, severity: 'warning', allowedDecisions: ['allow-once', 'deny'], timeoutMs: 120000, ...(onResolution ? { onResolution } : {}) } };
}
