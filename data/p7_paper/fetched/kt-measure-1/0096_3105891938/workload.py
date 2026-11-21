import asyncio
import hashlib
import json
import os
import random
import shutil

import yaml

from ocode_python.tools.data_tools import JsonYamlTool
from ocode_python.tools.find_tool import FindTool
from ocode_python.tools.head_tail_tool import HeadTool, TailTool
from ocode_python.tools.notebook_tools import NotebookEditTool, NotebookReadTool

ROOT = "/tmp/kt_2/work"
rng = random.Random(1234)


def setup():
    if os.path.exists(ROOT):
        shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    # directory tree
    for a in range(6):
        for b in range(6):
            d = os.path.join(ROOT, "tree", f"d{a}", f"s{b}")
            os.makedirs(d)
            for c in range(8):
                ext = [".py", ".txt", ".md"][c % 3]
                with open(os.path.join(d, f"f{c}{ext}"), "w") as f:
                    f.write("x" * (c * 300))
    # text file
    with open(os.path.join(ROOT, "big.txt"), "w") as f:
        for i in range(20000):
            f.write(f"line {i} {rng.randint(0, 10**6)}\n")
    # data
    data = {
        "users": [
            {"name": f"u{i}", "age": rng.randint(18, 80), "tags": [f"t{j}" for j in range(3)]}
            for i in range(200)
        ],
        "config": {"debug": False, "level": 3},
    }
    with open(os.path.join(ROOT, "data.json"), "w") as f:
        json.dump(data, f)
    with open(os.path.join(ROOT, "data.yaml"), "w") as f:
        yaml.safe_dump(data, f)
    return json.dumps(data)


def make_notebook(path):
    cells = []
    for i in range(30):
        if i % 3 == 0:
            cells.append({"cell_type": "markdown", "metadata": {}, "source": [f"# Title {i}"]})
        else:
            cells.append({
                "cell_type": "code", "metadata": {}, "execution_count": i,
                "source": [f"x = {i}\n", "print(x)"],
                "outputs": [{"output_type": "stream", "name": "stdout", "text": [f"{i}\n"]}],
            })
    nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3"}},
          "nbformat": 4, "nbformat_minor": 5}
    with open(path, "w") as f:
        json.dump(nb, f)


def rec(out, r):
    out.append((bool(r.success), r.output if r.success else ""))


async def main():
    data_str = setup()
    out = []
    find = FindTool()
    head = HeadTool()
    tail = TailTool()
    jy = JsonYamlTool()
    nbr = NotebookReadTool()
    nbe = NotebookEditTool()
    tree = os.path.join(ROOT, "tree")
    big = os.path.join(ROOT, "big.txt")
    js = os.path.join(ROOT, "data.json")
    ym = os.path.join(ROOT, "data.yaml")
    nb = os.path.join(ROOT, "nb.ipynb")

    for it in range(15):
        rec(out, await find.execute(path=tree, name="*.py"))
        rec(out, await find.execute(path=tree, type="d"))
        rec(out, await find.execute(path=tree, type="f", extension=".md", maxdepth=3))
        rec(out, await find.execute(path=tree, type="f", size="+1k"))
        rec(out, await find.execute(path=tree, name="nomatch*"))
        rec(out, await find.execute(path="/nonexistent/kt2"))

        rec(out, await head.execute(file_path=big, lines=50 + it))
        rec(out, await tail.execute(file_path=big, lines=50 + it))
        rec(out, await head.execute(file_path="/nonexistent/kt2.txt"))
        rec(out, await tail.execute(file_path=tree))

        rec(out, await jy.execute(action="parse", source=js))
        rec(out, await jy.execute(action="parse", source=ym))
        rec(out, await jy.execute(action="query", source=js, query="$.users[*].name"))
        rec(out, await jy.execute(action="query", source='{"config": {"level": 3}}', format="json",
                                  query="$.config.level"))
        rec(out, await jy.execute(action="validate", source=ym))
        rec(out, await jy.execute(action="set", source=js, path="config.level",
                                  value=json.dumps({"lvl": it}), output_path=os.path.join(ROOT, "out.json")))
        rec(out, await jy.execute(action="bogus", source=js))
        rec(out, await jy.execute(action="query", source=js))

        make_notebook(nb)
        rec(out, await nbr.execute(path=nb))
        rec(out, await nbr.execute(path=nb, cell_types=["code"], cell_range="2-10",
                                   include_metadata=True))
        rec(out, await nbe.execute(path=nb, operation="add_cell", source="y = 1\nprint(y)"))
        rec(out, await nbe.execute(path=nb, operation="add_cell", source="# md",
                                   cell_type="markdown", cell_index=2))
        rec(out, await nbe.execute(path=nb, operation="update_cell", cell_index=1,
                                   source="z = 2"))
        rec(out, await nbe.execute(path=nb, operation="remove_cell", cell_index=0))
        rec(out, await nbe.execute(path=nb, operation="clear_outputs", backup=False))
        rec(out, await nbe.execute(path=nb, operation="set_metadata",
                                   metadata={"k": it}))
        rec(out, await nbe.execute(path=nb, operation="set_metadata", cell_index=3,
                                   metadata={"tag": "a"}))
        rec(out, await nbe.execute(path=nb, operation="remove_cell", cell_index=999))
        rec(out, await nbe.execute(path=nb, operation="weird"))
        rec(out, await nbr.execute(path=nb))

    for i, (s, o) in enumerate(out[:30]):
        print(i, s, len(o))
    print(hashlib.sha256(json.dumps(out).encode()).hexdigest())


asyncio.run(main())
