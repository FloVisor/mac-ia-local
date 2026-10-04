# Rollback — retour à Codex → Ollama → qwen3.6:35b-coding

Date : 2026-10-04 · **Testé et opérationnel** (ROLLBACK_OLLAMA_OK en 39.8s, modèle rechargé automatiquement)

## Procédure (aucune réinstallation nécessaire)

Le rollback est **immédiat** car rien n'a été supprimé ni modifié côté Ollama :

```sh
# 1. (Optionnel) Arrêter vLLM pour libérer la mémoire wired GPU
ps aux | grep -E "vllm|EngineCore" | grep -v grep   # repérer les PID
kill <PID_vllm> <PID_EngineCore>

# 2. Utiliser Ollama (le modèle se recharge automatiquement à la première requête)
cd /Users/fngux2/mac-ia-local
codex exec -c model_provider=ollama_codex -c model=qwen3.6:35b-coding "test"

# 3. Vérifier
ollama ps   # doit montrer qwen3.6:35b-coding 22GB 100% GPU
```

## État conservé pour le rollback

| Élément | État |
|---|---|
| Ollama 0.35.1 | installé, actif sur 127.0.0.1:11434 |
| Modèle qwen3.6:35b-coding | présent (22 GB, jamais supprimé) |
| Provider `ollama_codex` dans config.toml | intact |
| Catalogue/routing/overrides Ollama | intacts (sauvegardes .bak-mission-20261003-225030 en plus) |
| MCP, permissions, profils, Cloud | intacts |
| LaunchAgent org.gangneux.ollama-serve | intact |

## Si une restauration complète de config.toml était nécessaire

```sh
cp ~/.codex/config.toml.bak-mission-20261003-225030 ~/.codex/config.toml
```
(SHA256 d'origine : 653b280f7c177aaf1ab4564d48746fa1925517bcc8e9453812f6d8bb492d43b7 — voir 01-baseline-codex.md)

## Désinstallation complète de vLLM-Metal (si souhaité un jour)

```sh
rm -rf ~/.venv-vllm-metal
rm -rf ~/.cache/huggingface/hub/models--mlx-community--Qwen3.6-35B-A3B-4bit
# et retirer le bloc [model_providers.vllm_metal] de ~/.codex/config.toml
```
