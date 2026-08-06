"""
Module 7 — CSS Tokenizer & Parser
====================================
Proves: a stylesheet string becomes a structured list of Rule objects —
each with a parsed selector list and a parsed declaration list — with no
`tinycss`/`cssutils` import.

Deliberately does NOT compute specificity or decide which rule wins a
conflict — that's the cascade's job (Module 9), a genuinely separate
concern from parsing (see Module 0's DECISIONS.md §4). This module only
answers "what does the stylesheet text say," never "which rule wins."
"""

WHITESPACE = " \t\n\r\f"


class SimpleSelector:
    """One compound selector, e.g. `div.card#main` -> type='div', id='main', classes=['card']."""

    def __init__(self, type_name=None, id=None, classes=None):
        self.type_name = type_name   # None = no tag constraint (matches any tag)
        self.id = id                  # None = no id constraint
        self.classes = classes or []  # [] = no class constraints

    def __repr__(self):
        t = self.type_name or "*"
        i = f"#{self.id}" if self.id else ""
        c = "".join(f".{c}" for c in self.classes)
        return f"{t}{i}{c}"


class Selector:
    """A sequence of SimpleSelectors combined by the descendant combinator
    (whitespace) only — `nav a.active` means "an <a class=active> that is
    a descendant, at any depth, of a <nav>". See DECISIONS.md for why
    child (>), sibling (+, ~) combinators are out of scope."""

    def __init__(self, parts):
        self.parts = parts   # left = ancestor ... right = the element itself

    def __repr__(self):
        return " ".join(repr(p) for p in self.parts)


class Declaration:
    def __init__(self, property, value, important=False):
        self.property = property
        self.value = value
        self.important = important

    def __repr__(self):
        bang = " !important" if self.important else ""
        return f"{self.property}: {self.value}{bang}"


class Rule:
    def __init__(self, selectors, declarations):
        self.selectors = selectors        # list[Selector] — comma-separated group
        self.declarations = declarations  # list[Declaration]

    def __repr__(self):
        sels = ", ".join(repr(s) for s in self.selectors)
        return f"Rule({sels} {{ {len(self.declarations)} declarations }})"


# --------------------------------------------------------------- tokenizing


def strip_comments(css: str) -> str:
    """Remove /* ... */ comments. CSS comments don't nest, so a simple
    find-the-next-`*/`  loop is sufficient — unlike HTML tags (Module 5),
    there's no equivalent to RAWTEXT content to worry about here."""
    out = []
    i, n = 0, len(css)
    while i < n:
        if css[i:i + 2] == "/*":
            end = css.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            out.append(css[i])
            i += 1
    return "".join(out)


def _skip_block(css: str, open_brace_idx: int) -> int:
    """Given the index of a '{', return the index just past its matching
    '}', counting nested braces. Used to skip @media/@font-face/etc.
    blocks whole, without parsing their contents — see DECISIONS.md."""
    depth = 0
    i = open_brace_idx
    n = len(css)
    while i < n:
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def parse_stylesheet(css: str) -> list[Rule]:
    """Top-level parse: strip comments, then repeatedly find
    'selector-text { declarations }' blocks. Selector text before '{' is
    only ever expected to contain selectors, not more '{' — real CSS's
    at-rules (@media, @font-face, ...) are the exception, handled by
    detecting the leading '@' and skipping the whole block unparsed."""
    css = strip_comments(css)
    rules: list[Rule] = []
    i, n = 0, len(css)

    while i < n:
        while i < n and css[i] in WHITESPACE:
            i += 1
        if i >= n:
            break

        brace_idx = css.find("{", i)
        if brace_idx == -1:
            break   # trailing junk after the last rule; ignore

        header = css[i:brace_idx].strip()

        if header.startswith("@"):
            i = _skip_block(css, brace_idx)   # explicit scope-out: at-rules unsupported
            continue

        close_idx = css.find("}", brace_idx)
        if close_idx == -1:
            break

        body = css[brace_idx + 1:close_idx]
        selectors = [parse_selector(s) for s in header.split(",") if s.strip()]
        declarations = parse_declarations(body)
        if selectors:
            rules.append(Rule(selectors, declarations))
        i = close_idx + 1

    return rules


def parse_selector(text: str) -> Selector:
    tokens = text.split()   # any run of whitespace = one descendant combinator
    return Selector([_parse_compound(t) for t in tokens])


def _parse_compound(token: str) -> SimpleSelector:
    type_name, id_, classes = None, None, []
    i, n = 0, len(token)

    if i < n and token[i] not in ".#":
        start = i
        while i < n and token[i] not in ".#":
            i += 1
        name = token[start:i]
        type_name = None if name == "*" else name   # '*' = no constraint

    while i < n:
        marker = token[i]
        i += 1
        start = i
        while i < n and token[i] not in ".#":
            i += 1
        piece = token[start:i]
        if marker == ".":
            classes.append(piece)
        elif marker == "#":
            id_ = piece

    return SimpleSelector(type_name, id_, classes)


def parse_declarations(text: str) -> list[Declaration]:
    declarations = []
    for part in text.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        prop, _, value = part.partition(":")
        prop = prop.strip().lower()
        value = value.strip()
        important = False
        if value.lower().endswith("!important"):
            value = value[:-len("!important")].strip()
            important = True
        declarations.append(Declaration(prop, value, important))
    return declarations


if __name__ == "__main__":
    sample = """
    /* base styles */
    * { margin: 0; padding: 0; }

    body {
      font-family: sans-serif;
      color: #333;
    }

    .card, .panel {
      border: 1px solid #ccc;
      padding: 10px !important;
    }

    nav a.active {
      color: red;
    }

    #main-header {
      font-size: 24px;
    }

    @media (max-width: 600px) {
      body { font-size: 14px; }
    }

    h1, h2 {
      font-weight: bold;
    }
    """

    rules = parse_stylesheet(sample)
    print(f"Parsed {len(rules)} rules (the @media block should be SKIPPED, not counted):\n")
    for r in rules:
        print(f"  {r}")
        for sel in r.selectors:
            print(f"      selector parts: {sel.parts!r}")
        for d in r.declarations:
            print(f"      {d}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"6 real rules parsed, @media skipped entirely: {len(rules) == 6}")

    card_rule = next(r for r in rules if any("card" in s.parts[0].classes for s in r.selectors))
    padding_decl = next(d for d in card_rule.declarations if d.property == "padding")
    print(f"'.card, .panel' has 2 comma-separated selectors: {len(card_rule.selectors) == 2}")
    print(f"padding declaration correctly marked !important, value cleaned to '10px': "
          f"{padding_decl.important and padding_decl.value == '10px'}")

    nav_rule = next(r for r in rules if r.selectors[0].parts[0].type_name == "nav")
    nav_sel = nav_rule.selectors[0]
    print(f"'nav a.active' parsed as 2-part descendant selector "
          f"(nav, then a.active): {len(nav_sel.parts) == 2 and nav_sel.parts[1].classes == ['active']}")

    id_rule = next(r for r in rules if r.selectors[0].parts[0].id == "main-header")
    print(f"'#main-header' parsed with id constraint, no type constraint: "
          f"{id_rule.selectors[0].parts[0].type_name is None}")

    star_rule = rules[0]
    print(f"'*' (universal) parsed with type_name=None (no constraint): "
          f"{star_rule.selectors[0].parts[0].type_name is None}")
