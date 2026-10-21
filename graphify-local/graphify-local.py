#!/usr/bin/env python3
"""Local per-worktree Graphify CLI. No LLM, hooks, global graph or server."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

EXCLUDES = [".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx",
    "id_rsa*", "id_ed25519*", "*credentials*", "*credential*", "*secrets*",
    "auth.json", ".ssh/", "node_modules/", ".venv/", "venv/", "vendor/",
    "__pycache__/", ".cache/", "artifacts/", "toolchains/", "isolated-home/",
    "backups/", "backup/", "*.bak", "*.backup", "dist/", "build/", "target/",
    "graphify-out/", ".codex-worktrees/"]

def current_head():
    result = subprocess.run(["git", "rev-parse", "--verify", "--quiet", "HEAD"], text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "UNBORN"

def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("refresh", "query", "explain", "path"):
        sys.exit("Usage: graphify-local refresh | query QUESTION | explain SYMBOL | path A B")
    cmd = args[0]
    expected = {"refresh": 0, "query": 1, "explain": 1, "path": 2}[cmd]
    if len(args) != expected + 1 or any(a.startswith("--") for a in args[1:]):
        sys.exit("Invalid arguments; supply quoted symbols/questions, no extra flags.")
    location = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], text=True, capture_output=True
    )
    if location.returncode:
        if "not a git repository" in location.stderr:
            sys.exit(
                "Graphify : le dossier courant n'est pas un dépôt Git.\n"
                "Entrez d'abord dans le dépôt à analyser, par exemple :\n"
                "  cd ~/Workspaces/mac-ia-local\n"
                "Puis relancez graphify-local. Aucun fichier n'a été indexé."
            )
        sys.exit(location.stderr.strip() or "Graphify : impossible d'identifier le dépôt Git.")
    root = Path(location.stdout.strip()).resolve()
    os.chdir(root)
    out = root / "graphify-out"
    if out.is_symlink():
        sys.exit("Refusing symlinked graphify-out")
    out.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["GRAPHIFY_BACKEND"] = "none"
    env["GRAPHIFY_OUT"] = "graphify-out"
    exe = shutil.which("graphify") or str(Path.home() / ".local/bin/graphify")
    with (out / ".local.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit("Graphify busy for this worktree; wait for the current command.")
        owner = out / ".local-owner.json"
        if owner.exists() and json.loads(owner.read_text())["root"] != str(root):
            sys.exit("Graph belongs to another worktree; do not reuse or merge it.")
        if cmd == "refresh":
            call = [exe, "extract", str(root), "--code-only", "--max-workers", "2"]
            for pattern in EXCLUDES:
                call.extend(["--exclude", pattern])
            # Exclude nested repositories/worktrees even if tracked by their parent.
            for directory, dirs, files in os.walk(root, followlinks=False):
                here = Path(directory)
                if here != root and (".git" in dirs or ".git" in files):
                    call.extend(["--exclude", here.relative_to(root).as_posix() + "/"])
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", "venv", "vendor", "__pycache__", ".cache", "artifacts", "toolchains", "isolated-home", "graphify-out", "build", "dist", "target"} and not (here / d).is_symlink()]
            subprocess.run(call, env=env, check=True)
            owner.write_text(json.dumps({"root": str(root), "branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(), "head": current_head()}, indent=2) + "\n")
        else:
            if not (out / "graph.json").is_file():
                sys.exit("No graph here. Run graphify-local refresh first.")
            if owner.exists():
                old = json.loads(owner.read_text())
                head = current_head()
                branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
                if old["head"] != head or old["branch"] != branch:
                    sys.exit("HEAD changed; run graphify-local refresh before querying.")
            call = [exe, *args]
            if cmd == "query":
                call.extend(["--budget", "1500"])
            subprocess.run(call, env=env, check=True)

if __name__ == "__main__":
    main()
