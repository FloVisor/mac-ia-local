#!/usr/bin/env python3
"""Apply the maintained patch only to a pristine upstream v3.14.1 checkout."""
from pathlib import Path
import subprocess,sys,shutil,json
here=Path(__file__).resolve().parent
repo=Path(sys.argv[1]).resolve()
manifest=json.loads((here/'manifest.json').read_text())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
if head!=manifest['commit']: raise SystemExit('Unexpected upstream revision; qualify the new version first')
if subprocess.check_output(['git','status','--porcelain','--','src/index.ts','src/hook-composition.integration.test.ts'],cwd=repo,text=True).strip(): raise SystemExit('Existing source changes: refuse to overwrite')
subprocess.run(['git','apply','--check',str(here/'3.14.1.patch')],cwd=repo,check=True)
subprocess.run(['git','apply',str(here/'3.14.1.patch')],cwd=repo,check=True)
shutil.copy2(here/'send-exact.local.test.ts',repo/'src/send-exact.local.test.ts')
print('Patched source only. Build/test/package with cwd set to this checkout, then install through openclaw plugins install.')
