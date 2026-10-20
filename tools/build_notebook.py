"""Assemble ``Corpus_Analysis.ipynb`` from the chapter modules.

Usage:  python tools/build_notebook.py [--execute]

``--execute`` runs the notebook headlessly (nbclient) and stores outputs, which is also the
repository's acceptance test for the notebook.
"""

import argparse
import os
import sys
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import nb_part_a  # noqa: E402
import nb_part_b  # noqa: E402
import nb_part_c  # noqa: E402

ROOT = HERE.parent
NOTEBOOK = ROOT / "Corpus_Analysis.ipynb"


def build() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    cells = nb_part_a.chapters() + nb_part_b.chapters() + nb_part_c.chapters()
    nb.cells = [nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src)
                for kind, src in cells]
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python",
                                 "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    return nb


def execute(nb: nbf.NotebookNode, timeout: int = 1800, allow_errors: bool = False
            ) -> nbf.NotebookNode:
    from nbclient import NotebookClient

    os.environ.setdefault("CORPUS_CACHE_POLICY", "keep")
    os.environ.setdefault("MPLBACKEND", "Agg")
    NotebookClient(nb, timeout=timeout, kernel_name="python3", allow_errors=allow_errors,
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    return nb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="execute headlessly and save outputs")
    ap.add_argument("--out", default=None,
                    help="target path (defaults to executed_Corpus_Analysis.ipynb if --execute, else Corpus_Analysis.ipynb)")
    ap.add_argument("--allow-errors", action="store_true",
                    help="continue after a failing cell and list all failures")
    args = ap.parse_args()
    target_out = args.out or (str(ROOT / "executed_Corpus_Analysis.ipynb") if args.execute else str(NOTEBOOK))
    nb = build()
    if args.execute:
        nb = execute(nb, allow_errors=args.allow_errors)

        failed = [i for i, c in enumerate(nb.cells) if c.cell_type == "code" and any(
            o.get("output_type") == "error" for o in c.get("outputs", []))]
        for i in failed:
            err = next(o for o in nb.cells[i].outputs if o.output_type == "error")
            print(f"❌ cell {i}: {err.ename}: {err.evalue}\n   source: {nb.cells[i].source[:140]!r}")
        print(f"{len(failed)} failing code cell(s)")
    nbf.write(nb, target_out)
    print(f"wrote {target_out} ({len(nb.cells)} cells, executed={args.execute})")



if __name__ == "__main__":
    main()
