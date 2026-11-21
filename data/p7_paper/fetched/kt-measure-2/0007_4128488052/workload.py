import hashlib
import os

os.environ.setdefault("DO_NOT_TRACK", "1")
_HOME = "/tmp/kt_784/home"
os.makedirs(_HOME, exist_ok=True)
os.environ["HOME"] = _HOME

from pipelex.core.interpreter.interpreter import PipelexInterpreter  # noqa: E402
from pipelex.hub import get_library_manager, set_current_library  # noqa: E402
from pipelex.pipelex import Pipelex  # noqa: E402
from pipelex.system.runtime import IntegrationMode  # noqa: E402

N_DOMAINS = 12
N_CONCEPTS = 10
N_PIPES = 8
REPEATS = 6


def make_bundle(d: int) -> str:
    dom = f"dom{d}"
    lines = [f'domain = "{dom}"', f'description = "Synthetic domain {d}"', f'main_pipe = "seq_{dom}"', ""]
    # Concepts declared in reverse order so topo sorting matters
    for c in reversed(range(N_CONCEPTS)):
        lines.append(f"[concept.Thing{c}]")
        lines.append(f'description = "Concept {c} of {dom}"')
        if c == 0:
            if d > 0:
                lines.append(f'refines = "dom{d - 1}.Thing0"')
            else:
                lines.append("")
                lines.append("[concept.Thing0.structure]")
                lines.append('name = { type = "text", required = true, description = "Name" }')
                lines.append('score = { type = "integer", required = false, description = "Score" }')
        elif c % 3 == 0:
            lines.append('refines = "Text"')
        else:
            lines.append(f'refines = "{dom}.Thing{c - 1}"')
        lines.append("")
    lines.append(f'[concept]\nNote{dom} = "A plain string concept"\n')
    for p in range(N_PIPES):
        lines.append(f"[pipe.llm_{dom}_{p}]")
        lines.append('type = "PipeLLM"')
        lines.append(f'description = "LLM pipe {p}"')
        lines.append(f'inputs = {{ item = "Thing{p % N_CONCEPTS}" }}')
        lines.append('output = "Text"')
        lines.append(f'prompt = "Process this @item for step {p}"')
        lines.append("")
    steps = ", ".join(
        f'{{ pipe = "llm_{dom}_{p}", result = "r{p}" }}' for p in range(1)
    )
    lines.append(f"[pipe.seq_{dom}]")
    lines.append('type = "PipeSequence"')
    lines.append('description = "Sequence"')
    lines.append('inputs = { item = "Thing0" }')
    lines.append('output = "Text"')
    lines.append(f"steps = [{steps}]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    Pipelex.make(integration_mode=IntegrationMode.CI, needs_inference=False)
    lm = get_library_manager()
    contents = [make_bundle(d) for d in range(N_DOMAINS)]
    blueprints = [PipelexInterpreter.make_pipelex_bundle_blueprint(mthds_content=c) for c in contents]

    h = hashlib.sha256()
    for _ in range(REPEATS):
        library_id, _lib = lm.open_library()
        set_current_library(library_id=library_id)
        pipes = lm.load_from_blueprints(library_id=library_id, blueprints=blueprints)
        lib = lm.get_library(library_id=library_id)
        refs = sorted(f"{p.domain_code}.{p.code}:{type(p).__name__}:{p.output}" for p in pipes)
        h.update("|".join(refs).encode())
        concepts = sorted(
            f"{c.concept_ref}<{','.join(sorted(c.refines or [])) if isinstance(c.refines, list) else c.refines}"
            for c in lib.concept_library.root.values()
        )
        h.update("|".join(concepts).encode())
        doms = sorted(lib.domain_library.root.keys())
        h.update("|".join(doms).encode())
        # Remove one bundle (exercises _remove_pipes_from_blueprint)
        lm._remove_from_blueprint(library_id=library_id, blueprint=blueprints[-1])
        h.update(str(len(lib.pipe_library.root)).encode())
        lm.teardown(library_id=library_id)
    print(len(refs), len(concepts), len(doms))
    Pipelex.teardown_if_needed()
    print(h.hexdigest())


if __name__ == "__main__":
    main()
