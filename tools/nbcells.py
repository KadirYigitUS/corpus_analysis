"""Tiny helpers for describing notebook cells (used by the chapter modules).

Markdown treats lines indented by 4+ spaces as a *code block*.  Multi-line values are therefore
never interpolated into an indented triple-quoted f-string (``dedent`` would find a zero common
margin and keep the indentation); lines are built flush-left and ``flush`` strips the margin.
"""

from textwrap import dedent

Cell = tuple[str, str]

LEARN_STYLE = ("border-left:4px solid #f59e0b;background:#fffbeb;padding:8px 12px;"
               "border-radius:0 8px 8px 0;margin:12px 0;")
SCHOLARLY_STYLE = ("border-left:4px solid #3b82f6;background:#eff6ff;padding:8px 12px;"
                   "border-radius:0 8px 8px 0;margin:12px 0;")


def flush(text: str) -> str:
    """Remove the common indentation and leading/trailing blank lines."""
    return dedent(text).strip("\n")


def md(text: str) -> Cell:
    return ("md", flush(text))


def code(text: str) -> Cell:
    return ("code", flush(text))


def chapter_header(number: int, title: str, minutes: int, objectives: list[str],
                   prerequisites: str, one_liner: str) -> Cell:
    lines = [
        "---",
        f"# Chapter {number} · {title}",
        f"⏱ ~{minutes} min · 📚 prerequisites: {prerequisites}",
        "",
        f"> {one_liner}",
        "",
        "**Learning objectives** — after this chapter you can:",
        "",  # blank line before the list so the bullets render as a list
        *[f"- {o}" for o in objectives],
    ]
    return ("md", "\n".join(lines))


def pitfalls(items: list[str]) -> Cell:
    lines = [
        f'<div class="learn" style="{LEARN_STYLE}">',
        "",
        "**⚠️ Common pitfalls**",
        "",
        *[f"- {i}" for i in items],
        "",
        "</div>",
    ]
    return ("md", "\n".join(lines))


def exercises(items: list[tuple[str, str]]) -> Cell:
    """items = [(question, solution_markdown_or_code)] → collapsible solutions."""
    parts = ["### ✏️ Exercises (try first, then open the solution)"]
    for i, (q, sol) in enumerate(items, 1):
        parts.append(f"**{i}.** {q}\n\n<details><summary>Show solution</summary>\n\n{flush(sol)}\n\n"
                     "</details>\n")
    return ("md", "\n".join(parts))


def scholarly(text: str) -> Cell:
    """Scholarly note connecting results to thesis methodology and literature."""
    lines = [
        f'<div class="scholarly" style="{SCHOLARLY_STYLE}">',
        "",
        "**🎓 Scholarly Note & Theoretical Grounding**",
        "",
        flush(text),
        "",
        "</div>",
    ]
    return ("md", "\n".join(lines))


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
    return ("md", "\n".join(lines))
