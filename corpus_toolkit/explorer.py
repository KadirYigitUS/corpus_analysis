"""Interactive explorer (Chapter 13): the whole toolkit behind one ipywidgets panel.

If ``ipywidgets`` is unavailable (or in a headless run) use :func:`quick_search`, a plain
function with the same options — every widget maps to a keyword argument, so the panel is a
visual cheat-sheet for the Python API.
"""

from typing import Any

from .collocation import collocates
from .kwic import SPAN_PRESETS, Concordancer
from .loader import CorpusLoader
from .render import show
from .search import CorpusSearchEngine, SearchQuery
from .tokenview import TokenView

CATEGORIES = {
    "All texts": "load_all",
    "All English texts": "load_all_english",
    "All Turkish texts": "load_all_turkish",
    "Indigenous Turkish novels": "load_indigenous",
    "Author-translator related texts": "load_author_related",
    "Author-translator Turkish texts": "load_author_turkish",
}


def _select_texts(loader: CorpusLoader, category: str, author: str | None) -> list[Any]:
    method = getattr(loader, CATEGORIES[category])
    if category in {"Author-translator related texts", "Author-translator Turkish texts",
                    "Indigenous Turkish novels"}:
        return list(method(author))
    return list(method())


def quick_search(loader: CorpusLoader, terms: "str | list[str]", category: str = "All texts",
                 author: str | None = None, field: str = "lem", match: str = "exact",
                 pos: set[str] | None = None, collocate: list[str] | None = None,
                 filter_function_words: bool = False, mode: str = "drop",
                 span: "int | tuple[int, int] | str" = "collocation", view: str = "kwic",
                 max_lines: int = 25, case_sensitive: bool = False) -> Any:
    """One call = search + concordance + display.  Returns the :class:`ConcordanceResult`."""
    texts = _select_texts(loader, category, author)
    q = SearchQuery([terms] if isinstance(terms, str) else list(terms), field,  # type: ignore[arg-type]
                    match, case_sensitive, pos, collocate,  # type: ignore[arg-type]
                    filter_function_words=filter_function_words, mode=mode)  # type: ignore[arg-type]
    result = CorpusSearchEngine().search(q, texts)
    conc = Concordancer().run(result, texts, span=span)
    try:
        from IPython.display import display

        display(result.summary())
    except ImportError:  # pragma: no cover
        print(result.summary().to_string())
    show(conc, view=view, loader=loader, max_lines=max_lines)
    return conc


class CorpusExplorerUI:
    """Widget panel: choose corpus → set options → search / concordance / collocates."""

    def __init__(self, loader: CorpusLoader) -> None:
        import ipywidgets as w

        self.loader = loader
        reg = loader.registry
        authors = [("All author-translators", "")] + [(f"{n} ({c})", c)
                                                      for c, n in reg.author_names.items()]
        self.w = w
        self.category = w.Dropdown(options=list(CATEGORIES), description="Corpus")
        self.author = w.Dropdown(options=authors, description="Author")
        self.terms = w.Text(value="robot", description="Words", placeholder="comma separated")
        self.field = w.ToggleButtons(options=[("Lemma", "lem"), ("Token", "tok")],
                                     description="Field")
        self.match = w.Dropdown(options=["exact", "glob", "regex"], description="Match")
        self.fw = w.Checkbox(value=False, description="Hide function words (content view)")
        self.mode = w.Dropdown(options=["drop", "mask"], description="Span mode")
        self.span = w.Dropdown(options=[*SPAN_PRESETS, "sentence"], value="collocation",
                               description="Span")
        self.left = w.BoundedIntText(value=5, min=0, max=20, description="Left")
        self.right = w.BoundedIntText(value=5, min=0, max=20, description="Right")
        self.custom = w.Checkbox(value=False, description="Use custom Left/Right")
        self.view = w.ToggleButtons(options=["kwic", "chips", "cards", "console"],
                                    description="View")
        self.pos = w.SelectMultiple(options=["NOUN", "VERB", "ADJ", "ADV", "PROPN"],
                                    description="UPOS", rows=5)
        self.colloc = w.Text(description="Needs word", placeholder="optional context word")
        self.out = w.Output()
        run = w.Button(description="Search & concordance", button_style="primary",
                       icon="search")
        coll = w.Button(description="Collocates", icon="share-alt")
        run.on_click(lambda _: self._run())
        coll.on_click(lambda _: self._collocates())
        top = w.HBox([w.VBox([self.category, self.author, self.terms, self.field, self.match]),
                      w.VBox([self.fw, self.mode, self.span, self.custom, self.left, self.right]),
                      w.VBox([self.pos, self.colloc, self.view])])
        self.panel = w.VBox([top, w.HBox([run, coll]), self.out])

    def _query(self) -> SearchQuery:
        terms = [t.strip() for t in self.terms.value.split(",") if t.strip()]
        return SearchQuery(terms, self.field.value, self.match.value,  # type: ignore[arg-type]
                           pos=set(self.pos.value) or None,
                           collocate=[c.strip() for c in self.colloc.value.split(",") if c.strip()]
                           or None, filter_function_words=self.fw.value,
                           mode=self.mode.value)  # type: ignore[arg-type]

    def _texts(self) -> list[Any]:
        return _select_texts(self.loader, self.category.value, self.author.value or None)

    def _run(self) -> None:
        with self.out:
            self.out.clear_output()
            texts = self._texts()
            result = CorpusSearchEngine().search(self._query(), texts)
            span = (self.left.value, self.right.value) if self.custom.value else self.span.value
            conc = Concordancer().run(result, texts, span=span)
            from IPython.display import display

            display(result.summary())
            show(conc, self.view.value, self.loader, 30)

    def _collocates(self) -> None:
        with self.out:
            self.out.clear_output()
            q = self._query()
            for t in self._texts():
                view = TokenView(t, q.field, q.filter_function_words, q.mode)
                table = collocates(view, q.terms, self.left.value, self.right.value)
                from IPython.display import display

                print(f"— {t.record.title} ({self.loader.registry.display(t.record)})")
                display(table.head(10).round(2))
                t.evict()

    def show(self) -> None:
        from IPython.display import display

        display(self.panel)
