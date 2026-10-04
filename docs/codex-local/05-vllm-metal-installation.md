# Installation vLLM-Metal

Date : 2026-10-03 · Machine : MacBook Pro M4 Max 48 GB, macOS 27.0

## 1. Méthode d'installation (officielle, vérifiée)

Script officiel du projet (méthode recommandée "Latest development build") :

```sh
curl -fsSL https://raw.githubusercontent.com/vllm-project/vllm-metal/main/install.sh | bash
```

- Venv isolé : `~/.venv-vllm-metal` (Python 3.12.14 natif arm64 — requirement officiel)
- Aucune modification du Python système (Homebrew 3.14 intact), aucun impact sur Ollama.
- Désinstallation complète : `rm -rf ~/.venv-vllm-metal` (+ éventuellement le cache HF du modèle).

## 2. Versions installées (observées)

| Composant | Version |
|---|---|
| vllm (core) | 0.30.0+cpu (plugin metal activé) |
| vllm-metal | 0.30.0.dev20261003204550 |
| mlx / mlx-metal | 0.32.1 |
| mlx-lm | 0.32.0 (git 9e6acca) |
| mlx-vlm | 0.6.17 |
| Python (venv) | 3.12.14 |
| Backend | MLX device gpu(0), PyTorch mps, wired_limit 37.4 GB |

## 3. Checkpoint téléchargé

`mlx-community/Qwen3.6-35B-A3B-4bit` (SHA repo 38740b84) → cache HF `~/.cache/huggingface/hub/` — 4 shards safetensors complets (5.29+5.37+5.37+4.38 GB ≈ 20.4 GB), checksums LFS vérifiés par hf download.

## 4. Lancement testé (32K initial)

```sh
source ~/.venv-vllm-metal/bin/activate
vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 \
  --max-model-len 32768 \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice
```

Parsers vérifiés dans la version installée (pas devinés) :
- `--tool-call-parser qwen3_coder` → `Qwen3EngineToolParser` (format XML `<tool_call><function=…><parameter=…>…_des_modules_vllm/tool_parsers/__init__.py_`)
- `--reasoning-parser qwen3` → `Qwen3ParserReasoningAdapter` (think tags `…`)

## 5. Endpoints testés (indépendamment de Codex)

| Endpoint | Test | Résultat |
|---|---|---|
| `/health` | GET | **PASS** HTTP 200 |
| `/v1/models` | GET | **PASS** — id `mlx-community/Qwen3.6-35B-A3B-4bit`, max_model_len 32768 |
| `/v1/responses` | POST | **PASS** — status completed, texte exact, usage détaillé (input 21, output 200 dont 191 reasoning tokens) |
| `/v1/chat/completions` (tool calling) | POST + tools | **PASS** — finish_reason=tool_calls, `get_weather(city="Paris")`, 139 completion tokens dont 111 reasoning |
| `/v1/chat/completions` (streaming) | POST stream | **PASS** — deltas `reasoning` puis `content` |

## 6. Mémoire (modèle chargé, 32K)

- EngineCore RSS : 11.2 GB (vs llama-server Ollama 24.4 GB — le MoE 4-bit MLX ne charge que les poids actifs + KV cache paged)
- wired_limit Metal : 37.4 GB
- Swap : 3.0 GB used, mem free 81% (Ollama déchargé de la RAM entre-temps par keep_alive expiré)

## 7. Notes

- Warning ffmpeg/cv2 (classes AVF dupliquées) : cosmétique, sans impact serveur.
- `device_config=cpu` affiché mais MLX device = gpu(0) : normal pour le plugin metal (PyTorch mps + MLX gpu).
- Prefix caching activé par défaut (enable_prefix_caching=True), chunked prefill activé (max_num_batched_tokens=2048).
