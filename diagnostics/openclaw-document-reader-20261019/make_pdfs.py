import subprocess, os, struct, zlib

TEXT = """Rapport de validation documentaire
Reference interne : DOC-2026-1019
Objet : verification de l extraction de texte et de l OCR.

Ce document contient du texte reel, selectionnable, encode dans le flux
de contenu du PDF. Il sert de temoin pour la conversion texte vers Markdown.

Points de controle :
1. Le titre doit etre restitue.
2. La reference DOC-2026-1019 doit apparaitre.
3. Le mot clef ZEBULON42 doit etre retrouve a l identique.
"""

def text_pdf(path, text):
    lines = text.splitlines()
    content = ["BT", "/F1 14 Tf", "50 780 Td", "16 TL"]
    for ln in lines:
        esc = ln.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        content.append(f"({esc}) Tj T*")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>")
    objs.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    open(path, "wb").write(out)

def jpeg_pdf(path, jpg):
    data = open(jpg, "rb").read()
    w, h = 1240, 1754
    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] /Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>".encode())
    content = f"q {w} 0 0 {h} 0 0 cm /Im0 Do Q".encode()
    objs.append(b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream")
    objs.append(f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    open(path, "wb").write(out)

text_pdf("texte.pdf", TEXT)
open("scan.txt","w").write("FACTURE SCANNEE\nNumero : SCAN-7788\nMontant total : 1 234,56 EUR\nClient : ZEBULON42\n")
subprocess.run(["cupsfilter","-m","application/pdf","scan.txt"], stdout=open("scan_src.pdf","wb"), stderr=subprocess.DEVNULL, check=True)
subprocess.run(["sips","-s","format","jpeg","-s","formatOptions","best","scan_src.pdf","--out","scan.jpg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
jpeg_pdf("scanne.pdf","scan.jpg")
print("ok", os.path.getsize("texte.pdf"), os.path.getsize("scanne.pdf"))
