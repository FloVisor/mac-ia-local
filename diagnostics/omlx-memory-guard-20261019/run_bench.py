#!/usr/bin/env python3
"""Benchmark prefill oMLX : SpecPrefill ON vs OFF, cold vs warm, multi-tour.

Mesures réelles via l'API OpenAI d'oMLX (usage natif) :
  prompt_tokens, cached_tokens, time_to_first_token, prompt_eval_duration,
  generation_duration, generation_tokens_per_second.
Mémoire : /health (engine_pool) + RSS du process omlx-server + swap.

Isolation : chaque test froid utilise un nonce unique en tête de prompt, donc
aucun préfixe commun avec un test précédent (cache froid garanti).
"""
import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
MODEL = "mlx-community--Qwen3.6-35B-A3B-4bit"


def http(url, payload=None, key=None, timeout=1800):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return {"raw": e.read()[:400].decode(errors="replace")}, f"HTTP {e.code}"
    except Exception as e:
        return {}, f"error: {e}"


def mem():
    h, _ = http(BASE + "/health", timeout=10)
    ep = h.get("engine_pool", {}) if isinstance(h, dict) else {}
    rss = subprocess.run(["ps", "-o", "rss=", "-p", str(pid())],
                         capture_output=True, text=True).stdout.strip()
    swap = subprocess.run(["sysctl", "-n", "vm.swapusage"],
                          capture_output=True, text=True).stdout.strip()
    return {
        "model_memory_gb": round(ep.get("current_model_memory", 0) / 1e9, 2),
        "rss_gb": round(int(rss or 0) / 1e6, 2),
        "swap": swap,
    }


def pid():
    out = subprocess.run(["pgrep", "-x", "omlx-server"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else 0


def chat(prompt, key, max_tokens=32, specprefill=None, nonce=None):
    content = prompt if nonce is None else f"[run {nonce}]\n{prompt}"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "enable_thinking": False,
    }
    if specprefill is not None:
        payload["specprefill"] = specprefill
    t0 = time.time()
    d, err = http(BASE + "/v1/chat/completions", payload, key)
    wall = time.time() - t0
    if err:
        return {"error": err, "raw": d, "wall": round(wall, 2)}
    u = d["usage"]
    return {
        "prompt_tokens": u["prompt_tokens"],
        "cached_tokens": u["prompt_tokens_details"]["cached_tokens"],
        "ttft": u["time_to_first_token"],
        "prefill_s": u["prompt_eval_duration"],
        "gen_s": u["generation_duration"],
        "gen_tps": u["generation_tokens_per_second"],
        "completion_tokens": u["completion_tokens"],
        "wall": round(wall, 2),
        "text": d["choices"][0]["message"]["content"],
        "finish": d["choices"][0]["finish_reason"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--specprefill", default="none", choices=["none", "on", "off"])
    ap.add_argument("--levels", default="8192,32768,65536")
    ap.add_argument("--max-tokens", type=int, default=32)
    args = ap.parse_args()

    sp = {"none": None, "on": True, "off": False}[args.specprefill]
    P = json.load(open(args.prompts))
    res = {"label": args.label, "specprefill": args.specprefill,
           "model": MODEL, "levels": {}, "multiturn": {}, "mem": {}}

    res["mem"]["before"] = mem()

    for lvl in [int(x) for x in args.levels.split(",")]:
        content = P["levels"][str(lvl)]["content"]
        markers = P["levels"][str(lvl)]["markers"]
        nonce = f"{args.label}-{lvl}-{int(time.time())}"
        entry = {"declared_tokens": P["levels"][str(lvl)]["tokens"]}

        # 1. cold : nonce unique -> aucun préfixe commun
        entry["cold"] = chat(content, args.key, args.max_tokens, sp, nonce)
        entry["mem_after_cold"] = mem()

        # 2. warm : même prompt exactement (nonce identique)
        entry["warm"] = chat(content, args.key, args.max_tokens, sp, nonce)

        # 3. rétention : marqueurs debut/milieu/fin
        q = ("Cite exactement, sans paraphrase, les trois identifiants "
             "MARQUEUR présents dans le texte ci-dessus, dans l'ordre "
             "DEBUT, MILIEU, FIN.")
        entry["retention"] = chat(content + "\n\n" + q, args.key, 96, sp, nonce)
        entry["markers"] = markers
        res["levels"][str(lvl)] = entry
        print(f"[{args.label}] {lvl}: cold ttft={entry['cold'].get('ttft')} "
              f"cached={entry['cold'].get('cached_tokens')} | "
              f"warm ttft={entry['warm'].get('ttft')} "
              f"cached={entry['warm'].get('cached_tokens')}", flush=True)

    # 4. multi-tour : préfixe 32K + 4 tours append
    mt = P["multiturn"]
    nonce = f"{args.label}-mt-{int(time.time())}"
    conv = mt["base"]
    turns = []
    for i, t in enumerate(mt["turns"]):
        conv = conv + "\n" + t
        r = chat(conv, args.key, args.max_tokens, sp, nonce)
        turns.append(r)
        print(f"[{args.label}] turn{i+1}: prompt={r.get('prompt_tokens')} "
              f"cached={r.get('cached_tokens')} ttft={r.get('ttft')}", flush=True)
    res["multiturn"] = {"turns": turns, "markers": mt["markers"],
                        "base_tokens": mt["base_tokens"],
                        "turn_tokens": mt["turn_tokens"]}

    res["mem"]["after"] = mem()
    with open(args.out, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("written", args.out)


if __name__ == "__main__":
    main()
