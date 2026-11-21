import hashlib, json, logging, re, urllib.parse
import requests
from requests.adapters import HTTPAdapter
from requests.models import Response
from github_dependents_info import GithubDependentsInfo

logging.disable(logging.CRITICAL)

REPO = "acme/widget"
N_PAGES = 12
PER_PAGE = 30
PACKAGES = {"pkg1": "widget-core", "pkg2": "widget-cli", "pkg3": "widget-web"}


def build_page(pkg, page):
    rows = []
    for i in range(PER_PAGE):
        k = (hash_int(pkg) * 7 + page * PER_PAGE + i)
        owner = f"owner{k % 97}"
        name = f"repo{pkg}_{page}_{i}"
        stars = (k * 2654435761) % 5000
        rows.append(
            f'<div class="Box-row"><img class="avatar" src="https://avatars.example/{owner}.png"/>'
            f'<span><a data-hovercard-type="user" href="/{owner}">{owner}</a> / '
            f'<a data-hovercard-type="repository" href="/{owner}/{name}">{name}</a></span>'
            f'<div><span><svg class="octicon-star"></svg>{stars:,}</span></div></div>'
        )
    pag = '<div class="paginate-container"><a href="#">Previous</a>'
    if page < N_PAGES:
        pag += f'<a href="https://github.com/{REPO}/network/dependents?package_id={pkg}&page={page + 1}">Next</a>'
    pag += "</div>"
    pkglinks = "".join(
        f'<a href="/{REPO}/network/dependents?package_id={pid}"><span>{pn}</span></a>' for pid, pn in PACKAGES.items()
    )
    total = N_PAGES * PER_PAGE + 57
    return (
        f"<html><body>{pkglinks}<a class=\"btn-link selected\">{total:,} Repositories</a>"
        + "".join(rows) + pag + "</body></html>"
    )


def hash_int(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:6], 16)


_cache = {}


def fake_send(self, request, **kwargs):
    # Stand-in for GitHub network I/O.
    q = urllib.parse.parse_qs(urllib.parse.urlparse(request.url).query)
    pkg = q.get("package_id", ["pkg1"])[0]
    page = int(q.get("page", ["1"])[0])
    key = (pkg, page)
    if key not in _cache:
        _cache[key] = build_page(pkg, page).encode()
    resp = Response()
    resp.status_code = 200
    resp._content = _cache[key]
    resp.url = request.url
    resp.request = request
    resp.headers["Content-Type"] = "text/html"
    return resp


HTTPAdapter.send = fake_send

out = []
for opts in [
    dict(max_scraped_pages=1),
    dict(max_scraped_pages=3, sort_key="stars"),
    dict(max_scraped_pages=0),
    dict(max_scraped_pages=5, min_stars=1000),
    dict(debug=True, max_scraped_pages=2),
    dict(),
]:
    g = GithubDependentsInfo(REPO, time_delay=0, **opts)
    res = g.collect()
    out.append(json.dumps(res, sort_keys=True, default=str))
    print(opts, res["total_dependents_number"] if "total_dependents_number" in res else len(res.get("public_dependents", [])), g.total_public_sum)
print(hashlib.sha256("\n".join(out).encode()).hexdigest())
