"""
Module 9 — The Cascade
=========================
Proves: given several matching, CONFLICTING rules for the same element
and property, this module picks exactly one final value — deterministically
— using specificity, source order, and !important, in the correct
precedence order. Also implements inheritance (a computed value flowing
from parent to child for certain properties) and fallback to an initial
value when nothing set a property at all.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "07_css_parser"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "08_selector_matching"))
from dom_tree_builder import parse_html, Element                          # noqa: E402
from css_parser import parse_stylesheet, Selector                          # noqa: E402
from selector_matching import matches_selector, walk                       # noqa: E402

# A small, deliberately incomplete subset of real CSS's inheritance table —
# enough to demonstrate the mechanism honestly. See DECISIONS.md.
INHERITED_PROPERTIES = {"color", "font-family", "font-size", "font-weight", "line-height", "text-align"}

# Likewise a small initial-value table — real CSS defines one for every
# property; we only define what our test cases exercise.
INITIAL_VALUES = {
    "color": "black",
    "font-weight": "normal",
    "font-size": "16px",
    "display": "inline",
}


def specificity(selector: Selector) -> tuple:
    """(id count, class count, type count) — compared as a tuple, so an id
    always outweighs any number of classes, and a class always outweighs
    any number of type selectors, exactly like the real CSS spec defines."""
    ids = sum(1 for p in selector.parts if p.id)
    classes = sum(len(p.classes) for p in selector.parts)
    types = sum(1 for p in selector.parts if p.type_name)
    return (ids, classes, types)


def compute_style(node: Element, rules: list, parent_style: dict | None = None) -> dict:
    """The cascade for one node: gather every candidate value per property
    from every matching rule, then resolve conflicts, then apply
    inheritance, then fall back to initial values."""
    candidates: dict[str, list] = {}

    for order_idx, rule in enumerate(rules):
        matched = [s for s in rule.selectors if matches_selector(node, s)]
        if not matched:
            continue
        spec = max(specificity(s) for s in matched)   # best-matching selector in the comma group
        for decl in rule.declarations:
            candidates.setdefault(decl.property, []).append(
                (spec, order_idx, decl.important, decl.value)
            )

    computed: dict[str, str] = {}
    for prop, cands in candidates.items():
        important_cands = [c for c in cands if c[2]]
        pool = important_cands if important_cands else cands
        # max() over (specificity, source_order) — Python compares tuples
        # lexicographically, so specificity always dominates order, and
        # order only breaks a TIE in specificity. That single line IS the
        # cascade's tie-breaking rule.
        best = max(pool, key=lambda c: (c[0], c[1]))
        computed[prop] = best[3]

    if parent_style:
        for prop in INHERITED_PROPERTIES:
            if prop not in computed and prop in parent_style:
                computed[prop] = parent_style[prop]

    for prop, initial in INITIAL_VALUES.items():
        computed.setdefault(prop, initial)

    return computed


def compute_all(root: Element, rules: list) -> dict:
    """Walk the whole tree top-down (parent before child — required,
    since a child's inheritance depends on the parent's ALREADY-computed
    style), returning {id(node): computed_style_dict}."""
    result: dict[int, dict] = {}

    def _walk(node: Element, parent_style):
        style = compute_style(node, rules, parent_style)
        result[id(node)] = style
        for child in node.children:
            if isinstance(child, Element):
                _walk(child, style)

    _walk(root, None)
    return result


if __name__ == "__main__":
    html = """
    <body>
      <p class="highlight">Text <span>inner</span></p>
      <div class="a b">Both classes</div>
      <div id="special" class="override">Important test</div>
      <p>Plain paragraph</p>
    </body>
    """
    # Source order matters for this test, and is deliberately arranged so
    # that "correct answer" and "the rule listed last" disagree, except
    # where they're SUPPOSED to agree (case 2).
    css = """
    .highlight { color: red; border: 1px solid black; }
    p { color: black; }

    .a { color: blue; }
    .b { color: green; }

    #special { color: navy; }
    .override { color: orange !important; }
    """

    tree = parse_html(html)
    rules = parse_stylesheet(css)
    styles = compute_all(tree, rules)

    elements = list(walk(tree))
    highlight_p = next(e for e in elements if e.tag == "p" and "highlight" in e.attrs.get("class", ""))
    inner_span = next(e for e in elements if e.tag == "span")
    ab_div = next(e for e in elements if e.tag == "div" and e.attrs.get("class") == "a b")
    special_div = next(e for e in elements if e.attrs.get("id") == "special")
    plain_p = next(e for e in elements if e.tag == "p" and "class" not in e.attrs)

    print("=" * 70)
    print("Computed styles for each test element")
    print("=" * 70)
    for label, el in [("<p class=highlight>", highlight_p), ("<span> inside it", inner_span),
                       ("<div class='a b'>", ab_div), ("<div id=special class=override>", special_div),
                       ("<p> (plain)", plain_p)]:
        print(f"{label}: {styles[id(el)]}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"CASE 1 — specificity beats source order: .highlight (class, spec 0,1,0) "
          f"beats 'p' (type, spec 0,0,1) declared AFTER it -> color=red: "
          f"{styles[id(highlight_p)]['color'] == 'red'}")

    print(f"CASE 2 — equal specificity, source order tiebreak: .a then .b, "
          f"both spec 0,1,0, LATER (.b) wins -> color=green: "
          f"{styles[id(ab_div)]['color'] == 'green'}")

    print(f"CASE 3 — !important beats higher specificity: .override (spec 0,1,0, "
          f"!important) beats #special (spec 1,0,0, not important) -> color=orange: "
          f"{styles[id(special_div)]['color'] == 'orange'}")

    print(f"CASE 4a — inheritance: <span> has no color rule of its own, "
          f"inherits parent's computed color=red: "
          f"{styles[id(inner_span)]['color'] == 'red'}")
    print(f"CASE 4b — non-inherited property does NOT leak: <span> has no "
          f"'border' in its computed style even though its parent does: "
          f"{'border' not in styles[id(inner_span)]}")

    print(f"CASE 5 — initial value fallback: plain <p> has no font-weight "
          f"rule anywhere, falls back to initial 'normal': "
          f"{styles[id(plain_p)]['font-weight'] == 'normal'}")
