# smda #84 "Cache label provider capability lists in IntelDisassembler".
# Pilot workload (hand-written, experimenter has read the PR): disassemble
# /usr/bin/bash (ELF, x86-64) with SMDA. Last line = SHA-256 over the
# recovered function addresses and their API/symbol labels (the report's
# timing fields are left out because they depend on run time, not code).
import hashlib
import json

from smda.Disassembler import Disassembler

report = Disassembler().disassembleFile("/usr/bin/bash")
d = report.toDict()
funcs = d["xcfg"]
summary = sorted((int(k), v.get("metadata", {}).get("function_name", ""),
                  len(v.get("apirefs", {}) or {})) for k, v in funcs.items())
print(len(summary))
print(hashlib.sha256(json.dumps(summary).encode()).hexdigest())
