#!/usr/bin/env bash
# Retest rapide vLLM-Metal — relève versions/mémoire puis lance A/B/C.
# N'installe rien, ne supprime aucun modèle, ne modifie ni Codex ni Ollama.
# Usage: bash scripts/codex-local/retest-vllm-metal.sh [--skip-bench]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BENCH_DIR="$REPO/docs/codex-local/evidence"
ENDPOINT="http://127.0.0.1:11400/v1"
MODEL="mlx-community/Qwen3.6-35B-A3B-4bit"
REPORT_DIR="${REPO}/artifacts/vllm-retest"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/retest-$(date +%Y%m%d-%H%M%S).txt"

{
  echo "== Retest vLLM-Metal $(date) =="
  echo "-- macOS --"; sw_vers
  echo "-- vLLM --"; (source ~/.venv-vllm-metal/bin/activate && vllm --version) 2>&1
  echo "-- vllm-metal --"; (source ~/.venv-vllm-metal/bin/activate && pip show vllm-metal 2>/dev/null | head -2) 2>&1
  echo "-- MLX --"; (source ~/.venv-vllm-metal/bin/activate && python -c "import mlx.core as mx; print(mx.__version__)") 2>&1
  echo "-- swap --"; sysctl vm.swapusage
  echo "-- memory_pressure --"; memory_pressure -Q | tail -1
  echo "-- health --"; curl -s --max-time 5 "$ENDPOINT/models" | head -c 300; echo
} | tee "$REPORT"

if [[ "${1:-}" == "--skip-bench" ]]; then
  echo "Benchmarks ignorés (--skip-bench). Rapport: $REPORT"
  exit 0
fi

if ! curl -s --max-time 5 "$ENDPOINT/health" >/dev/null 2>&1; then
  echo "vLLM non joignable sur $ENDPOINT — démarrer le serveur (voir docs/codex-local/08-vllm-metal-conclusion-and-retest.md §13) puis relancer." >&2
  exit 1
fi

source ~/.venv-vllm-metal/bin/activate
for t in A-generation B-reasoning C-repo-task; do
  echo "== Test $t ==" | tee -a "$REPORT"
  python3 "$BENCH_DIR/bench.py" --endpoint "$ENDPOINT" --model "$MODEL" \
    --prompt-file "$BENCH_DIR/bench-prompts/$t.md" --runs 3 2>&1 | tee -a "$REPORT"
done

echo "-- swap post-bench --" | tee -a "$REPORT"
sysctl vm.swapusage | tee -a "$REPORT"
echo "Rapport: $REPORT"
echo "Gate: test B >= 50 tok/s ? Sinon STOP (voir 08-vllm-metal-conclusion-and-retest.md §7)."
