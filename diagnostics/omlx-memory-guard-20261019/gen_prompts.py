#!/usr/bin/env python3
"""Génère des prompts synthétiques à longueur exacte (tokens réels) pour le
benchmark SpecPrefill ON/OFF sur oMLX.

Contenu : texte technique réaliste, non répétitif, RNG seedé par niveau.
Marqueurs uniques DEBUT / MILIEU / FIN pour contrôler la rétention.
Aucune donnée personnelle ou professionnelle.
"""
import argparse
import json
import os
import random
import uuid

SERVICES = ["auth-svc", "api-gateway", "ledger", "queue-mgr", "indexer",
            "cache-daemon", "scheduler", "webhook-dispatch", "metrics-aggr",
            "session-store", "search-idx", "billing-core", "notify-relay",
            "feature-flags", "rate-limiter", "doc-store"]
LEVELS = ["INFO", "WARN", "ERROR", "DEBUG", "AUDIT"]
MSGS = [
    "request completed status={st} bytes={n}",
    "retry attempt={k} backoff={ms}ms cause=upstream_timeout",
    "cache miss key=ctx:{hex} eviction=policy-{p}",
    "connection pool saturated active={a}/{cap}",
    "schema drift detected table={t} version={v}",
    "partition rebalanced shard={k} moved={n} rows",
    "token refresh ok sub=user-{n} ttl={ms}s",
    "backpressure signal queue_depth={q} consumers={a}",
    "compaction finished segment={hex} reclaimed={n}MB",
    "handshake negotiated proto={p} cipher={c}",
]


class Gen:
    def __init__(self, seed):
        self.r = random.Random(seed)

    def line(self):
        svc = self.r.choice(SERVICES)
        lvl = self.r.choice(LEVELS)
        msg = self.r.choice(MSGS).format(
            st=self.r.choice([200, 201, 204, 400, 404, 429, 500, 503]),
            n=self.r.randint(1, 99999),
            k=self.r.randint(1, 9),
            ms=self.r.randint(10, 9000),
            hex="%012x" % self.r.getrandbits(48),
            p=self.r.choice(["lru", "fifo", "ttl", "arc"]),
            a=self.r.randint(1, 64),
            cap=self.r.choice([64, 128, 256, 512]),
            t=self.r.choice(["orders", "events", "sessions", "audit"]),
            v="%d.%d.%d" % (self.r.randint(1, 9), self.r.randint(0, 20), self.r.randint(0, 9)),
            q=self.r.randint(0, 5000),
            c=self.r.choice(["AES256-GCM", "CHACHA20", "TLS13-AES128"]),
        )
        ts = "2026-%02d-%02dT%02d:%02d:%02d.%03dZ" % (
            self.r.randint(1, 12), self.r.randint(1, 28), self.r.randint(0, 23),
            self.r.randint(0, 59), self.r.randint(0, 59), self.r.randint(0, 999))
        return f"{ts} {lvl:5s} [{svc}] {msg} trace={self.r.getrandbits(64):016x}\n"


def build(tok, target_tokens, seed, marker_prefix):
    """Construit un contenu dont la tokenisation fait exactement target_tokens."""
    g = Gen(seed)
    uid = uuid.uuid4().hex[:12]
    m_debut = f"MARQUEUR-DEBUT-{marker_prefix}-{uid}"
    m_milieu = f"MARQUEUR-MILIEU-{marker_prefix}-{uid}"
    m_fin = f"MARQUEUR-FIN-{marker_prefix}-{uid}"

    pool = "".join(g.line() for _ in range(target_tokens // 12 + 512))

    # troncature exacte du pool à target_tokens
    enc = tok.encode(pool)
    ids = enc.ids[:target_tokens]
    pool = tok.decode(ids)

    # insertion des marqueurs aux positions token exactes via les offsets
    enc = tok.encode(pool)
    offs = enc.offsets
    n = len(enc.ids)
    pos_debut = min(250, n // 4)
    pos_milieu = n // 2
    pos_fin = max(n - 250, 3 * n // 4)
    inserts = sorted([(pos_debut, m_debut), (pos_milieu, m_milieu),
                      (pos_fin, m_fin)], reverse=True)
    body = pool
    for pos, marker in inserts:
        char = offs[pos][0] if pos < len(offs) else len(body)
        body = body[:char] + "\n" + marker + "\n" + body[char:]

    # re-calage final sur target_tokens (les marqueurs ajoutent des tokens)
    ids = tok.encode(body).ids
    while len(ids) > target_tokens:
        body = tok.decode(ids[:target_tokens])
        ids = tok.encode(body).ids
    while len(ids) < target_tokens:
        body += " x"
        ids = tok.encode(body).ids
    body = tok.decode(ids[:target_tokens])
    return body, {"debut": m_debut, "milieu": m_milieu, "fin": m_fin}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--levels", default="8192,32768,65536")
    ap.add_argument("--seed", type=int, default=20261019)
    args = ap.parse_args()

    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(args.tokenizer)

    out = {"tokenizer": args.tokenizer, "levels": {}}
    for lvl in [int(x) for x in args.levels.split(",")]:
        body, markers = build(tok, lvl, args.seed + lvl, f"L{lvl}")
        ids = tok.encode(body).ids
        out["levels"][str(lvl)] = {
            "content": body,
            "tokens": len(ids),
            "markers": markers,
        }
        print(f"level={lvl} tokens={len(ids)} chars={len(body)}")

    # conversation multi-tour : préfixe 32K + 4 tours de ~200 tokens
    base, markers = build(tok, 32768, args.seed + 999, "MT")
    turns = []
    g = Gen(args.seed + 1000)
    for i in range(4):
        extra = "".join(g.line() for _ in range(13))
        turns.append(extra)
    out["multiturn"] = {
        "base": base,
        "turns": turns,
        "markers": markers,
        "base_tokens": len(tok.encode(base).ids),
        "turn_tokens": [len(tok.encode(t).ids) for t in turns],
    }
    print("multiturn base=%d turns=%s" % (
        out["multiturn"]["base_tokens"], out["multiturn"]["turn_tokens"]))

    with open(args.out, "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print("written", args.out)


if __name__ == "__main__":
    main()
