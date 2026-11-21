"""Look up candidate related papers in arXiv and DBLP, so references are never typed from memory.

  python -I analysis/refs_lookup.py arxiv  "<title words>" ...
  python -I analysis/refs_lookup.py dblp   "<title words>" ...
  python -I analysis/refs_lookup.py id     2302.07867 ...      (exact arXiv ids)

Prints what the service returns (title, authors, year, venue, id/DOI).
Results are appended to related-papers/_lookup.jsonl as the record of where
each reference came from.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "related-papers"
OUT.mkdir(exist_ok=True)
A = "{http://www.w3.org/2005/Atom}"
UA = {"User-Agent": "refs-lookup/1.0 (research script)"}


def get(url):
    for wait in (0, 5, 15, 30):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                body = r.read().decode("utf-8", "replace")
            if "Rate exceeded" not in body[:200]:
                return body
        except Exception as e:  # noqa: BLE001
            err = e
    raise RuntimeError(f"failed: {url}")


def arxiv(params):
    body = get("https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params))
    out = []
    for e in ET.fromstring(body).findall(A + "entry"):
        out.append({
            "src": "arxiv", "id": e.find(A + "id").text.rsplit("/", 1)[-1],
            "title": " ".join(e.find(A + "title").text.split()),
            "authors": [a.find(A + "name").text for a in e.findall(A + "author")],
            "published": e.find(A + "published").text[:10],
            "comment": (e.findtext("{http://arxiv.org/schemas/atom}comment") or ""),
            "journal_ref": (e.findtext("{http://arxiv.org/schemas/atom}journal_ref") or ""),
        })
    return out


def dblp(q):
    """Crossref (publisher metadata); DBLP's API blocks scripts. Mode name kept as 'dblp'."""
    body = get("https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.bibliographic": q, "rows": 3,
        "select": "title,author,DOI,container-title,issued,page,volume,issue,type,publisher"}))
    out = []
    for i in json.loads(body)["message"]["items"]:
        out.append({"src": "crossref", "title": (i.get("title") or [""])[0],
                    "authors": [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in i.get("author", [])],
                    "year": (i.get("issued", {}).get("date-parts") or [[None]])[0][0],
                    "venue": (i.get("container-title") or [""])[0], "pages": i.get("page"),
                    "volume": i.get("volume"), "number": i.get("issue"), "type": i.get("type"),
                    "publisher": i.get("publisher"), "doi": i.get("DOI")})
    return out


sys.stdout.reconfigure(encoding="utf-8", errors="replace")
mode, args = sys.argv[1], sys.argv[2:]
with open(OUT / "_lookup.jsonl", "a", encoding="utf-8") as log:
    for a in args:
        if mode == "arxiv":
            res = arxiv({"search_query": 'ti:"%s"' % a, "max_results": 3})
        elif mode == "id":
            res = arxiv({"id_list": a})
        else:
            res = dblp(a)
        print(f"\n### {mode}: {a}")
        for r in res:
            log.write(json.dumps({"query": a, **r}, ensure_ascii=False) + "\n")
            print("  ", json.dumps(r, ensure_ascii=False)[:600])
        if not res:
            print("   (no result)")
        time.sleep(3.2)
