# Incident du 2026-10-20 — « Envoi recp deux prêts Anais SMS »

Session : `agent:perso:dashboard:4455548a-2384-4e9d-8206-fadb5c3e761a`
(groupe « Appartement VARS »).

## Symptôme 1 — SMS « non distribué »

**Le SMS n'a PAS été distribué.** Message `id 24738`, chat 58,
`2026-10-20T14:43:01Z`, `is_from_me: true` — mais marqué **« non distribué »**
en rouge dans Messages (constaté par Florian).

L'agent a exécuté :

```sh
imsg send --to "+33624310266" --text "Salut Anaïs, …" --service sms
```

`imsg` a retourné **exit 1** avec :

```
applescript send failed (may_have_completed): Messages automation returned
success, but no matching outgoing text row was observed within 8 seconds.
```

**Cause réelle** : `--service sms` forcé vers un contact iMessage. Le Mac n'a
pas de relais SMS utilisable pour ce destinataire, donc `imagent` échoue au
contrôle de routage :

```
imagent: (IMDaemonCore) [com.apple.Messages:Chat] Routable message unable to
perform downgrade/routing check. Is the account and service set correctly?
```

(16:43:01.358, GUID `2BE4563A-CC26-42B6-9CA8-26C8C0B529F6` — seule occurrence
de la journée, exactement sur ce message.)

Le GUID a été retenté à 16:53 sans jamais recevoir de
`SMSReceivedRelaySentReceipt`, contrairement aux envois réussis de 16:40:11 et
16:40:12.

**Diagnostic erroné corrigé** : la première analyse concluait « le SMS est bien
parti » sur la base de `is_from_me: true`. C'est faux — `imsg history` n'expose
ni `isDelivered` ni `isSent`, et la ligne est écrite dès la tentative. Seul
**exit 0** prouve un envoi accepté.

**Correctifs appliqués** :
- `AGENTS.md` (Perso) et les deux skills `imessage` : ne plus forcer
  `--service sms`, laisser `auto` ; `is_from_me` ne prouve rien ; exit 1 = état
  inconnu ; « non distribué » = échec.
- Ne jamais réessayer sans accord de Florian (risque de doublon).

## Symptôme 2 — BookStack non consulté

Dans la session d'origine, l'agent a répondu « je n'ai pas accès à BookStack
(jeton manquant) » puis a demandé les chiffres à Florian.

**Cause** : à 06:49 UTC, le jeton BookStack n'était pas encore résolu dans cette
session (le plugin a été configuré plus tard dans la journée). Le message
d'erreur était donc exact à ce moment-là.

En revanche, la règle manquait : une demande métier documentée doit déclencher
une consultation BookStack **avant** de répondre, même sans le mot « BookStack ».

**Correctif appliqué** : règle dans `AGENTS.md` (Perso) — consulter l'activité
avant de répondre, ne jamais dire « pas d'accès » sans avoir cherché, citer la
requête utilisée en cas d'absence de résultat.

**Vérification** : en session neuve, « résumé des deux prêts » produit
maintenant un résumé complet issu des pages 41 (offre de prêt) et des
commentaires associés.

## Symptôme 3 — appels `tool_call` sur des ids de skill

Deux appels ont échoué :

```
tool_call {"id":"famille-contacts"} → This id names a skill, not a callable tool
tool_call {"id":"imsg"}             → This id names a skill, not a callable tool
```

**Correctif appliqué** : règle dans `AGENTS.md` (Perso) — charger le skill avec
`read` sur son `SKILL.md`, puis appeler les vrais outils (`exec`, `message`,
`bookstack_*`).

## Symptôme 4 — syntaxe `imsg` inventée

Le modèle a produit `imsg send --to X --message "…"` puis `--phone`. Ces options
n'existent pas en 0.17.0.

**Correctif appliqué** : bloc de syntaxe exacte ancré dans `AGENTS.md` (Perso),
toujours injecté, en plus des skills.

## Points restés ouverts

- `imsg history` par nom seul (`imsg …`) est refusé par l'allowlist exec du
  nœud ; le chemin absolu `/opt/homebrew/bin/imsg` fonctionne. Documenté.
- Le faux négatif `may_have_completed` vient d'`imsg` 0.17.0, pas d'OpenClaw :
  aucune correction possible côté agent au-delà de la vérification.
