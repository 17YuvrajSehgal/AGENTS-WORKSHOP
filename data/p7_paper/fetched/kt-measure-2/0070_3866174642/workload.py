import hashlib
import os
import sys
import tempfile
import urllib.parse
import webbrowser

_home = tempfile.mkdtemp(prefix="kt_20440_")
os.environ["PREFECT_HOME"] = _home
os.environ["PREFECT_LOGGING_SETTINGS_PATH"] = os.path.join(_home, "logging.yml")
os.environ["PREFECT_PROFILES_PATH"] = os.path.join(_home, "profiles.toml")
os.environ["PREFECT_CLOUD_UI_URL"] = "http://127.0.0.1:1"
os.environ.pop("BROWSER", None)

import anyio
import httpx

import prefect.cli.cloud as cloud

N = 120
_counter = [0]


class FakeBrowser(webbrowser.BaseBrowser):
    """Stand-in for a real web browser: posts the login result to the callback."""

    def open(self, url, new=0, autoraise=True):
        qs = urllib.parse.urlparse(url).query
        callback = urllib.parse.parse_qs(qs)["callback"][0]
        i = _counter[0]
        _counter[0] += 1
        if i % 3 == 2:
            r = httpx.post(callback + "/failure", json={"reason": f"denied-{i}"})
        else:
            r = httpx.post(callback + "/success", json={"api_key": f"pnu_key_{i:04d}"})
        r.raise_for_status()
        return True


webbrowser.register("kt-fake", None, FakeBrowser("kt-fake"), preferred=True)


def main():
    results = []
    for _ in range(N):
        try:
            key = anyio.run(cloud.login_with_browser)
            results.append(("ok", key))
        except BaseException as exc:  # exit_with_error raises typer.Exit/SystemExit
            if isinstance(exc, (KeyboardInterrupt,)):
                raise
            results.append(("err", type(exc).__name__))
    for r in results[:6]:
        print(r)
    print(hashlib.sha256(repr(results).encode()).hexdigest())


if __name__ == "__main__":
    main()
