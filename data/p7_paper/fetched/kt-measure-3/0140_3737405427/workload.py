import hashlib
import random

from foamlib._files._parsing import ParsedFile
from foamlib._files._parsing._parser import _skip, parse
from foamlib._files._parsing.exceptions import FoamFileDecodeError
from foamlib.typing import FileDict

random.seed(742)

HEADER = b"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;   // version
    format      ascii; /* inline */
    class       dictionary;
    object      testDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

"""


def make_file(n):
    parts = [HEADER]
    for i in range(n):
        parts.append(b"// entry %d comment \\\n continued line\n" % i)
        parts.append(b"/* block\n comment %d\n */\n" % i)
        parts.append(b"sub%d\n{\n    // inner\n    a%d   %d;  // trailing\n" % (i, i, random.randint(0, 1000)))
        parts.append(b"    b%d /* mid */ %.6g;\n" % (i, random.random()))
        parts.append(b"    c%d (1 2 3 /* x */ 4);\n    \t\n" % i)
        parts.append(b"    d%d word%d; // \\\n\n}\n\n" % (i, i))
    return b"".join(parts)


h = hashlib.sha256()
data = make_file(1500)
for rep in range(3):
    res = parse(data, target=FileDict)
    h.update(repr(res).encode())
pf = ParsedFile(data)
h.update(repr(sorted(pf.keys(), key=str)[:50]).encode())

# direct _skip calls
snippets = [
    b"   // c \\\n more\n  x",
    b"/* a */ /* b */\n\t y",
    b"// no newline at end",
    b"  \n  // c\n  /* d */  z",
    b"//\\",
    b"// abc\\\nq\nrest",
]
for _ in range(20000):
    for s in snippets:
        h.update(str(_skip(s, 0)).encode())
        h.update(str(_skip(s, 0, newline_ok=False)).encode())
        h.update(str(_skip(bytearray(s), 0)).encode())

for s in [b"  /* unterminated", b"a /* x"]:
    try:
        parse(s, target=FileDict)
        h.update(b"ok")
    except FoamFileDecodeError as e:
        h.update(b"err")


def run_phase(h):
    from foamlib._files._parsing._parser import _skip, parse
    from foamlib._files._parsing.exceptions import FoamFileDecodeError
    from foamlib.typing import FileDict
    res = parse(data, target=FileDict)
    h.update(repr(res).encode())
    for _ in range(3000):
        for s in snippets:
            h.update(str(_skip(s, 0)).encode())
            h.update(str(_skip(s, 0, newline_ok=False)).encode())
    for s in [b"  /* unterminated", b"a /* x"]:
        try:
            parse(s, target=FileDict)
            h.update(b"ok")
        except FoamFileDecodeError:
            h.update(b"err")


# Phase 2: pure-Python configuration (as when the compiled extension is not
# installed). On base the extension does not exist, so this is a no-op there.
import sys
for name in [m for m in sys.modules if m == "foamlib" or m.startswith("foamlib.")]:
    del sys.modules[name]
sys.modules["foamlib.foamlib_rust"] = None
run_phase(h)

print(h.hexdigest())
