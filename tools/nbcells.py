"""Tiny helpers for describing notebook cells (used by the chapter modules)."""

from textwrap import dedent

Cell = tuple[str, str]


def md(text: str) -> Cell:
    return ("md", dedent(text).strip("\n"))


def code(text: str) -> Cell:
    return ("code", dedent(text).strip("\n"))


def chapter_header(number: int, title: str, minutes: int, objectives: list[str],
                   prerequisites: str, one_liner: str) -> Cell:
    obj = "\n".join(f"- {o}" for o in objectives)
    return md(f"""
    ---
    # Chapter {number} · {title}
    ⏱ ~{minutes} min · 📚 prerequisites: {prerequisites}

    > {one_liner}

    **Learning objectives** — after this chapter you can:
    {obj}
    """)


def pitfalls(items: list[str]) -> Cell:
    body = "\n".join(f"- {i}" for i in items)
    return md(f"""
    <div class="learn" style="border-left:4px solid #f59e0b;background:#fffbeb;padding:8px 12px;border-radius:0 8px 8px 0">

    **⚠️ Common pitfalls**
    {body}

    </div>
    """)


def exercises(items: list[tuple[str, str]]) -> Cell:
    """items = [(question, solution_markdown_or_code)] → collapsible solutions."""
    parts = ["### ✏️ Exercises (try first, then open the solution)"]
    for i, (q, sol) in enumerate(items, 1):
        parts.append(f"**{i}.** {q}\n\n<details><summary>Show solution</summary>\n\n{sol}\n\n"
                     "</details>\n")
    return md("\n".join(parts))


def scholarly(text: str) -> Cell:
    """Scholarly note connecting results to thesis methodology and literature."""
    return md(f"""
    <div class="scholarly" style="border-left:4px solid #3b82f6;background:#eff6ff;padding:8px 12px;border-radius:0 8px 8px 0;margin:12px 0;">

    **🎓 Scholarly Note & Theoretical Grounding**

    {text.strip()}

    </div>
    """)


def cheat_sheet(title: str, rows: list[tuple[str, str, str]]) -> Cell:
    """Generate a clean Markdown table of commands/methods, arguments, and examples."""
    lines = [
        f"### 📋 Command Cheat-Sheet · {title}",
        "",
        "| Method / Function | Parameters & Options | Example Call |",
        "| :--- | :--- | :--- |",
    ]
    for fn, params, eg in rows:
        lines.append(f"| `{fn}` | {params} | `{eg}` |")
    return md("\n".join(lines))

