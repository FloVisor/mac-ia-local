#!/usr/bin/env python3
"""Test A/B/A interleavé : neutralise la dérive thermique/mémoire.

Séquence : OFF, ON, OFF, ON ... sur le même prompt (nonce unique par cycle).
Si SpecPrefill est un no-op (aucun draft model chargé), les deux séries
doivent être statistiquement indiscernables.
"""
import argparse
import json
import statistics
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from run_bench import chat, mem  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--level", type=int, default=32768)
    ap.add_argument("--cycles", type=int, default=3)
    args = ap.parse_args()

    P = json.load(open(args.prompts))
    content = P["levels"][str(args.level)]["content"]
    rows = []
    for c in range(args.cycles):
        for mode in (False, True):
            # nonce distinct par requête -> chaque mesure est un cold prefill
            nonce = f"aba-{args.level}-{c}-{'on' if mode else 'off'}-{time.time_ns()}"
            r = chat(content, args.key, 32, mode, nonce)
            rows.append({"cycle": c, "specprefill": mode,
                         "ttft": r.get("ttft"), "prefill_s": r.get("prefill_s"),
                         "cached": r.get("cached_tokens"),
                         "prompt": r.get("prompt_tokens"),
                         "gen_tps": r.get("gen_tps")})
            print(f"cycle{c} sp={'ON ' if mode else 'OFF'} "
                  f"ttft={r.get('ttft')} cached={r.get('cached_tokens')} "
                  f"gen={r.get('gen_tps')}", flush=True)

    off = [r["ttft"] for r in rows if not r["specprefill"]]
    on = [r["ttft"] for r in rows if r["specprefill"]]
    summary = {
        "level": args.level,
        "off_ttft": off, "on_ttft": on,
        "off_mean": round(statistics.mean(off), 2),
        "on_mean": round(statistics.mean(on), 2),
        "off_stdev": round(statistics.stdev(off), 2) if len(off) > 1 else 0,
        "on_stdev": round(statistics.stdev(on), 2) if len(on) > 1 else 0,
        "delta_pct": round((statistics.mean(on) - statistics.mean(off))
                           / statistics.mean(off) * 100, 1),
        "mem": mem(),
    }
    print(json.dumps(summary, indent=1))
    json.dump({"rows": rows, "summary": summary}, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
