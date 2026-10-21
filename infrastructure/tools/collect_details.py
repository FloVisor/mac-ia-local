"""Supplement to collect_remote.py; definitions supplied by run_audit.py."""

def metadata(path):
    p = Path(path)
    try:
        st = p.stat()
        return {"path": str(p), "realpath": str(p.resolve()), "symlink": p.is_symlink(),
                "mode": oct(st.st_mode & 0o7777), "uid": st.st_uid, "gid": st.st_gid,
                "bytes": st.st_size, "is_directory": p.is_dir()}
    except OSError as e:
        return {"path": str(p), "error": type(e).__name__}


def script_summary(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 300000:
        return metadata(path)
    text = p.read_text(errors='replace')
    return {**metadata(path), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "functions": re.findall(r'^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\)', text, re.M),
            "tools_referenced": sorted(set(re.findall(r'\b(docker|flock|ssh|rsync|tar|mariadb-dump|pg_dump|redis-cli|curl|wget|findmnt|systemctl|mount|umount|iptables|nft|kill|pkill|timeout|pg_isready)\b', text))),
            "paths_referenced": sorted(set(re.findall(r'/(?:srv|run/lock|usr/local|mnt|var/backups|root/\.ssh)/[\w./-]+', text))),
            "compose_actions": sorted(set(re.findall(r'\b(?:up|down|start|stop|restart|kill|create|rm)\b', text))) if 'compose' in text else [],
            "ssh_present": bool(re.search(r'\bssh\b', text)), "flock_present": 'flock' in text,
            "note": "Static indicators only, not proof of execution or fencing"}


def details():
    out = {"captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "hostname": socket.gethostname()}
    if sys.argv[1] == 'proxmox':
        exports = []
        for p in ['/etc/exports', *glob.glob('/etc/exports.d/*')]:
            if Path(p).is_file():
                exports.extend(x.strip() for x in Path(p).read_text().splitlines() if x.strip() and not x.lstrip().startswith('#'))
        out['nfs_exports'] = exports
        out['snapshots'] = {Path(p).stem: run(['pvesh', 'get', f'/nodes/{socket.gethostname()}/qemu/{Path(p).stem}/snapshot', '--output-format', 'json'], True) for p in glob.glob('/etc/pve/qemu-server/*.conf')}
        backup = Path('/mnt/pve/GAN-NAS-720-01/dump')
        out['backup_archive_metadata'] = [metadata(p) for p in sorted(backup.glob('*.vma.zst'), key=lambda p: p.stat().st_mtime, reverse=True)[:30]] if backup.is_dir() else []
        out['smart_health'] = {}
        if Path('/usr/sbin/smartctl').exists():
            disks = run(['lsblk', '-J', '-d', '-o', 'NAME,TYPE'], True) or {}
            for device in disks.get('blockdevices', []):
                if device.get('type') == 'disk':
                    out['smart_health'][device['name']] = run(['smartctl', '-H', '/dev/' + device['name']])
    else:
        ids = run(['docker','ps','-aq']).split()
        containers = run(['docker','inspect',*ids],True) if ids else []
        out['mount_metadata'] = [metadata(p) for p in sorted(set(m['Source'] for c in containers or [] for m in c.get('Mounts',[]) if m.get('Type')=='bind'))]
        out['traefik_static_arguments'] = []
        out['runtime_command_summary'] = []
        for c in containers or []:
            cfg=c.get('Config') or {}
            cmd=cfg.get('Cmd') or []
            args=[cmd] if isinstance(cmd,str) else cmd
            out['runtime_command_summary'].append({'container':c['Name'],'executable':str(args[0]).split()[0] if args else None,'argument_count':len(args),'entrypoint_present':bool(cfg.get('Entrypoint'))})
            if c['Name']=='/Traefik':
                out['traefik_static_arguments']=[clean(a) if not SENSITIVE.search(a.split('=',1)[0]) else '[REDACTED]' for a in args if a.startswith('--')]
        keep=Path('/etc/keepalived/keepalived.conf')
        scripts=set()
        if keep.exists():
            lines=[]; depth=0
            for line in keep.read_text().splitlines():
                if re.match(r'^\s*authentication\b',line): depth=1;continue
                if depth:
                    depth+=line.count('{')-line.count('}');continue
                if re.search(r'\bauth_pass\b',line): continue
                if re.match(r'^\s*(script|notify(?:_master|_backup|_fault|_stop)?)\b',line):
                    matches=re.findall(r'/(?:usr/local|srv)/[\w./-]+',line)
                    scripts.update(matches)
                lines.append(line)
            out['keepalived_without_authentication']='\n'.join(lines)
        scripts.update(glob.glob('/usr/local/sbin/*traefik*'))
        scripts.update(glob.glob('/usr/local/sbin/*backup*'))
        scripts.update(glob.glob('/usr/local/sbin/*super-agent*'))
        # Follow local script references, never execute their contents.
        for p in list(scripts):
            if Path(p).is_file():
                scripts.update(re.findall(r'/usr/local/(?:sbin|bin)/[\w.-]+',Path(p).read_text(errors='replace')))
        out['scripts']=[script_summary(p) for p in sorted(scripts)]
        out['custom_units']={}
        for p in glob.glob('/etc/systemd/system/*.service')+glob.glob('/etc/systemd/system/*.timer'):
            if Path(p).is_symlink():continue
            text=Path(p).read_text(errors='replace')
            out['custom_units'][p]={'sha256':hashlib.sha256(text.encode()).hexdigest(),'settings':[line for line in text.splitlines() if re.match(r'^(Description|User|Group|Type|Restart|After|Requires|Wants|OnCalendar|OnBootSec|OnUnitActiveSec|Persistent|RandomizedDelaySec|ReadWritePaths|ProtectSystem|NoNewPrivileges)=',line)],'executables':re.findall(r'^Exec\w+=[-+!:@]*([^\s]+)',text,re.M)}
        daemon=Path('/etc/docker/daemon.json')
        if daemon.is_file():
            out['daemon_configuration']=fields(json.loads(daemon.read_text()),['data-root','log-driver','log-opts','live-restore','default-address-pools','ipv6','ip6tables','iptables','userns-remap','no-new-privileges','icc','hosts'])
        net=Path('/etc/network/interfaces')
        out['interfaces_configuration']=[line for line in net.read_text().splitlines() if re.match(r'^\s*(auto|allow-hotplug|iface|address|gateway|netmask|mtu|bridge-ports|bridge-stp|bridge-fd|vlan-raw-device|source)\b',line)] if net.exists() else []
        rules=run(['nft','-j','list','ruleset'],True) or {}
        out['firewall']={'tables':[], 'chains':[], 'rule_count':0}
        for obj in rules.get('nftables',[]):
            if 'table' in obj:out['firewall']['tables'].append(fields(obj['table'],['family','name']))
            if 'chain' in obj:out['firewall']['chains'].append(fields(obj['chain'],['family','table','name','type','hook','policy','prio']))
            if 'rule' in obj:out['firewall']['rule_count']+=1
        out['networking_status']=run(['systemctl','show','networking.service','-p','Result','-p','ExecMainStatus','-p','ActiveState','-p','SubState'])
        # Only non-secret infrastructure directives; no request headers or auth material.
        nginx=Path('/srv/docker-shared/ollama-proxy/nginx.conf')
        if nginx.exists():
            out['ollama_proxy_configuration']={'path':str(nginx),'sha256':hashlib.sha256(nginx.read_bytes()).hexdigest(),'directives':[line.strip() for line in nginx.read_text().splitlines() if re.match(r'^\s*(upstream|server\s|location|listen|proxy_pass|proxy_connect_timeout|proxy_read_timeout|proxy_send_timeout|proxy_buffering|resolver)\b',line)]}
        out['shared_top_level']=[metadata(p) for p in sorted(Path('/srv/docker-shared').iterdir())]
    out['errors']=ERRORS
    return clean(out)


print(json.dumps(details(),ensure_ascii=False,indent=2))
