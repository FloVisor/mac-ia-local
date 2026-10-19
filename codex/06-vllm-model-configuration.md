# Configuration du modèle Qwen3.6-35B-A3B MLX 4-bit sur vLLM-Metal

Date : 2026-10-03 · Progression contextuelle testée : 32K → 64K → 96K → 128K

## 1. Paramètres serveur retenus (128K validé)

```sh
source ~/.venv-vllm-metal/bin/activate
vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 \
  --max-model-len 131072 \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice
```

- **Parsers** (vérifiés dans la version installée, pas devinés) :
  - tool-call : `qwen3_coder` (Qwen3EngineToolParser — format XML `<tool_call><function=…>…_des_vllm/tool_parsers/__init__.py_)
  - reasoning : `qwen3` (Qwen3ParserReasoningAdapter — think tags)
- **Prefix caching** : activé par défaut (enable_prefix_caching=True)
- **Paged attention** : activée par défaut (chunked prefill, max_num_batched_tokens=2048)
- **KV cache** : CPU KV cache 752 413 tokens, concurrence 5.74x à 128K
- **Mémoire Metal** : wired_limit 37.4 GB (auto)

## 2. Progression contextuelle (mesurée)

| Niveau | TTFT | Total | Notes |
|---|---|---|---|
| 32K (max-model-len 32768) | 25.1s | 28.3s | prompt ~32k tokens |
| ~62K (max-model-len 65536) | 72.1s | 75.3s | prompt 62k tokens (limite 65536 atteinte à 63k+100) |
| ~96K (max-model-len 131072) | 274.1s | 277.6s | prompt ~99k tokens |
| ~125K (max-model-len 131072) | 120.9s | 124.6s | prompt ~125k tokens — **128K opérationnel** |

Observations :
- Le serveur tient 128K sans crash ni swap massif (swap stable ~2.9 GB, mem free 9% pendant le test, 83% après).
- TTFT long-contexte variable (96K plus lent que 125K — effet cache/compilation chunked prefill, non déterministe).
- Erreurs 400 claires et propres quand prompt+output dépasse max-model-len (comportement correct).

## 3. Mémoire (128K, modèle chargé)

| Métrique | Valeur |
|---|---|
| EngineCore RSS | 9.8–11.1 GB |
| Swap used | ~2.9 GB (stable, pas de croissance) |
| Mem free pendant test | 9% (81–83% au repos) |
| wired_limit Metal | 37.4 GB |

vs Ollama : llama-server RSS 24.4 GB pour le même modèle en Q4_K_M GGUF. **vLLM-Metal utilise ~2.2x moins de RAM résidente** (MoE 4-bit MLX + KV cache paged CPU).

## 4. Décision contexte

- 128K validé comme maximum opérationnel (conforme objectif "max context = 128K au maximum").
- 256K non testé (hors périmètre demandé : "Ne cherche pas à utiliser 256K uniquement parce que le modèle le permet").
