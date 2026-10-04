#!/usr/bin/env python3
"""Benchmark reproductible Ollama vs vLLM — même corpus, mêmes paramètres.

Usage: python3 bench.py --endpoint http://127.0.0.1:11434/v1 --model qwen3.6:35b-coding --runs 3
Mesure: TTFT, temps total, tokens/s (via usage si dispo, sinon approximation mots).
"""
import argparse, json, time, urllib.request, statistics, sys

def bench_once(endpoint, model, prompt, max_tokens, timeout):
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": True,
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    ttft = None
    chunks = []
    usage = None
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            if "usage" in obj and obj["usage"]:
                usage = obj["usage"]
            delta = obj.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content") or delta.get("reasoning")
            if content:
                if ttft is None:
                    ttft = time.time() - t0
                chunks.append(content)
    total = time.time() - t0
    text = "".join(chunks)
    if usage and usage.get("completion_tokens"):
        out_tokens = usage["completion_tokens"]
    else:
        out_tokens = max(1, len(text.split()))
    return {"ttft": ttft, "total": total, "tokens": out_tokens,
            "tps": out_tokens / total if total > 0 else 0, "chars": len(text)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()
    prompt = open(args.prompt_file).read()
    results = []
    for i in range(args.runs):
        r = bench_once(args.endpoint, args.model, prompt, args.max_tokens, args.timeout)
        results.append(r)
        ttft_s = f"{r['ttft']:.2f}s" if r["ttft"] is not None else "n/a"
        print(f"run {i+1}: ttft={ttft_s} total={r['total']:.2f}s tokens={r['tokens']} tps={r['tps']:.1f}", flush=True)
    ttfts = [r["ttft"] for r in results if r["ttft"] is not None]
    if not ttfts:
        print("ERROR: no TTFT captured (no content deltas?)", file=sys.stderr)
        sys.exit(1)
    totals = [r["total"] for r in results]
    tps = [r["tps"] for r in results]
    print(json.dumps({
        "model": args.model, "prompt": args.prompt_file, "runs": args.runs,
        "ttft": {"median": statistics.median(ttfts), "min": min(ttfts), "max": max(ttfts)},
        "total": {"median": statistics.median(totals), "min": min(totals), "max": max(totals)},
        "tps": {"median": statistics.median(tps), "min": min(tps), "max": max(tps)},
    }, indent=2))

if __name__ == "__main__":
    main()
