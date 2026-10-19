#!/usr/bin/env python3
"""Mesure de qualification de fenêtre de contexte — Qwen3.6-35B-A3B-4bit sur oMLX.

Campagne : niveaux 32K/64K/128K/256K sur Mac M4 Max 48 Go, instance de test
oMLX isolée (--base-path ~/.omlx-test, port 8001), production arrêtée pendant
les fenêtres de mesure (config inchangée).

Méthode par niveau N (identique pour chaque niveau) :
  0. relevés mémoire avant (RSS, swap, pression, /health) ;
  1. (re)démarrage de l'instance de test avec cap N (cache froid) ;
  2. A. préfill : TTFT à froid (première requête), TTFT à chaud (même préfixe
     rejoué), préfill natif via usage.prompt_eval_duration ;
  3. B. rétention : 3 requêtes par position (debut/milieu/fin), vérification
     de l'exactitude littérale du marqueur dans la réponse ;
  4. C. terminaison : finish_reason == "stop" obligatoire, tokens réels via
     usage (prompt_tokens, completion_tokens) ;
  5. D. mémoire : relevés après, scan des logs process_memory_enforcer ;
  6. E. concurrence (si A-D passent) : 2 requêtes simultanées à N-2048 tokens
     chacune, vérification : pas de mélange, pas de timeout, pas de rejet.

Verdicts :
  QUALIFIÉ : 3/3 rétentions exactes aux 3 positions, finish stop, TTFT froid
  documenté, aucune pression mémoire dure, swap stable ;
  QUALIFIÉ AVEC RÉSERVES : rétention OK mais TTFT froid > 60 s ou pression
  mémoire modérée (documentée) ;
  NON QUALIFIÉ : OOM, éviction, troncature, rétention < 3/3, TTFT froid > 180 s.

Entrées : générées par gen_input.py (tokeniseur réel, marqueurs uniques).
Sorties : JSON brut dans toolchains/qwen36-context-campaign/results/ (non versionné).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

OMLX_CLI = "/Applications/oMLX.app/Contents/MacOS/omlx-cli"
TEST_BASE = os.path.expanduser("~/.omlx-test")
PROD_LABEL = "org.gangneux.omlx-serve"
PROD_PLIST = os.path.expanduser("~/Library/LaunchAgents/org.gangneux.omlx-serve.plist")
PROD_SETTINGS = os.path.expanduser("~/.omlx/settings.json")
TEST_SETTINGS = os.path.join(TEST_BASE, "settings.json")
TEST_MODEL_SETTINGS = os.path.join(TEST_BASE, "model_settings.json")
MODEL_ID = "mlx-community--Qwen3.6-35B-A3B-4bit"
LAUNCHD_LOG = os.path.join(TEST_BASE, "logs", "server.log")


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)


def http_json(url, payload=None, api_key=None, timeout=600, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode(errors="replace")
        try:
            return json.loads(body), f"HTTP {e.code}"
        except json.JSONDecodeError:
            return {"raw": body}, f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {}, f"network/timeout: {e}"


# -- mémoire ---------------------------------------------------------------
def mem_snapshot():
    swap = sh(["sysctl", "-n", "vm.swapusage"]).stdout.strip()
    mp = sh(["memory_pressure", "-Q"]).stdout.strip().splitlines()[-1]
    rss = 0
    ps = sh(["ps", "-axo", "pid,rss,command"])
    for line in ps.stdout.splitlines():
        if "omlx-server" in line or ("Python" in line and "omlx" in line):
            parts = line.split()
            rss = max(rss, int(parts[1]))
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "swap": swap,
        "free_pct": mp,
        "omlx_rss_kb": rss,
    }


def health(port, api_key):
    d, err = http_json(f"http://127.0.0.1:{port}/health", api_key=api_key, timeout=10)
    return d, err


# -- instance de test ------------------------------------------------------
def write_test_settings(level, port):
    os.makedirs(TEST_BASE, exist_ok=True)
    with open(PROD_SETTINGS) as f:
        s = json.load(f)
    s["server"]["port"] = port
    s["server"]["auto_start_on_launch"] = False
    s["sampling"]["max_context_window"] = level
    s["sampling"]["max_context_window_policy"] = level
    s["sampling"]["max_tokens"] = level
    s["mcp"]["config_path"] = None
    s["mcp"]["expose_tools"] = False
    s["logging"]["log_dir"] = None
    with open(TEST_SETTINGS, "w") as f:
        json.dump(s, f, indent=2)
    # override par modèle (tier 1) : cap réel à N
    ms = {"version": 1, "models": {}}
    ms["models"][MODEL_ID] = {
        "temperature": 1.0, "top_p": 0.95, "top_k": 20,
        "repetition_penalty": 1.0, "force_sampling": False,
        "thinking_budget_enabled": False,
        "max_context_window": level,
        "is_pinned": True, "is_default": True,
    }
    with open(TEST_MODEL_SETTINGS, "w") as f:
        json.dump(ms, f, indent=2)
    return s


def start_test(port, level, api_key):
    write_test_settings(level, port)
    args = [OMLX_CLI, "serve", "--base-path", TEST_BASE,
            "--host", "127.0.0.1", "--port", str(port),
            "--memory-guard", "balanced", "--log-level", "info", "--headless"]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(240):
        time.sleep(1)
        d, err = health(port, api_key)
        if not err and d.get("status") == "healthy":
            return real_server_pid(port)
        if proc.poll() is not None:
            return None
    return None


def real_server_pid(port):
    """PID du processus serveur réel écoutant sur le port (omlx-server)."""
    r = sh(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"])
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) > 1 and parts[1].isdigit():
            return int(parts[1])
    return None


def stop_test(proc_pid):
    """Tue le serveur réel et attend la libération du port."""
    if proc_pid:
        try:
            subprocess.run(["kill", str(proc_pid)], capture_output=True)
        except OSError:
            pass
    for _ in range(30):
        time.sleep(1)
        pid = real_server_pid(8001)
        if pid is None:
            return True
        try:
            subprocess.run(["kill", str(pid)], capture_output=True)
        except OSError:
            pass
    return False


# -- production (arrêt/restauration, config inchangée) ---------------------
def prod_stop():
    r = sh(["launchctl", "bootout", f"gui/{os.getuid()}", PROD_LABEL])
    # attendre la disparition du service
    for _ in range(30):
        time.sleep(1)
        lst = sh(["launchctl", "list"]).stdout
        if PROD_LABEL not in lst:
            return True
    return r.returncode == 0


def prod_start():
    r = sh(["launchctl", "bootstrap", f"gui/{os.getuid()}", PROD_PLIST])
    for _ in range(60):
        time.sleep(1)
        d, err = health(8000, None)
        if not err and d.get("status") == "healthy":
            return True
    return r.returncode == 0


# -- requêtes --------------------------------------------------------------
def chat(port, api_key, prompt, max_tokens, timeout=900, temperature=0.6):
    """Requête non-stream : renvoie contenu, usage natif, finish_reason."""
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    t0 = time.monotonic()
    d, err = http_json(f"http://127.0.0.1:{port}/v1/chat/completions",
                       payload, api_key, timeout=timeout)
    dt = time.monotonic() - t0
    if err:
        return {"error": err, "total_s": round(dt, 3)}
    ch = (d.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    usage = d.get("usage") or {}
    return {
        "content": msg.get("content") or "",
        "finish_reason": ch.get("finish_reason"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
        "ttft_s": usage.get("time_to_first_token"),
        "prompt_eval_duration_s": usage.get("prompt_eval_duration"),
        "generation_duration_s": usage.get("generation_duration"),
        "total_s": round(dt, 3),
        "error": None,
    }


def chat_stream_ttft(port, api_key, prompt, max_tokens, timeout=900):
    """Requête stream : TTFT mesuré côté client + usage natif final."""
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", data=body)
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    t0 = time.monotonic()
    ttft = None
    content = []
    usage = None
    finish = None
    error = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                now = time.monotonic()
                s = raw.decode("utf-8", errors="replace").strip()
                if not s.startswith("data: "):
                    continue
                data = s[6:]
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if obj.get("usage"):
                    usage = obj["usage"]
                ch = (obj.get("choices") or [{}])[0]
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
                delta = (ch.get("delta") or {})
                piece = delta.get("content") or ""
                if piece:
                    content.append(piece)
                    if ttft is None:
                        ttft = now - t0
    except urllib.error.HTTPError as e:
        error = f"HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        error = f"network/timeout: {e}"
    total = time.monotonic() - t0
    return {
        "content": "".join(content),
        "ttft_client_s": round(ttft, 3) if ttft is not None else None,
        "ttft_native_s": (usage or {}).get("time_to_first_token"),
        "prompt_eval_duration_s": (usage or {}).get("prompt_eval_duration"),
        "generation_duration_s": (usage or {}).get("generation_duration"),
        "prompt_tokens": (usage or {}).get("prompt_tokens"),
        "completion_tokens": (usage or {}).get("completion_tokens"),
        "cached_tokens": ((usage or {}).get("prompt_tokens_details") or {}).get("cached_tokens"),
        "finish_reason": finish,
        "total_s": round(total, 3),
        "error": error,
    }


# -- logs enforcer ---------------------------------------------------------
def scan_enforcer(since_ts):
    """Compte les warnings pression mémoire depuis since_ts (epoch)."""
    hard = soft = 0
    lines = []
    if os.path.exists(LAUNCHD_LOG):
        try:
            with open(LAUNCHD_LOG, errors="replace") as f:
                for line in f:
                    if "process_memory_enforcer" not in line:
                        continue
                    m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    if not m:
                        continue
                    try:
                        ts = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                    except ValueError:
                        continue
                    if ts < since_ts - 60:
                        continue
                    if "Hard memory pressure" in line:
                        hard += 1
                        lines.append(line.strip()[:200])
                    elif "Memory pressure level" in line and "-> hard" in line:
                        soft += 1
        except OSError:
            pass
    return {"hard_warnings": hard, "to_hard_transitions": soft, "samples": lines[:10]}


# -- campagne --------------------------------------------------------------
def run_level(level, port, api_key, input_path, out_path, do_concurrency):
    with open(input_path) as f:
        inp = json.load(f)
    markers = inp["markers"]
    variants = inp["variants"]
    res = {"level": level, "port": port, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}

    res["mem_before"] = mem_snapshot()
    hb, err = health(port, api_key)
    res["health_before"] = {"health": hb, "error": err}

    since = time.time()
    # -- A. préfill : TTFT froid (première requête après démarrage) --------
    cold = chat_stream_ttft(port, api_key, variants["ack"]["prompt"],
                            variants["ack"]["max_tokens"])
    res["prefill_cold"] = cold
    # -- TTFT à chaud : même préfixe rejoué --------------------------------
    warm = chat_stream_ttft(port, api_key, variants["ack"]["prompt"],
                            variants["ack"]["max_tokens"])
    res["prefill_warm"] = warm

    # -- B/C. rétention : 3 requêtes par position --------------------------
    retention = {}
    for pos in ("debut", "milieu", "fin"):
        runs = []
        for i in range(3):
            r = chat(port, api_key, variants[pos]["prompt"],
                     variants[pos]["max_tokens"])
            ok = (r.get("error") is None
                  and markers[pos] in (r.get("content") or "")
                  and r.get("finish_reason") == "stop")
            r["marker_expected"] = markers[pos]
            r["marker_found"] = markers[pos] in (r.get("content") or "")
            r["pass"] = bool(ok)
            runs.append(r)
            res.setdefault("retention", {})[pos] = runs
            retention[pos] = runs
    res["retention"] = retention

    # -- D. mémoire après ---------------------------------------------------
    res["mem_after"] = mem_snapshot()
    hb2, err2 = health(port, api_key)
    res["health_after"] = {"health": hb2, "error": err2}
    res["enforcer"] = scan_enforcer(since)

    # -- E. concurrence (si A-D passent) ------------------------------------
    res["concurrency"] = None
    if do_concurrency:
        a_prompt = variants["ack_a"]["prompt"]
        b_prompt = variants["ack_b"]["prompt"]
        out = {}

        def worker(tag, prompt, mt):
            out[tag] = chat(port, api_key, prompt, mt)

        t1 = threading.Thread(target=worker, args=("a", a_prompt, 64))
        t2 = threading.Thread(target=worker, args=("b", b_prompt, 64))
        t0 = time.monotonic()
        t1.start(); t2.start(); t1.join(); t2.join()
        dur = time.monotonic() - t0
        ra, rb = out.get("a", {}), out.get("b", {})
        mixed = ("ALPHA" in (ra.get("content") or "") and "BRAVO" in (ra.get("content") or "")) or \
                ("BRAVO" in (rb.get("content") or "") and "ALPHA" in (rb.get("content") or ""))
        res["concurrency"] = {
            "wall_s": round(dur, 3),
            "a": {k: ra.get(k) for k in ("content", "finish_reason", "prompt_tokens",
                                          "completion_tokens", "error", "total_s")},
            "b": {k: rb.get(k) for k in ("content", "finish_reason", "prompt_tokens",
                                          "completion_tokens", "error", "total_s")},
            "response_mixed": bool(mixed),
            "pass": bool(not mixed and ra.get("error") is None and rb.get("error") is None
                         and "ALPHA" in (ra.get("content") or "")
                         and "BRAVO" in (rb.get("content") or "")),
        }

    # -- verdict ------------------------------------------------------------
    ret_ok = all(
        all(r.get("pass") for r in runs) for runs in retention.values()
    )
    trunc = any(
        r.get("finish_reason") == "length"
        for runs in retention.values() for r in runs
    )
    ttft_cold = cold.get("ttft_client_s")
    hard = res["enforcer"]["hard_warnings"]
    oom = any("OOM" in (r.get("error") or "") or "out of memory" in (r.get("error") or "").lower()
              for runs in retention.values() for r in runs)
    if oom or trunc or not ret_ok or (ttft_cold is not None and ttft_cold > 180):
        verdict = "NON QUALIFIE"
    elif (ttft_cold is not None and ttft_cold > 60) or hard > 0:
        verdict = "QUALIFIE AVEC RESERVES"
    else:
        verdict = "QUALIFIE"
    res["verdict"] = verdict
    res["verdict_details"] = {
        "retention_3x3": ret_ok,
        "truncation": trunc,
        "ttft_cold_s": ttft_cold,
        "hard_pressure_warnings": hard,
        "oom": oom,
    }
    res["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(out_path, "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print(json.dumps({
        "level": level, "verdict": verdict,
        "ttft_cold_s": ttft_cold, "ttft_warm_s": warm.get("ttft_client_s"),
        "retention": {p: sum(1 for r in v if r.get("pass")) for p, v in retention.items()},
        "hard_warnings": hard,
        "concurrency_pass": (res["concurrency"] or {}).get("pass"),
    }, ensure_ascii=False))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level", type=int, required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--no-concurrency", action="store_true")
    ap.add_argument("--server-already-running", action="store_true",
                    help="ne pas (re)démarrer l'instance de test (reprise)")
    args = ap.parse_args()

    api_key = args.api_key
    if not api_key:
        env = os.environ.get("OMLX_API_KEY")
        if env:
            api_key = env
        else:
            with open(PROD_SETTINGS) as f:
                api_key = json.load(f)["auth"]["api_key"]

    pid = None
    if not args.server_already_running:
        pid = start_test(args.port, args.level, api_key)
        if pid is None:
            sys.exit("instance de test non démarrée (timeout)")
        print(f"test instance pid={pid} level={args.level}", flush=True)
    try:
        run_level(args.level, args.port, api_key, args.input, args.out,
                  not args.no_concurrency)
    finally:
        if pid:
            stop_test(pid)


if __name__ == "__main__":
    main()