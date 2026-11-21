# Helpers for the build agent

Rebuild ONE environment from the existing source tree (no git access), e.g.
with another Python version or as a normal (non-editable) install for
packages with C extensions:

    bash ~/agent/rebuild_env.sh <base|head> <python-version> [editable|normal] [extra packages...]

Example: `bash ~/agent/rebuild_env.sh base 3.11 normal` then the same for
`head`. Always rebuild BOTH sides the same way. Dependencies are frozen at
the date in job.json automatically.

The project folder that gets installed is in `pkgdir.txt` (chosen by setup
as the nearest folder with pyproject.toml/setup.py above the changed .py
files). To install a different folder, prefix the command with
`KT_PKGDIR=<path inside src>`, e.g.
`KT_PKGDIR=libs/nox-py bash ~/agent/rebuild_env.sh base 3.12`.

Check the result at any time:

    python3 ~/agent/check.py . workload.py
