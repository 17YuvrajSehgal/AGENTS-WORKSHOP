"""Build the blind human-labelling sheets for the perf classifier check.

Sample (seed 42) from the 1,999 labelled pilot PRs, stratified by the
LLM's label:
  stratum A: LLM says runtime perf (primary or secondary + runtime) -> 150
  stratum B: everything else                                       -> 150
Each row keeps its stratum and inclusion weight (stratum size / sampled),
so precision, recall and population shares can be re-weighted.

Outputs (labels/human/):
  sheet_<annotator>.xlsx  one per annotator, same items, shuffled order per
                          annotator, NO LLM labels, drop-down answer cells
  key.csv                 item -> PR id, stratum, weight, LLM label (do not
                          give to annotators)

Usage: python -I analysis/p1_label_sheets.py A1 A2
"""

import random
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "labels" / "human"
SEED, PER_STRATUM = 42, 150
ROLES = ["primary", "secondary", "measurement_only", "none"]
SCOPES = ["runtime", "build_or_ci", "test_suite", "other", "not_applicable"]
CONF = ["high", "medium", "low"]


def main(annotators):
    OUT.mkdir(parents=True, exist_ok=True)
    lab = pd.read_parquet(ROOT / "data" / "p1_classify" / "pilot_labels_cc.parquet")
    lab = lab[lab["status"] == "ok"].copy()
    lab["stratum"] = "B"
    lab.loc[lab["perf_role"].isin(["primary", "secondary"])
            & (lab["perf_scope"] == "runtime"), "stratum"] = "A"
    inputs = pd.read_json(ROOT / "data" / "p1_classify" / "pilot_input.jsonl", lines=True)

    picked = []
    for s, g in lab.groupby("stratum"):
        ids = sorted(g["id"])
        chosen = random.Random(f"{SEED}-{s}").sample(ids, PER_STRATUM)
        picked.append(g[g["id"].isin(chosen)].assign(weight=len(g) / PER_STRATUM,
                                                      stratum_size=len(g)))
    items = pd.concat(picked).merge(inputs, on="id", suffixes=("_llm", ""))
    items = items.sort_values("id").reset_index(drop=True)
    items["item"] = [f"P{i:03d}" for i in range(1, len(items) + 1)]

    items[["item", "id", "html_url", "agent", "stratum", "stratum_size", "weight",
           "perf_role", "perf_scope", "confidence", "evidence_quote"]].rename(
        columns={"perf_role": "llm_role", "perf_scope": "llm_scope",
                 "confidence": "llm_confidence", "evidence_quote": "llm_quote"}
    ).to_csv(OUT / "key.csv", index=False, encoding="utf-8")

    replaced = set()
    for k, name in enumerate(annotators):
        order = items.sample(frac=1, random_state=SEED + 1 + k)
        wb = Workbook()
        ws = wb.active
        ws.title = "label"
        head = ["item", "pr_link", "title", "description", "commit_messages",
                "changed_files", "perf_role", "perf_scope", "evidence_quote",
                "confidence", "notes"]
        ws.append(head)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in order.itertuples():
            files = "\n".join(r.files) + (f"\n... and {r.n_files - len(r.files)} more"
                                          if r.n_files > len(r.files) else "")
            cells = [r.item, r.html_url, r.title, r.body or "(empty)",
                     r.commit_msgs or "(none)", files or "(no file list)"]
            # Excel rejects control characters; show them as a visible marker
            for i, v in enumerate(cells):
                if isinstance(v, str) and ILLEGAL_CHARACTERS_RE.search(v):
                    cells[i] = ILLEGAL_CHARACTERS_RE.sub("□", v)
                    replaced.add((r.item, head[i]))
            ws.append(cells + [None] * 5)
        n = len(order) + 1
        for col, opts in (("G", ROLES), ("H", SCOPES), ("J", CONF)):
            dv = DataValidation(type="list", formula1='"' + ",".join(opts) + '"',
                                allow_blank=False)
            ws.add_data_validation(dv)
            dv.add(f"{col}2:{col}{n}")
        widths = {"A": 7, "B": 30, "C": 40, "D": 80, "E": 60, "F": 40,
                  "G": 16, "H": 16, "I": 40, "J": 12, "K": 30}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "C2"
        wb.save(OUT / f"sheet_{name}.xlsx")

    print(items.groupby("stratum").agg(n=("id", "size"),
                                       stratum_size=("stratum_size", "first"),
                                       weight=("weight", "first")))
    print("by agent:", items["agent"].value_counts().to_dict())
    print("cells with control characters shown as a box marker:", sorted(replaced))


if __name__ == "__main__":
    main(sys.argv[1:] or ["A1", "A2"])
