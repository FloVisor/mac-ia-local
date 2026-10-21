"""Collect from the Mac via strict direct SSH. No remote files or packages installed."""
import concurrent.futures
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import yaml

BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--details', action='store_true')
parser.add_argument('--output', type=Path, default=BASE.parent / 'evidence' / datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'))
args = parser.parse_args()
DEST = args.output

# Supply the already-installed pure Python YAML parser in memory when absent remotely.
# This avoids installing packages or copying unfiltered configurations to the Mac.
sources = {'yaml' + ('.' + p.stem if p.stem != '__init__' else ''): p.read_text()
           for p in Path(yaml.__file__).parent.glob('*.py')}
bootstrap = '''import sys, importlib.abc, importlib.util
try:
 import yaml
except ImportError:
 class MemoryYaml(importlib.abc.MetaPathFinder, importlib.abc.Loader):
  def find_spec(self, fullname, path=None, target=None):
   if fullname in SOURCES: return importlib.util.spec_from_loader(fullname,self,is_package=fullname=='yaml')
  def create_module(self,spec): return None
  def exec_module(self,module): exec(compile(SOURCES[module.__name__],'<memory-yaml>','exec'),module.__dict__)
 sys.meta_path.insert(0,MemoryYaml())
'''
detail_mode = args.details
collector = (BASE / 'collect_remote.py').read_text()
if detail_mode:
    collector = collector.split("if __name__ == '__main__':")[0] + '\n' + (BASE / 'collect_details.py').read_text()
payload = 'SOURCES=' + repr(sources) + '\n' + bootstrap + '\n' + collector


def collect(host):
    mode = 'proxmox' if host == '192.168.201.39' else 'docker'
    dest = DEST / (host + ('.details' if detail_mode else '') + '.json')
    if dest.exists():
        raise FileExistsError(f'Refusing to replace existing evidence: {dest}')
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                        '-o', 'PreferredAuthentications=publickey', '-o', 'ConnectTimeout=8',
                        'root@' + host, 'python3 - ' + mode], input=payload, capture_output=True, text=True, timeout=240)
    if p.returncode:
        return {'host': host, 'exit': p.returncode, 'stderr': p.stderr[:1500]}
    data = json.loads(p.stdout)
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    return {'host': host, 'path': str(dest), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
            'containers': len(data.get('docker', {}).get('containers', [])), 'errors': data['errors']}


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(collect, ['docker-01', 'docker-02', 'docker-03', '192.168.201.39']):
            print(json.dumps(result, ensure_ascii=False))
