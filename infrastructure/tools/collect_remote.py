"""Read-only collector. Run through run_audit.py; stdout contains sanitized JSON only."""
import datetime
import glob
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

import yaml

ERRORS = []
SENSITIVE = re.compile(r"password|passwd|token|credential|authorization|auth_pass|private.?key|client.?secret|api.?key|access.?key|secret.?key|usersfile|basicauth|digestauth", re.I)


def clean(value):
    if isinstance(value, dict):
        return {str(k): ("[REDACTED]" if SENSITIVE.search(str(k)) else clean(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r"(https?://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", value)
        value = re.sub(r"([?&](?:token|key|secret|password|auth)=)[^&\s]+", r"\1[REDACTED]", value, flags=re.I)
        value = re.sub(r"((?:password|passwd|token|client_secret|api_key|access_key|secret_key)=)[^,;\s&]+", r"\1[REDACTED]", value, flags=re.I)
        if re.search(r"-----BEGIN .*PRIVATE KEY|\$2[aby]\$|\$apr1\$", value):
            return "[REDACTED]"
    return value


def run(argv, parse=False):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=25)
    except (OSError, subprocess.TimeoutExpired) as e:
        ERRORS.append({"command": argv, "error": type(e).__name__})
        return None if parse else ""
    if p.returncode:
        ERRORS.append({"command": argv, "exit": p.returncode, "stderr": clean(p.stderr[:1200])})
        return None if parse else ""
    if parse:
        try:
            return json.loads(p.stdout)
        except ValueError:
            ERRORS.append({"command": argv, "error": "invalid JSON"})
            return None
    return p.stdout.strip()


def fields(obj, names):
    return {k: obj[k] for k in names if k in obj}


def config_file(path, mode):
    """Read only declared non-secret YAML. Environment/command values never leave host."""
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > 2_000_000:
        return {"path": str(p), "status": "SKIPPED_SYMLINK_SIZE_OR_MISSING"}
    try:
        raw = p.read_bytes()
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return {"path": str(p), "status": "UNSUPPORTED_STRUCTURE"}
        out = {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest()}
        if mode == "compose":
            services = {}
            for name, s in (data.get("services") or {}).items():
                if not isinstance(s, dict):
                    continue
                item = fields(s, ["image", "container_name", "restart", "ports", "expose", "volumes", "networks", "depends_on", "deploy", "privileged", "read_only", "cap_add", "cap_drop", "security_opt", "user", "devices", "network_mode", "pid", "ipc", "mem_limit", "cpus", "secrets", "configs", "env_file"])
                env = s.get("environment") or {}
                item["environment_keys_only"] = list(env) if isinstance(env, dict) else [str(x).split("=", 1)[0] for x in env]
                item["healthcheck_present"] = bool(s.get("healthcheck"))
                item["command_present"] = "command" in s
                item["entrypoint_present"] = "entrypoint" in s
                labels = s.get("labels") or {}
                if isinstance(labels, list):
                    labels = dict(str(x).split("=", 1) if "=" in str(x) else (str(x), "") for x in labels)
                item["traefik_labels"] = {k: v for k, v in labels.items() if str(k).startswith("traefik.")}
                services[name] = item
            out["configuration"] = {"services": services, **fields(data, ["networks", "volumes", "secrets", "configs"])}
        else:
            out["configuration"] = fields(data, ["http", "tcp", "udp", "tls", "entryPoints", "providers", "api", "ping", "log", "accessLog", "metrics", "global", "certificatesResolvers", "serversTransport"])
            # Headers may carry credentials even with innocuous names: retain names only.
            for mw in ((out["configuration"].get("http") or {}).get("middlewares") or {}).values():
                if isinstance(mw, dict):
                    for key in ["customRequestHeaders", "customResponseHeaders"]:
                        if key in (mw.get("headers") or {}):
                            mw["headers"][key] = list(mw["headers"][key])
        return clean(out)
    except Exception as e:
        return {"path": str(p), "status": "PARSE_ERROR", "error_type": type(e).__name__}


def host_info():
    return {
        "hostname": socket.gethostname(), "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "os_release": Path('/etc/os-release').read_text(),
        "kernel": run(["uname", "-r"]), "uptime": run(["uptime"]),
        "memory": run(["free", "-b"]), "cpu": run(["lscpu", "-J"], True),
        "filesystems": run(["findmnt", "-J", "-o", "TARGET,SOURCE,FSTYPE,OPTIONS"], True),
        "disk_usage": run(["df", "-hT"]),
        "addresses": run(["ip", "-j", "address"], True), "routes": run(["ip", "-j", "route", "show", "table", "all"], True),
        "routes6": run(["ip", "-j", "-6", "route", "show", "table", "all"], True),
        "listeners": run(["ss", "-lntup"]), "failed_units": run(["systemctl", "--failed", "--no-pager", "--plain"]),
        "timers": run(["systemctl", "list-timers", "--all", "--no-pager"]),
        "sshd": run(["sshd", "-T"]),
    }


def docker_info():
    info = run(["docker", "info", "--format", "{{json .}}"], True) or {}
    out = {"info": fields(info, ["ServerVersion", "DockerRootDir", "Driver", "CgroupDriver", "CgroupVersion", "LiveRestoreEnabled", "SecurityOptions", "LoggingDriver", "NCPU", "MemTotal", "Swarm", "Containers", "ContainersRunning", "ContainersStopped", "Warnings"])}
    # Swarm info has no join tokens; no secret/config object data is requested.
    ids = run(["docker", "ps", "-aq", "--no-trunc"]).split()
    containers = run(["docker", "inspect", *ids], True) if ids else []
    out["containers"] = []
    compose_paths = set()
    for c in containers or []:
        cfg, hc, st = c.get("Config", {}), c.get("HostConfig", {}), c.get("State", {})
        labels = cfg.get("Labels") or {}
        for p in labels.get("com.docker.compose.project.config_files", "").split(','):
            if p and Path(p).name in ["compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.yaml"]:
                compose_paths.add(p)
        out["containers"].append({
            **fields(c, ["Id", "Name", "Created", "Image", "RestartCount", "Mounts"]),
            "state": fields(st, ["Status", "Running", "Paused", "Restarting", "OOMKilled", "Dead", "Pid", "ExitCode", "StartedAt", "FinishedAt"]),
            "health": fields(st.get("Health", {}), ["Status", "FailingStreak"]),
            "config": {**fields(cfg, ["Image", "User", "ExposedPorts", "WorkingDir", "StopSignal"]),
                       "environment_keys_only": [x.split("=", 1)[0] for x in cfg.get("Env", [])],
                       "healthcheck_present": bool(cfg.get("Healthcheck")),
                       "labels": {k: v for k, v in labels.items() if k.startswith(("traefik.", "com.docker.compose.", "com.docker.swarm."))}},
            "host_config": fields(hc, ["RestartPolicy", "NetworkMode", "PortBindings", "Privileged", "ReadonlyRootfs", "CapAdd", "CapDrop", "SecurityOpt", "Devices", "DeviceRequests", "PidMode", "IpcMode", "Memory", "MemorySwap", "NanoCpus", "CpuShares", "PidsLimit", "Ulimits", "LogConfig", "Dns", "ExtraHosts"]),
            "network": fields(c.get("NetworkSettings", {}), ["Ports", "Networks"]),
        })
    network_ids = run(["docker", "network", "ls", "-q"]).split()
    out["networks"] = run(["docker", "network", "inspect", *network_ids], True) if network_ids else []
    vols = run(["docker", "volume", "ls", "-q"]).split()
    out["volumes"] = run(["docker", "volume", "inspect", *vols], True) if vols else []
    image_ids = run(["docker", "image", "ls", "-q", "--no-trunc"]).split()
    imgs = run(["docker", "image", "inspect", *sorted(set(image_ids))], True) if image_ids else []
    out["images"] = [fields(x, ["Id", "RepoTags", "RepoDigests", "Created", "Architecture", "Os", "Size"]) for x in imgs or []]
    if (info.get("Swarm") or {}).get("ControlAvailable"):
        node_ids = run(["docker", "node", "ls", "-q"]).split()
        out["nodes"] = run(["docker", "node", "inspect", *node_ids], True) if node_ids else []
        service_ids = run(["docker", "service", "ls", "-q"]).split()
        out["services"] = []
        for service in run(["docker", "service", "inspect", *service_ids], True) if service_ids else []:
            spec = service.get("Spec", {})
            task = spec.get("TaskTemplate", {})
            cs = task.get("ContainerSpec", {})
            out["services"].append({"ID": service["ID"], "name": spec.get("Name"), "mode": spec.get("Mode"),
                                    "task": {**fields(task, ["Resources", "RestartPolicy", "Placement", "Networks", "LogDriver"]), "container": fields(cs, ["Image", "Mounts", "User", "ReadOnly", "Secrets", "Configs"])},
                                    "endpoint": service.get("Endpoint"), "update": fields(spec, ["UpdateConfig", "RollbackConfig"]),
                                    "tasks": run(["docker", "service", "ps", "--no-trunc", "--format", "{{json .}}", service["ID"]])})
        out["secrets_metadata"] = run(["docker", "secret", "ls", "--format", "{{json .}}"])
        out["configs_metadata"] = run(["docker", "config", "ls", "--format", "{{json .}}"])
    for pattern in ["/srv/docker-local/compose/*/compose.y*ml", "/srv/docker-local/compose/*/docker-compose.y*ml"]:
        compose_paths.update(glob.glob(pattern))
    out["compose"] = [config_file(p, "compose") for p in sorted(compose_paths)]
    out["traefik"] = [config_file(p, "traefik") for p in sorted(set(glob.glob('/srv/docker-shared/traefik/dynamic/*.y*ml') + glob.glob('/srv/docker-local/compose/traefik/*traefik*.y*ml')))]
    out["keepalived_active"] = run(["systemctl", "is-active", "keepalived"])
    keep = Path('/etc/keepalived/keepalived.conf')
    if keep.exists():
        # Strict line allowlist; no authentication or script body exported.
        out["keepalived"] = {"path": str(keep), "sha256": hashlib.sha256(keep.read_bytes()).hexdigest(),
             "structure": [line.strip() for line in keep.read_text().splitlines() if re.match(r'^\s*(vrrp_instance\b|vrrp_script\b|state\b|interface\b|virtual_router_id\b|priority\b|nopreempt\b|unicast_src_ip\b|unicast_peer\b|virtual_ipaddress\b|no_virtual_ipaddress\b|track_script\b|advert_int\b|[0-9a-fA-F:.]+(?:/\d+)?\s*(?:dev\s+\w+)?\s*$)', line)]}
    out["firewall_tables"] = run(["nft", "list", "tables"])
    return out


def proxmox_info():
    out = {"version": run(["pveversion", "-v"]), "vms": run(["qm", "list"]), "lxc": run(["pct", "list"])}
    for name, endpoint in [("cluster_status", "/cluster/status"), ("resources", "/cluster/resources"), ("storage_config", "/storage"), ("directory_mapping", "/cluster/mapping/dir"), ("backup_jobs", "/cluster/backup"), ("replication", "/cluster/replication")]:
        out[name] = run(["pvesh", "get", endpoint, "--output-format", "json"], True)
    node = socket.gethostname()
    for name, endpoint in [("network", f"/nodes/{node}/network"), ("firewall_options", f"/nodes/{node}/firewall/options"), ("firewall_rules", f"/nodes/{node}/firewall/rules"), ("tasks", f"/nodes/{node}/tasks")]:
        out[name] = run(["pvesh", "get", endpoint, "--output-format", "json"], True)
    out["vm_config"] = {}
    for path in sorted(glob.glob('/etc/pve/qemu-server/*.conf')):
        vm = {}
        for line in Path(path).read_text().splitlines():
            if ':' not in line or line.startswith('#'):
                continue
            k, v = line.split(':', 1)
            if re.fullmatch(r'(name|agent|bios|boot|cores|cpu|memory|balloon|numa|ostype|sockets|machine|onboot|startup|protection|scsihw|tags|net\d+|virtiofs\d+|scsi\d+|sata\d+|ide\d+|virtio\d+|hostpci\d+|efidisk\d+|tpmstate\d+|unused\d+)', k):
                vm[k] = v.strip()
        out["vm_config"][Path(path).stem] = vm
    out["block_devices"] = run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL"], True)
    out["lvs"] = run(["lvs", "--reportformat", "json", "-o", "vg_name,lv_name,lv_size,lv_attr,data_percent,metadata_percent"], True)
    out["ha_resources"] = run(["ha-manager", "config"])
    out["firewall_status"] = run(["pve-firewall", "status"])
    return out


if __name__ == '__main__':
    result = {"host": host_info()}
    result["proxmox" if sys.argv[1] == 'proxmox' else "docker"] = proxmox_info() if sys.argv[1] == 'proxmox' else docker_info()
    result["errors"] = ERRORS
    print(json.dumps(clean(result), ensure_ascii=False, indent=2))
