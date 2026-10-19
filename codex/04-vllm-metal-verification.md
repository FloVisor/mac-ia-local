# Vérification vLLM-Metal + checkpoint Qwen3.6-35B-A3B MLX 4-bit

Date : 2026-10-03 · Sources : docs.vllm.ai (latest), github.com/vllm-project/vllm-metal, huggingface.co API — vérifiées en direct.

## 1. vLLM-Metal (vérifié)

- **Projet** : `vllm-project/vllm-metal` — plugin officiel vLLM pour Apple Silicon, backend MLX.
- **Statut** : actif, v0.2.0+ (2026/04 : paged varlen kernel par défaut, "83x TTFT, 3.6x throughput vs v0.1.0" ; 2026/08 : M5 NAX tensor units, Qwen3.8 support).
- **Requirements** : macOS 15+ (Mac actuel : macOS 27 ✅), Apple Silicon (M4 Max ✅), **Python 3.12 natif arm64** (⚠️ le Python Homebrew système est 3.14 — l'install script gère son propre venv).
- **Installation officielle** (2 méthodes) :
  - Stable : `brew tap vllm-project/vllm-metal https://github.com/vllm-project/vllm-metal && brew install vllm-project/vllm-metal/vllm-metal`
  - Dev (défaut) : `curl -fsSL https://raw.githubusercontent.com/vllm-project/vllm-metal/main/install.sh | bash` → venv `~/.venv-vllm-metal`
  - `pip install vllm-metal` **non supporté** (vérifié : le package n'existe pas sur PyPI).
- **Désinstallation** : `rm -rf ~/.venv-vllm-metal` (méthode curl) — propre et réversible. ✅ conforme à l'exigence "facilement supprimable".
- **Architecture** : vLLM fournit API server/scheduler/paged blocks ; mlx_lm les couches modèle ; vllm-metal le chemin attention (paged varlen kernel, prefill).

## 2. Support Qwen3.6 (vérifié)

Matrice `docs/supported_models.md` (vllm-metal) :

> | Qwen3.5 / 3.6 / 3.8 | ✅ | Hybrid SDPA + GDN linear (3.6 adds MoE) | 🔵 prefix cache | `mlx-community/Qwen3.8-27B-8bit` |

- Qwen3.6 = hybride SDPA + GDN + MoE → **supporté ✅**, prefix caching 🔵 (expérimental).
- Le checkpoint d'exemple est Qwen3.8-27B (même famille hybride) ; "Other sizes and quantizations of the same family generally work too".

## 3. Checkpoint EXACT : `mlx-community/Qwen3.6-35B-A3B-4bit` (vérifié)

Comparaison des candidats MLX 4-bit de Qwen3.6-35B-A3B :

| Repo | Mainteneur | Base | Downloads | Likes | Créé | Taille | Verdict |
|---|---|---|---|---|---|---|---|
| **mlx-community/Qwen3.6-35B-A3B-4bit** | mlx-community (officiel MLX) | Qwen/Qwen3.6-35B-A3B | 28 999 | 111 | 2026-04-16 | ~20.4 GB (4 shards safetensors) | **RETENU** |
| lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit | lmstudio-community | Qwen/Qwen3.6-35B-A3B | 266 190 | 16 | 2026-04-16 | ~20 GB | OK mais format lmstudio, moins canonique pour vllm-metal |
| mlx-community/Qwen3.6-35B-A3B-DFlash2-4bit | mlx-community | incoai/Qwen3.6-35B-A3B-Splash (finetune MTP) | 1 840 | 8 | 2026-09-23 | — | Rejeté : base = finetune DFlash2, pas le modèle de base |

Détails vérifiés du checkpoint retenu :
- `model_type: qwen3_5_moe`, architecture `Qwen3_5MoeForConditionalGeneration`, quantization bits=4
- 4 shards safetensors : 5.29 + 5.37 + 5.37 + 4.38 GB ≈ **20.4 GB**
- Tokenizer Qwen (eos `<|im_end|>`), chat template jinja complet (vision + thinking)
- License Apache-2.0, base_model: Qwen/Qwen3.6-35B-A3B (offiel Qwen)
- SHA repo : 38740b847e4cb78f352aba30aa41c76e08e6eb46

**Correspondance avec le modèle Ollama actuel** : qwen3.6:35b-coding (ollama) = qwen35moe 35.5B Q4_K_M 22 GB — même architecture qwen3_5_moe, même famille Qwen3.6-35B-A3B. Le checkpoint MLX 4-bit est l'équivalent direct.

## 4. Parsers (vérifiés dans la doc vLLM, à confirmer sur la version installée)

- **Reasoning parser** : `qwen3` (série Qwen3, thinking activé par défaut, `enable_thinking=False` pour désactiver via chat_template_kwargs).
- **Tool call parser** : Qwen3.6 n'est pas listé explicitement ; candidats selon la doc : `hermes` (Qwen2.5/QwQ), `qwen3_xml` (Qwen3-Coder). **À déterminer empiriquement sur la version installée** (Phase 6/7) — le chat template du checkpoint (format tool calls Qwen3.6) dictera le parser.

## 5. Responses API (vérifié)

- vLLM expose une API OpenAI-compatible incluant `/v1/responses` (doc vLLM : "OpenAI-compatible API server, plus Anthropic Messages API and gRPC support" ; Responses API supportée par vLLM core).
- Codex `wire_api = "responses"` → compatible en principe. **À valider empiriquement** (Phase 6).

## 6. Décision

✅ Toutes les conditions de la Phase 5 sont réunies : vLLM-Metal officiel, support Qwen3.6 confirmé, checkpoint MLX 4-bit officiel mlx-community identifié avec certitude. On passe à l'installation (Phase 6).
