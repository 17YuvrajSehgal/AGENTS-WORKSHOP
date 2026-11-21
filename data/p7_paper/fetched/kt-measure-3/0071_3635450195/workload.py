import contextlib
import hashlib
import io
import json
import shutil
from pathlib import Path

import fitz  # PyMuPDF, used only to create input PDFs

import pymupdf4llm_c
from pymupdf4llm_c import ConversionConfig, to_json
from pymupdf4llm_c.main import main as cli_main

SIDE = "head" if "/head/" in pymupdf4llm_c.__file__ else "base"
LIB = Path(f"/tmp/kt_3/build_{SIDE}/lib/libtomd.so")
WORK = Path(f"/tmp/kt_3/work_{SIDE}")
shutil.rmtree(WORK, ignore_errors=True)
WORK.mkdir(parents=True)


def make_pdf(path, n_pages, seed):
    doc = fitz.open()
    for p in range(n_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Heading {seed}.{p}", fontsize=20)
        y = 110
        for i in range(12):
            page.insert_text((72, y), f"Line {i} of page {p} seed {seed}: lorem ipsum dolor sit amet {i*p+seed}", fontsize=10)
            y += 14
        page.insert_text((72, y + 20), "- bullet item one", fontsize=10)
        page.insert_text((72, y + 34), "- bullet item two", fontsize=10)
    doc.save(str(path))
    doc.close()


pdfs = []
for k in range(4):
    pth = WORK / f"doc{k}.pdf"
    make_pdf(pth, 3 + k, k)
    pdfs.append(pth)

cfg = ConversionConfig(lib_path=LIB)
h = hashlib.sha256()
for rep in range(250):
    for k, pdf in enumerate(pdfs):
        out = WORK / f"out_{k}"
        res = to_json(pdf, output_dir=out, config=cfg, collect=(rep % 2 == 0))
        if rep % 2 == 0:
            h.update(json.dumps(res, sort_keys=True).encode())
        else:
            h.update(",".join(p.name for p in res).encode())

buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
    rc1 = cli_main([])
    rc2 = cli_main([str(WORK / "missing.pdf")])
h.update(f"{rc1},{rc2}".encode())
print("cli rcs", rc1, rc2)
print(h.hexdigest())
