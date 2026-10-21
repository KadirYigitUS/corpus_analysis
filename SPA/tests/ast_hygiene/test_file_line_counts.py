"""AST and line count hygiene test enforcing <= 200 lines per file."""

from pathlib import Path


def test_spa_file_line_counts():
    """Verify that every source file in SPA respects <= 200 physical lines."""
    spa_dir = Path(__file__).resolve().parent.parent.parent
    violations = []
    checked = 0

    for ext in ("*.py", "*.js", "*.css", "*.html"):
        for file_path in spa_dir.rglob(ext):
            rel = str(file_path.relative_to(spa_dir))
            if rel.startswith("tests/results/"):
                continue
            checked += 1
            lines = len(file_path.read_text(encoding="utf-8").splitlines())
            if lines > 200:
                violations.append((rel, lines))

    assert checked > 30, f"Expected >30 files checked, found {checked}"
    assert not violations, (
        f"Files exceeding 200 lines hard limit: {violations}"
    )
