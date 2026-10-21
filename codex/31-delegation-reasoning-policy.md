# Raisonnement des délégations MCP — 21 octobre 2026

## Changements appliqués

Politique globale installée dans `~/.codex/AGENTS.md`, copie de maintenance ajustée dans `codex/global-instructions.md`. Deux règles ajoutées : effort explicite proportionné par sous-tâche et sortie structurée concise complète, sans raisonnement interne. Remplacement de la préférence nominative Qwen par un modèle local adapté. Toutes les autres lignes de chaque fichier sont conservées exactement ; les différences antérieures entre les deux fichiers sont préservées.

Emplacement global confirmé par la documentation officielle : https://learn.chatgpt.com/docs/agent-configuration/agents-md . Les nouvelles sessions chargent la politique ; aucun redémarrage forcé, et la session courante a également reçu les instructions actualisées.

## Contrat vérifié dans les sources et outils chargés

`submit` et `delegate` exposent `reasoning` optionnel : off/minimal 0, low 512, medium 2048 (défaut), high 8192, max 16384, ultra 8192 (alias historique High). Le schéma expose les valeurs, mais ne décrivait pas leurs usages ; les instructions globales comblent cette lacune sans changer le schéma ni les clients.

Le routeur ne classe pas l’effort. Pour la route locale Qwen : `chat_template_kwargs.enable_thinking` et `thinking_budget` ; aucun `reasoning_effort` envoyé. Les autres routes ne reçoivent pas ces budgets numériques (`unsupported_not_sent`) : aucune équivalence Cloud revendiquée. La complexité utilisée pour sélectionner une route est distincte de reasoning.

`max_tokens = réserve finale + budget réflexion + 1` si réflexion active. Réserve automatique review/analysis 3072, coding 4096, testing 2048 ; texte >=12000 octets : réserve >=6144 ; plafond automatique 8192. High/Max préservent cette réserve. Un plafond explicite reste un plafond de réponse. L’admission réserve toute la génération dans les 131072 tokens de contexte. La récupération automatique après troncature double seulement la réserve finale, au plus une fois ; elle ne requalifie pas l’effort.

Aucune modification de router.py, LiteLLM, oMLX, paramètres mémoire/contexte, modèle OpenClaw, séparation Pro/Perso, RTK ou Graphify. Aucun commit/push ni redémarrage.

## Contrôles

`python3 -m unittest discover -s mcp/llm-router -q` : **117 tests PASS**, 6,006 s. ResourceWarning sur connexions SQLite non fermées dans la suite, sans échec ; non traité hors périmètre.

Deux tests ajoutés à `test_output_budget.py` : valeurs littérales de tous les budgets et défaut Medium pour codex/openclaw-pro/openclaw-perso via moteur et backend simulé ; Low/High/Max inchangés après récupération de taille. Les tests existants couvrent contexte, isolation, non-transmission des budgets Cloud et troncatures.

`python3 -m pytest witness-a/ -q` : **NOT_RUN**, sortie 1, `No module named pytest`. Aucun paquet installé. Aucun paramètre moteur modifié.

## Comparaison réelle bornée

Deux soumissions locales gratuites, même prompt de revue de politique, seule différence reasoning Low/Medium ; qualité JSON obligatoire. Aucun secret transmis, Cloud désactivé, aucun modèle imposé. 
| Mesure | Low | Medium |
|---|---:|---:|
| task_id | dba9409d-bdc9-4424-a854-072cdbfcebe2 | 80e76543-1b6b-477f-85ca-c889f8838699 |
| Durée routeur | 22,887 s | 74,570 s |
| Tokens produits | 546 | 2353 |
| Tokens de raisonnement comptabilisés | 513 | 2047 |
| Budget envoyé | 512 | 2048 |
| max_tokens envoyé | 3585 | 5121 |
| Réserve finale | 3072 | 3072 |
| Contrôle JSON | PASS | PASS |
| Contrôle métier Codex | PASS | REJET |

Les deux réponses finissent avec stop, une seule tentative chacune ; LiteLLM déclare zéro retry et zéro fallback. Le modèle retourné est l’alias local, fournisseur non confirmé indépendamment. Les résultats MCP ne contiennent aucun raisonnement interne.

Low conclut coherent, sans risque, ce qui correspond au contrat examiné. Medium invente trois contradictions : (1) Codex qualifie l’effort lui-même, donc ne pas déléguer cette qualification est cohérent ; (2) 16384 est un budget de réflexion, pas le plafond total, auquel s’ajoute correctement la réserve finale ; (3) qualifier les sous-tâches ne requiert aucun fractionnement artificiel. Ces recommandations sont rejetées, aucune modification n’en découle. Le contrôle JSON seul n’aurait pas suffi.

Sur ce seul couple, Low réduit la durée de 69,3 % et les tokens produits de 76,8 %, avec une réponse correcte et complète. Cela ne prouve aucune supériorité générale de Low. Deux inférences réelles locales au total, aucune route payante ni Cloud ; pas de troisième test.


## Limites

Compatibilité des identités Pro/Perso testée hors ligne ; aucune inférence dans leurs sessions réelles. High/Max vérifiés sur payloads et réserves, pas par génération réelle. Les métadonnées reasoning.confirmed restent null : budgets envoyés et usage observé ne constituent pas une attestation fournisseur indépendante. Les réponses MCP exposent seulement le contenu final, pas reasoning_content. Une comparaison unique ne qualifie pas un gain général ni toutes les tâches.

## Rollback

Sauvegardes avant modification dans `artifacts/reasoning-policy-20261021/` :

```sh
cp artifacts/reasoning-policy-20261021/0-AGENTS.md ~/.codex/AGENTS.md
cp artifacts/reasoning-policy-20261021/1-global-instructions.md codex/global-instructions.md
cp artifacts/reasoning-policy-20261021/2-test_output_budget.py mcp/llm-router/test_output_budget.py
```

Avant restauration, vérifier l’absence de changements ultérieurs dans ces fichiers ; sinon retirer seulement les deux règles ajoutées et rétablir la phrase Qwen. Aucun service à redémarrer. Ce rapport peut être supprimé si inutile ; ne pas supprimer les sauvegardes avant décision de conservation.
