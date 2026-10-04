# Optimisation vLLM-Metal — tests avant/après

Date : 2026-10-04 · Méthode : une variable à la fois, mesure avant/après.

## Test 1 : `--max-num-batched-tokens` 2048 (défaut) → 8192

| Métrique | 2048 (défaut) | 8192 | Verdict |
|---|---|---|---|
| Test A tok/s médian | 19.2 | 17.6 | légère dégradation |
| Test A TTFT médian | 0.87s | 0.15s | mieux (mais variance) |
| Prefill 62K à froid | **69.2s** | 110.5s | **2x dégradation** |

**Décision : REJET de 8192.** Le défaut 2048 est optimal sur M4 Max pour ce modèle (le chunked prefill plus petit laisse plus de marge au décodage MoE). Retour au défaut.

## Test 2 : Prefix caching (activé par défaut, non modifié)

- Hit rate observé : 33–49% après quelques requêtes, 0% au premier passage.
- Effet mesuré : requête 99K répétée → TTFT 274s (froid) → 3.3s (chaud). **Conservé** (défaut).

## Configuration finale retenue

```sh
source ~/.venv-vllm-metal/bin/activate
vllm serve mlx-community/Qwen3.6-35B-A3B-4bit \
  --port 11400 \
  --max-model-len 131072 \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice
```

- max-num-batched-tokens : 2048 (défaut, optimal mesuré)
- prefix caching : on (défaut)
- paged attention : on (défaut)
- gpu-memory-utilization : 0.92 (défaut Metal)
- wired_limit : 37.4 GB (auto)
