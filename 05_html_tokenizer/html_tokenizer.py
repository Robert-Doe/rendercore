"""
Module 5 — HTML Tokenizer
============================
Proves: a state machine can turn a raw HTML string into a stream of typed
tokens (start tag, end tag, text, comment) — including the two cases that
break a naive "split on < and >" approach: comments containing fake tags,
and <script>/<style> content that must NOT be tokenized as markup even
though it's full of < and > characters.

Explicitly out of scope (see DECISIONS.md): character reference (entity)
decoding (&amp; stays literal), full DOCTYPE parsing, and CDATA sections.
"""

from dataclasses import dataclass, field


@dataclass
class StartTag:
    name: str
    attrs: dict = field(default_factory=dict)
    self_closing: bool = False


@dataclass
class EndTag:
    name: str


@dataclass
class Text:
    data: str


@dataclass
class Comment:
    data: str


Token = StartTag | EndTag | Text | Comment

# Elements whose content is NOT markup — read as plain text until the
# matching end tag. Real HTML has more of these (textarea, title, etc.);
# we scope to the two that matter for a browser engine: script and style.
RAWTEXT_ELEMENTS = {"script", "style"}

WHITESPACE = " \t\n\r\f"


class HTMLTokenizer:
    """A hand-rolled state machine. `state` is always one of "DATA" or
    "RAWTEXT" at the top level — see prereqs/state_machines.html. The
    finer-grained states inside a tag (attribute name, attribute value,
    etc.) are handled by small dedicated methods rather than more top-level
    state names, purely to keep this teaching version readable; a
    spec-accurate tokenizer (WHATWG HTML §13.2.5) names every one of them
    explicitly as its own state.
    """

    def __init__(self, html: str):
        self.html = html
        self.pos = 0
        self.length = len(html)
        self.tokens: list[Token] = []
        self.state = "DATA"
        self.text_buffer: list[str] = []
        self.rawtext_tag_name = None

    def peek(self):
        return self.html[self.pos] if self.pos < self.length else None

    def advance(self) -> str:
        ch = self.html[self.pos]
        self.pos += 1
        return ch

    def _emit_text_if_any(self):
        if self.text_buffer:
            self.tokens.append(Text("".join(self.text_buffer)))
            self.text_buffer = []

    def run(self) -> list[Token]:
        while self.pos < self.length:
            if self.state == "DATA":
                self._step_data()
            elif self.state == "RAWTEXT":
                self._step_rawtext()
            else:
                raise AssertionError(f"unreachable tokenizer state {self.state!r}")
        self._emit_text_if_any()
        return self.tokens

    # ---------------------------------------------------------------- DATA

    def _step_data(self):
        ch = self.advance()
        if ch == "<":
            self._consume_markup()
        else:
            self.text_buffer.append(ch)

    def _consume_markup(self):
        """Called immediately after consuming '<'. Decides what kind of
        markup construct is starting, or falls back to treating '<' as a
        literal character if nothing recognizable follows it — real HTML
        is full of unescaped '<' in text, and a browser must not choke on
        it."""
        nxt = self.peek()
        if nxt == "!":
            self.advance()
            self._emit_text_if_any()
            if self.html[self.pos:self.pos + 2] == "--":
                self.pos += 2
                self._consume_comment()
            else:
                self._consume_bogus_declaration()   # e.g. <!DOCTYPE html>
            return
        if nxt == "/":
            self.advance()
            self._emit_text_if_any()
            self._consume_end_tag()
            return
        if nxt is not None and nxt.isalpha():
            self._emit_text_if_any()
            self._consume_start_tag()
            return
        # '<' not followed by anything tag-like: it's just a literal '<'
        self.text_buffer.append("<")

    def _consume_name(self) -> str:
        start = self.pos
        while self.peek() is not None and (self.peek().isalnum() or self.peek() in "-_:"):
            self.advance()
        return self.html[start:self.pos]

    def _skip_whitespace(self):
        while self.peek() is not None and self.peek() in WHITESPACE:
            self.advance()

    def _consume_start_tag(self):
        name = self._consume_name().lower()
        attrs: dict[str, str] = {}
        self_closing = False
        while True:
            self._skip_whitespace()
            ch = self.peek()
            if ch is None:
                break                          # truncated input; stop gracefully
            if ch == "/":
                self.advance()
                self._skip_whitespace()
                if self.peek() == ">":
                    self.advance()
                    self_closing = True
                break
            if ch == ">":
                self.advance()
                break
            attr_name = self._consume_attr_name()
            if not attr_name:                   # stray char we can't use as a name; skip it
                self.advance()
                continue
            self._skip_whitespace()
            if self.peek() == "=":
                self.advance()
                self._skip_whitespace()
                value = self._consume_attr_value()
            else:
                value = ""
            attrs[attr_name.lower()] = value

        self.tokens.append(StartTag(name, attrs, self_closing))
        if name in RAWTEXT_ELEMENTS and not self_closing:
            self.rawtext_tag_name = name
            self.state = "RAWTEXT"

    def _consume_attr_name(self) -> str:
        start = self.pos
        while self.peek() is not None and self.peek() not in WHITESPACE + "=/>":
            self.advance()
        return self.html[start:self.pos]

    def _consume_attr_value(self) -> str:
        ch = self.peek()
        if ch in ('"', "'"):
            quote = self.advance()
            start = self.pos
            while self.peek() is not None and self.peek() != quote:
                self.advance()
            value = self.html[start:self.pos]
            if self.peek() == quote:
                self.advance()
            return value
        start = self.pos
        while self.peek() is not None and self.peek() not in WHITESPACE + ">":
            self.advance()
        return self.html[start:self.pos]

    def _consume_end_tag(self):
        name = self._consume_name().lower()
        self._skip_whitespace()
        if self.peek() == ">":
            self.advance()
        self.tokens.append(EndTag(name))

    def _consume_comment(self):
        start = self.pos
        end = self.html.find("-->", self.pos)
        if end == -1:
            self.tokens.append(Comment(self.html[start:]))
            self.pos = self.length
        else:
            self.tokens.append(Comment(self.html[start:end]))
            self.pos = end + 3

    def _consume_bogus_declaration(self):
        """DOCTYPE and any other <!...> construct we don't model in
        detail: skip straight to the next '>'. See DECISIONS.md."""
        end = self.html.find(">", self.pos)
        self.pos = self.length if end == -1 else end + 1

    # ------------------------------------------------------------- RAWTEXT

    def _step_rawtext(self):
        """Scan forward for the matching '</tagname', treating everything
        before it as one literal Text token — this is what stops
        `if (x < 10)` inside a <script> block from being misread as the
        start of a tag."""
        end_marker = f"</{self.rawtext_tag_name}"
        idx = self.html.lower().find(end_marker, self.pos)
        if idx == -1:
            data, self.pos = self.html[self.pos:], self.length
        else:
            data, self.pos = self.html[self.pos:idx], idx
        if data:
            self.tokens.append(Text(data))
        self.state = "DATA"   # the end tag itself is now re-processed normally


def tokenize(html: str) -> list[Token]:
    return HTMLTokenizer(html).run()


if __name__ == "__main__":
    sample = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body class="main" data-x=1 disabled>
  <p>Hello, <b>World</b>!</p>
  <img src="a.png" />
  <!-- a comment with <fake> tags inside, ignored -->
  <script>
    if (x < 10) { console.log("a < b"); }
  </script>
</body>
</html>"""

    tokens = tokenize(sample)
    print(f"Produced {len(tokens)} tokens:\n")
    for i, t in enumerate(tokens):
        print(f"  [{i:2}] {t}")

    # ---- checks against the two things this module exists to prove ----
    script_texts = [t.data for t in tokens if isinstance(t, Text) and "x < 10" in t.data]
    comment_texts = [t.data for t in tokens if isinstance(t, Comment) and "<fake>" in t.data]
    fake_start_tags = [t for t in tokens if isinstance(t, StartTag) and t.name == "fake"]
    img_tags = [t for t in tokens if isinstance(t, StartTag) and t.name == "img"]

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"script content captured as one Text token containing 'x < 10': "
          f"{len(script_texts) == 1}")
    print(f"comment's embedded '<fake>' captured as Comment text, not a tag: "
          f"{len(comment_texts) == 1 and len(fake_start_tags) == 0}")
    print(f"self-closing <img> parsed with self_closing=True and src attr: "
          f"{len(img_tags) == 1 and img_tags[0].self_closing and img_tags[0].attrs.get('src') == 'a.png'}")

    # Regression check for a real bug caught during development: text
    # immediately before a CLOSING tag must be emitted BEFORE that end
    # tag's token, not after it (see DECISIONS.md). Find the <title> run.
    title_idx = next(i for i, t in enumerate(tokens) if isinstance(t, StartTag) and t.name == "title")
    ordering_ok = (
        isinstance(tokens[title_idx + 1], Text) and
        tokens[title_idx + 1].data == "Test Page" and
        isinstance(tokens[title_idx + 2], EndTag) and
        tokens[title_idx + 2].name == "title"
    )
    print(f"text before </title> ordered BEFORE the end tag, not after: {ordering_ok}")
