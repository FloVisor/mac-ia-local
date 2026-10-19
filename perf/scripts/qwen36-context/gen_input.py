#!/usr/bin/env python3
"""Générateur d'entrées à longueur contrôlée — campagne fenêtre de contexte
Qwen3.6-35B-A3B-4bit sur oMLX (Mac M4 Max 48 Go).

Méthode implémentée :
- tokenisation réelle via tokenizer.json du snapshot HF local (jamais mots->tokens) ;
- marqueurs uniques « MARQUEUR-<POSITION>-<uuid> » noyés dans du texte technique
  réaliste (logs / code / config / métriques), non répétitif (RNG seedé par niveau) :
    * DEBUT  : marqueur dans les 500 premiers tokens du prompt rendu ;
    * MILIEU : marqueur exactement à N/2 (index 0-based du premier token du marqueur) ;
    * FIN    : marqueur dans les 500 derniers tokens de l'entrée ;
- budget mission : entrée + sortie <= N - 2048, avec max_tokens par variante
  (ack: 64, rétention: 512) ;
- positions calées par pads à compte de tokens exact, corrigés itérativement
  sur la tokenisation complète (les fusions de tokens aux frontières de lignes
  rendent les comptes par ligne non additifs).

Les données produites vont dans toolchains/ (non versionné) ; ce script est versionnable.

Interpréteur requis : transformers + tokenizers (p. ex. venv vllm de la campagne).
"""
import argparse
import glob
import json
import os
import random
import sys
import uuid

DEFAULT_SNAPSHOT_GLOB = (
    "~/.cache/huggingface/hub/models--mlx-community--Qwen3.6-35B-A3B-4bit/"
    "snapshots/*/tokenizer.json"
)

SERVICES = [
    "auth-svc", "api-gateway", "ledger", "queue-mgr", "indexer", "cache-daemon",
    "scheduler", "webhook-dispatch", "metrics-aggr", "session-store", "search-idx",
    "billing-core", "notify-relay", "feature-flags", "rate-limiter", "doc-store",
]
LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG", "AUDIT"]
LOG_MSGS = [
    "request completed status={st} bytes={n}",
    "retry attempt={k} backoff={ms}ms cause=upstream_timeout",
    "cache miss key=ctx:{hex} eviction=policy-{p}",
    "connection pool saturated active={a}/{cap}",
    "schema drift detected table={t} version={v}",
    "partition rebalanced shard={k} moved={n} rows",
    "token refresh ok sub=user-{n} ttl={ms}s",
    "backpressure signal queue_depth={q} consumers={a}",
    "compaction finished segment={hex} reclaimed={n}MB",
    "health probe failed endpoint={svc2} attempt={k}",
    "rate limit tripped key={hex} window={ms}s",
    "index rebuild done docs={n} shards={k} took={dur}ms",
    "gc pause {ms}ms heap_used={n}MB",
    "subscription reconciled topic={t} lag={q}",
    "warmup finished model={svc2} batches={k} took={dur}ms",
    "trace span closed id={hex} duration={dur}ms",
    "lease acquired key={hex} ttl={ms}s holder={svc2}",
    "dedupe window flushed entries={n} duplicates={k}",
]
FNAMES = [
    "process_batch", "validate_schema", "aggregate_metrics", "transform_records",
    "resolve_refs", "compact_segments", " " "enrich_document", "normalize_keys",
    "merge_shards", "prune_index", "sync_remote", "audit_entries",
    "decode_payload", "route_request", "checkpoint_state", "hydrate_cache",
]
ARGNAMES = ["records", "payload", "entries", "events", "docs", "batch", "shard", "snapshot"]
CODE_TEMPLATES = [
    "    {var} = await {fn}({arg}, timeout={n})",
    "    def {fn}({arg}, *, depth={n}): return self._{fw}({arg})",
    "    result = {fn}({arg}) or DEFAULT_{up}",
    "    async with self._lock: await self.{fn}({arg}, retries={n})",
    "    for {var} in {arg}: yield transform({var}, depth={n})",
    "    assert len({arg}) >= {n}, f\"{arg} too short\"",
    "    return {fn}({arg}) if {arg} else fallback_{fw}()",
]
CONFIG_KEYS = [
    "replication_factor", "max_queue_depth", "lease_ttl_seconds", "compaction_interval",
    "shard_count", "retry_budget", "cache_ttl", "worker_threads", "batch_max_bytes",
    "healthcheck_path", "index_refresh", "session_grace", "upload_limit_mb",
]
YAML_TEMPLATES = [
    "  {key}: {val}",
    "    - name: {svc} image=registry.local/{svc}:{v}",
    "      {key}: {val}",
    "  {key}:  # tuned {i}",
]
METRIC_TEMPLATES = [
    "ctx_prefill_tokens{{level=\"{v}\"}} {n}",
    "queue_depth{{svc=\"{svc}\"}} {n}",
    "request_duration_seconds_bucket{{le=\"{ms}\"}} {n}",
    "cache_hit_ratio{{shard=\"{k}\"}} 0.{pct}",
    "gpu_wired_bytes{{model=\"{svc}\"}} {n}",
]

QUESTIONS = {
    "ack": "Réponds uniquement: ACK.",
    "ack_a": "Réponds uniquement: ACK-ALPHA.",
    "ack_b": "Réponds uniquement: ACK-BRAVO.",
    "debut": (
        "Question: le texte technique ci-dessus contient un marqueur unique au format "
        "MARQUEUR-DEBUT-<identifiant>, placé dans les premiers tokens du document. "
        "Restitue ce marqueur exactement, caractère pour caractère, sans aucun autre texte."
    ),
    "milieu": (
        "Question: le texte technique ci-dessus contient un marqueur unique au format "
        "MARQUEUR-MILIEU-<identifiant>, placé exactement au milieu du document. "
        "Restitue ce marqueur exactement, caractère pour caractère, sans aucun autre texte."
    ),
    "fin": (
        "Question: le texte technique ci-dessus contient un marqueur unique au format "
        "MARQUEUR-FIN-<identifiant>, placé à la fin du document, dans les derniers tokens. "
        "Restitue ce marqueur exactement, caractère pour caractère, sans aucun autre texte."
    ),
}

VARIANT_MAX_TOKENS = {"ack": 64, "ack_a": 64, "ack_b": 64,
                      "debut": 512, "milieu": 512, "fin": 512}


class LineGen:
    """Texte technique réaliste, non répétitif, RNG seedé."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.seq = 0
        self.seen = set()

    def _uid(self):
        self.seq += 1
        return self.seq

    def _make(self):
        r = self.rng
        i = self._uid()
        kind = r.random()
        if kind < 0.45:
            ts = (
                f"2026-10-{r.randint(10, 17)}T{r.randint(0, 23):02d}:"
                f"{r.randint(0, 59):02d}:{r.randint(0, 59):02d}.{r.randint(0, 999):03d}Z"
            )
            lvl = r.choice(LOG_LEVELS)
            svc = f"{r.choice(SERVICES)}-{r.randint(1, 48)}"
            msg = r.choice(LOG_MSGS).format(
                st=r.choice([200, 201, 204, 301, 400, 404, 409, 422, 429, 500, 503]),
                n=r.randint(1, 99999), k=r.randint(1, 9), ms=r.randint(1, 9000),
                hex=f"{r.getrandbits(48):012x}", p=r.randint(1, 9),
                a=r.randint(1, 256), cap=r.randint(64, 512),
                t=r.choice(["events", "users", "txns", "docs", "sessions"]),
                v=f"{r.randint(1, 9)}.{r.randint(0, 9)}.{r.randint(0, 99)}",
                q=r.randint(1, 4096), dur=r.randint(1, 60000),
                svc2=r.choice(SERVICES), i=i,
            )
            return f"{ts} {lvl} [{svc}] {msg}\n"
        if kind < 0.70:
            fn = r.choice(FNAMES)
            arg = r.choice(ARGNAMES)
            var = r.choice(["acc", "row", "item", "buf", "out", "tmp", "res"])
            fw = r.choice(["walk", "scan", "fold", "reduce", "map"])
            line = r.choice(CODE_TEMPLATES).format(
                fn=fn, arg=arg, var=var, fw=fw, n=r.randint(1, 999),
                up=arg.upper(),
            )
            return f"{line}  # unit-{i:05d}\n"
        if kind < 0.85:
            svc = r.choice(SERVICES)
            line = r.choice(YAML_TEMPLATES).format(
                key=r.choice(CONFIG_KEYS),
                val=r.choice([
                    r.randint(1, 64), f"{r.randint(1, 9)}.{r.randint(0, 9)}",
                    f"\"{svc}-{r.randint(1, 99)}\"", f"{r.randint(1, 60000)}ms",
                    r.choice(["true", "false"]),
                ]),
                svc=svc, v=f"{r.randint(1, 9)}.{r.randint(0, 20)}", i=i,
            )
            return line + "\n"
        line = r.choice(METRIC_TEMPLATES).format(
            v=f"{r.randint(1, 9)}.{r.randint(0, 9)}", n=r.randint(1, 999999),
            svc=r.choice(SERVICES), ms=r.randint(1, 5000),
            k=r.randint(1, 32), pct=r.randint(10, 99),
        )
        return f"{line}  # scrape-{i:05d}\n"

    def line(self):
        for _ in range(30):
            s = self._make()
            if s not in self.seen:
                self.seen.add(s)
                return s
        self.seq += 1
        return f"# fallback unique line {self.seq:08d}\n"


class InputBuilder:
    def __init__(self, tokenizer_dir, level, seed, max_tokens, margin):
        from transformers import AutoTokenizer  # noqa: PLC0415
        self.tok = AutoTokenizer.from_pretrained(tokenizer_dir)
        self.level = level
        self.max_tokens = max_tokens
        self.margin = margin
        self.gen = LineGen(seed)

    # -- tokenisation -----------------------------------------------------
    def render(self, content):
        return self.tok.apply_chat_template(
            [{"role": "user", "content": content}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )

    def enc(self, s):
        return self.tok(s, add_special_tokens=False, return_offsets_mapping=True)

    def ntok(self, s):
        return len(self.enc(s)["input_ids"])

    # -- gabarit ---------------------------------------------------------
    def _measure_wrapper(self):
        sent = "SENTINEL-XYZ-0123456789"
        r = self.render(sent)
        e = self.enc(r)
        offs = e["offset_mapping"]
        c0 = r.index(sent)
        c1 = c0 + len(sent)
        pre = sum(1 for (a, b) in offs if b <= c0)
        post = sum(1 for (a, b) in offs if a >= c1)
        return {"pre": pre, "post": post}

    # -- pads à compte exact (déterministes) -------------------------------
    def pad_line(self, count):
        """Ligne de pad avec exactement `count` tokens (0 -> chaîne vide).

        Déterministe : ne dépend que de `count` (stabilité des fusions de
        frontières entre les itérations de correction).
        """
        if count <= 0:
            return ""
        words = [
            f"{((count * 2654435761 + i * 40503) % 0xFFFFFFFF):08x}"
            for i in range(400)
        ]

        def toks(n):
            return self.ntok("# pad " + " ".join(words[:n]) + "\n")

        lo, hi = 0, len(words)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if toks(mid) <= count:
                lo = mid
            else:
                hi = mid - 1
        base = "# pad " + " ".join(words[:lo]) if lo else ""
        base_t = toks(lo) if lo else 0
        rem = count - base_t
        for m in range(max(0, rem - 3), rem + 4):
            cand = base + (" x" * m if m else "") + "\n"
            if self.ntok(cand) == count:
                return cand
        raise RuntimeError(f"pad exact introuvable pour {count} tokens")

    # -- marqueurs ---------------------------------------------------------
    def marker_line(self, pos, marker):
        seq = {"DEBUT": "000001", "MILIEU": "000002", "FIN": "000003"}[pos]
        return (
            f"2026-10-17T21:00:00Z AUDIT [ctx-campaign] anchor: {marker} "
            f"seq={seq}\n"
        )

    # -- assemblage ---------------------------------------------------------
    def _assemble(self, frozen, pads):
        """Contenu : lignes gelées + pads exacts + lignes marqueurs.

        Structure : lines_A | padA | MARK_DEBUT | lines_B | padB | MARK_MILIEU |
        lines_C | padC | MARK_FIN | lines_D | padD
        """
        parts = []
        parts.extend(frozen["a"])
        parts.append(self.pad_line(pads["a"]))
        parts.append(self.marker_line("DEBUT", self.markers["debut"]))
        parts.extend(frozen["b"])
        parts.append(self.pad_line(pads["b"]))
        parts.append(self.marker_line("MILIEU", self.markers["milieu"]))
        parts.extend(frozen["c"])
        parts.append(self.pad_line(pads["c"]))
        parts.append(self.marker_line("FIN", self.markers["fin"]))
        parts.extend(frozen["d"])
        parts.append(self.pad_line(pads["d"]))
        return "".join(parts)

    def _locate(self, rendered, marker):
        """Index 0-based du premier token du marqueur.

        Compte les tokens entièrement situés avant le premier caractère du
        marqueur (le token fusionné « espace+MARQUEUR » n'est pas compté).
        """
        e = self.enc(rendered)
        offs = e["offset_mapping"]
        c0 = rendered.index(marker)
        return sum(1 for (a, b) in offs if b <= c0)

    def build(self):
        level = self.level
        self.markers = {
            "debut": f"MARQUEUR-DEBUT-{uuid.UUID(int=random.Random(level).getrandbits(128)).hex[:12]}",
            "milieu": f"MARQUEUR-MILIEU-{uuid.UUID(int=random.Random(level + 1).getrandbits(128)).hex[:12]}",
            "fin": f"MARQUEUR-FIN-{uuid.UUID(int=random.Random(level + 2).getrandbits(128)).hex[:12]}",
        }
        wrap = self._measure_wrapper()
        w_pre, w_post = wrap["pre"], wrap["post"]

        # coût rendu réel de chaque question (mesuré, pas estimé)
        probe_c = "".join(self.gen.line() for _ in range(3))
        base_t = self.ntok(self.render(probe_c))
        q_diff = {}
        for name, q in QUESTIONS.items():
            q_diff[name] = self.ntok(self.render(probe_c + "\n\n" + q)) - base_t
        q_max = max(q_diff.values())

        budget_input = level - self.margin - self.max_tokens  # N - 2048 - 512
        content_target = budget_input - q_max - w_pre - w_post

        # cibles de position (index 0-based du premier token du marqueur)
        p_debut_target = 250
        p_milieu_target = level // 2
        p_fin_target = content_target - 250  # dans les 500 derniers tokens

        m_debut = self.ntok(self.marker_line("DEBUT", self.markers["debut"]))
        m_milieu = self.ntok(self.marker_line("MILIEU", self.markers["milieu"]))
        m_fin = self.ntok(self.marker_line("FIN", self.markers["fin"]))

        # cibles par slot (approximation gloutonne initiale)
        slot_a = p_debut_target - w_pre
        slot_b = p_milieu_target - (w_pre + slot_a + m_debut)
        slot_c = p_fin_target - (w_pre + slot_a + m_debut + slot_b + m_milieu)
        slot_d = content_target - (slot_a + m_debut + slot_b + m_milieu + slot_c + m_fin)

        frozen = {"a": [], "b": [], "c": [], "d": []}
        for k, target in (("a", slot_a), ("b", slot_b), ("c", slot_c), ("d", slot_d)):
            acc = 0
            while True:
                line = self.gen.line()
                t = self.ntok(line)
                if acc + t > target:
                    break
                frozen[k].append(line)
                acc += t

        pads = {"a": 0, "b": 0, "c": 0, "d": 0}
        result = None
        for it in range(1, 9):
            content = self._assemble(frozen, pads)
            rendered = self.render(content + "\n\n" + QUESTIONS["ack"])
            pos = {m: self._locate(rendered, self.markers[m])
                   for m in ("debut", "milieu", "fin")}
            content_actual = self.ntok(self.render(content)) - w_pre - w_post
            # budget réel par variante
            budget_ok = True
            for name, q in QUESTIONS.items():
                t = self.ntok(self.render(content + "\n\n" + q))
                if t + VARIANT_MAX_TOKENS[name] > level - self.margin:
                    budget_ok = False
            err = {
                "debut": p_debut_target - pos["debut"],
                "milieu": p_milieu_target - pos["milieu"],
                "fin": p_fin_target - pos["fin"],
                "total": content_target - content_actual,
            }
            result = {"content": content, "pos": pos, "err": err,
                      "iterations": it, "content_tokens": content_actual,
                      "budget_ok": budget_ok}
            if (err["milieu"] == 0 and 0 < pos["debut"] < 500
                    and pos["fin"] >= content_target - 500 and budget_ok):
                break
            pads["a"] = max(0, pads["a"] + err["debut"])
            pads["b"] = max(0, pads["b"] + err["milieu"])
            pads["c"] = max(0, pads["c"] + err["fin"])
            pads["d"] = max(0, pads["d"] + err["total"])
        return self._finalize(result, q_diff, budget_input, w_pre, w_post)

    def _finalize(self, result, q_diff, budget_input, w_pre, w_post):
        content = result["content"]
        variants = {}
        for name, q in QUESTIONS.items():
            prompt = content + "\n\n" + q
            t = self.ntok(self.render(prompt))
            variants[name] = {
                "prompt": prompt,
                "local_prompt_tokens": t,
                "max_tokens": VARIANT_MAX_TOKENS[name],
                "budget_ok": t + VARIANT_MAX_TOKENS[name] <= self.level - self.margin,
            }
        out = {
            "level": self.level,
            "max_tokens": self.max_tokens,
            "margin": self.margin,
            "budget_input_tokens": budget_input,
            "wrapper": {"pre": w_pre, "post": w_post},
            "markers": self.markers,
            "marker_positions_rendered": result["pos"],
            "marker_targets_rendered": {
                "debut": 250,
                "milieu": self.level // 2,
                "fin": "content_target-250 (dans les 500 derniers)",
            },
            "content_tokens": result["content_tokens"],
            "iterations": result["iterations"],
            "q_diff": q_diff,
            "variants": variants,
            "questions": QUESTIONS,
        }
        # variantes spéciales : probe (calibration serveur) et overflow (rejet attendu)
        probe_content = "".join(self.gen.line() for _ in range(120))
        probe_prompt = probe_content + "\n\n" + QUESTIONS["ack"]
        out["variants"]["probe"] = {
            "prompt": probe_prompt,
            "local_prompt_tokens": self.ntok(self.render(probe_prompt)),
            "max_tokens": 64,
            "budget_ok": True,
        }
        over_lines = []
        approx = 0
        while approx < self.level + 4096:
            s = self.gen.line()
            over_lines.append(s)
            approx += 14  # estimation basse, vérifiée ensuite
        over_prompt = "".join(over_lines) + "\n\n" + QUESTIONS["ack"]
        out["variants"]["overflow"] = {
            "prompt": over_prompt,
            "local_prompt_tokens": self.ntok(self.render(over_prompt)),
            "max_tokens": 64,
            "budget_ok": None,  # rejet attendu par le serveur (400)
        }
        return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level", type=int, required=True, help="N (fenêtre testée)")
    ap.add_argument("--out", required=True, help="chemin JSON de sortie")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--margin", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--tokenizer-dir", default=None)
    args = ap.parse_args()

    if args.tokenizer_dir:
        tdir = args.tokenizer_dir
    else:
        cands = sorted(glob.glob(os.path.expanduser(DEFAULT_SNAPSHOT_GLOB)))
        if not cands:
            sys.exit("tokenizer.json introuvable dans le cache HF")
        tdir = os.path.dirname(cands[-1])

    seed = args.seed if args.seed is not None else args.level
    b = InputBuilder(tdir, args.level, seed, args.max_tokens, args.margin)
    out = b.build()

    # vérifications dures
    problems = []
    for name in ("ack", "ack_a", "ack_b", "debut", "milieu", "fin"):
        v = out["variants"][name]
        if not v["budget_ok"]:
            problems.append(f"{name}: {v['local_prompt_tokens']}+{v['max_tokens']} > budget")
    if not (0 < out["marker_positions_rendered"]["debut"] < 500):
        problems.append("marqueur DEBUT hors des 500 premiers tokens")
    if out["marker_positions_rendered"]["milieu"] != out["level"] // 2:
        problems.append("marqueur MILIEU pas exactement a N/2")
    if out["variants"]["overflow"]["local_prompt_tokens"] <= out["level"]:
        problems.append("variante overflow <= N (rejet attendu impossible)")
    out["checks"] = {"problems": problems, "budget_ok": not problems}
    with open(args.out, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({
        "level": out["level"],
        "content_tokens": out["content_tokens"],
        "positions": out["marker_positions_rendered"],
        "budget_ok": out["checks"]["budget_ok"],
        "problems": problems,
        "iterations": out["iterations"],
    }, ensure_ascii=False, indent=1))
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
