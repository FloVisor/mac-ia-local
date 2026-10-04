#!/usr/bin/env python3
"""Test de contexte à niveaux croissants (16K/32K/64K/96K/128K) — mesure TTFT, tps, mémoire.

Génère un prompt synthétique (résumé de fichiers fictifs, sans donnée privée) approchant
la taille cible, pose une question de rappel simple à la fin, mesure la réponse.
"""
import argparse, json, time, urllib.request, subprocess, sys

def sysmem():
    swap = subprocess.run(["sysctl","-n","vm.swapusage"], capture_output=True, text=True).stdout.strip()
    free = subprocess.run(["memory_pressure","-Q"], capture_output=True, text=True).stdout.strip().splitlines()[-1]
    return swap, free

def make_prompt(target_tokens):
    # ~1 token ≈ 3.5 chars en anglais; bloc de 100 tokens répété
    block = ("File module_%d.py: def process(data): validate schema, transform records, "
             "aggregate metrics, return summary dict with counts and errors list. ")
    parts, i, approx = [], 0, 0
    per_block_tokens = 28
    while approx < target_tokens:
        parts.append(block % i)
        i += 1
        approx += per_block_tokens
    parts.append("\n\nQuestion: cite exactement le nom de la fonction définie dans le premier fichier, puis le nombre total de fichiers décrits. Réponds en une phrase.")
    return "".join(parts)

def run(endpoint, model, prompt, max_tokens, timeout):
    url = endpoint.rstrip("/") + "/chat/completions"
    payload = {"model": model, "messages": [{"role":"user","content":prompt}],
               "max_tokens": max_tokens, "temperature": 0.6, "stream": True}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type":"application/json"})
    t0 = time.time(); ttft = None; chunks = []; usage = None
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for line in resp:
            line = line.decode().strip()
            if not line.startswith("data: "): continue
            data = line[6:]
            if data == "[DONE]": break
            try: obj = json.loads(data)
            except json.JSONDecodeError: continue
            if obj.get("usage"): usage = obj["usage"]
            d = obj.get("choices",[{}])[0].get("delta",{})
            c = d.get("content") or d.get("reasoning")
            if c:
                if ttft is None: ttft = time.time()-t0
                chunks.append(c)
    total = time.time()-t0
    toks = usage.get("completion_tokens") if usage else max(1,len("".join(chunks).split()))
    ptoks = usage.get("prompt_tokens") if usage else 0
    return ttft, total, toks, ptoks, "".join(chunks)[:200]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--levels", default="16000,32000,64000,96000,128000")
    ap.add_argument("--max-tokens", type=int, default=120)
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    for lvl in [int(x) for x in args.levels.split(",")]:
        prompt = make_prompt(lvl)
        print(f"\n=== LEVEL {lvl} (prompt ~{len(prompt)} chars) ===", flush=True)
        print("mem before:", sysmem()[0], "|", sysmem()[1], flush=True)
        try:
            ttft, total, toks, ptoks, sample = run(args.endpoint, args.model, prompt, args.max_tokens, args.timeout)
            print(f"ttft={ttft:.2f}s total={total:.2f}s out_tokens={toks} prompt_tokens={ptoks} tps={toks/total:.1f}", flush=True)
            print("answer sample:", sample.replace(chr(10)," ")[:150], flush=True)
        except Exception as e:
            print(f"FAIL: {e}", flush=True)
        print("mem after:", sysmem()[0], "|", sysmem()[1], flush=True)

if __name__ == "__main__":
    main()
