// A deliberately small shell language. Never interpret or resolve substitutions.
export function words(command) {
  if (typeof command !== 'string' || /[\r\n\0`$\\]/u.test(command)) throw Error('Commande non figée');
  let quote = '', word = '', active = false; const result = [];
  for (const c of command) {
    if (quote) { if (c === quote) quote = ''; else word += c; active = true; }
    else if (c === '"' || c === "'") { quote = c; active = true; }
    else if (/\s/u.test(c)) { if (active) { result.push(word); word = ''; active = false; } }
    else if (';|&<>(){}#'.includes(c)) throw Error('Commande composée non prise en charge');
    else { word += c; active = true; }
  }
  if (quote) throw Error('Guillemet non fermé');
  if (active) result.push(word);
  return result;
}
