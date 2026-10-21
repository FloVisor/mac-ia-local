"""Build the local VSIX from an explicit file allowlist (no dependencies)."""
from pathlib import Path
import json
import zipfile
root=Path(__file__).parent
p=json.loads((root/'package.json').read_text())
out=root.parents[1]/'artifacts'/f"{p['name']}-{p['version']}.vsix"
out.parent.mkdir(exist_ok=True)
manifest=f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
<Metadata><Identity Language="en-US" Id="{p['name']}" Version="{p['version']}" Publisher="{p['publisher']}"/><DisplayName>P3-C Observer</DisplayName><Description xml:space="preserve">Local read-only Codex observer</Description><Tags>codex</Tags><Categories>Other</Categories><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.90.0"/></Properties></Metadata>
<Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/>
<Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets></PackageManifest>'''
content='''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="py" ContentType="text/plain"/><Default Extension="md" ContentType="text/markdown"/><Default Extension="vsixmanifest" ContentType="text/xml"/></Types>'''
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('extension.vsixmanifest',manifest);z.writestr('[Content_Types].xml',content)
 for name in ['package.json','extension.js','collector.py','README.md']:
  z.write(root/name,'extension/'+name)
print(out)
