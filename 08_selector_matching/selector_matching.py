"""
Module 8 — Selector Matching Engine
======================================
Proves: given a real DOM node (Module 6) and a real parsed rule list
(Module 7), we can determine exactly which rules' selectors match that
node — including correctly walking ancestors for descendant combinators,
and correctly NOT matching descendants of an element against a selector
that targets the element itself.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "07_css_parser"))
from dom_tree_builder import parse_html, Element                 # noqa: E402
from css_parser import parse_stylesheet, Rule, Selector, SimpleSelector  # noqa: E402


def node_classes(node: Element) -> set:
    return set(node.attrs.get("class", "").split())


def node_id(node: Element):
    return node.attrs.get("id")


def matches_simple(node: Element, simple: SimpleSelector) -> bool:
    """A compound selector matches a node only if EVERY constraint it
    states is satisfied — type, id, and all classes are ANDed together."""
    if simple.type_name is not None and node.tag != simple.type_name:
        return False
    if simple.id is not None and node_id(node) != simple.id:
        return False
    if simple.classes and not set(simple.classes).issubset(node_classes(node)):
        return False
    return True


def _find_matching_ancestor(node: Element, simple: SimpleSelector):
    """Walk upward from node's PARENT (not node itself) looking for the
    first ancestor satisfying `simple`. See DECISIONS.md for why picking
    the *first* (nearest) match, without backtracking, is provably
    correct for descendant-only combinators."""
    ancestor = node.parent
    while ancestor is not None:
        if matches_simple(ancestor, simple):
            return ancestor
        ancestor = ancestor.parent
    return None


def matches_selector(node: Element, selector: Selector) -> bool:
    """A Selector's RIGHTMOST compound must match the node itself; each
    compound to its left must match SOME ancestor, walking up one
    matched ancestor at a time."""
    parts = selector.parts
    if not parts:
        return False
    if not matches_simple(node, parts[-1]):
        return False

    current = node
    for part in reversed(parts[:-1]):
        current = _find_matching_ancestor(current, part)
        if current is None:
            return False
    return True


def matches_rule(node: Element, rule: Rule) -> bool:
    """A rule matches if ANY of its comma-separated selectors match —
    `.card, .panel { ... }` applies to elements matching either one."""
    return any(matches_selector(node, sel) for sel in rule.selectors)


def matching_rules(node: Element, rules: list) -> list:
    """Rules that match `node`, IN SOURCE ORDER — Module 9's cascade
    needs source order preserved to break specificity ties correctly."""
    return [r for r in rules if matches_rule(node, r)]


def walk(node: Element):
    """Depth-first traversal yielding every Element in the tree."""
    if isinstance(node, Element):
        yield node
        for child in node.children:
            yield from walk(child)


if __name__ == "__main__":
    html = """
    <body>
      <nav>
        <a href="#" class="active">Home</a>
        <a href="#">About</a>
      </nav>
      <div class="card featured" id="hero">
        <p>Hello</p>
      </div>
    </body>
    """
    css = """
    nav a.active { color: red; }
    nav a { color: blue; }
    .card { border: 1px solid; }
    #hero { padding: 20px; }
    p { margin: 0; }
    * { box-sizing: border-box; }
    """

    tree = parse_html(html)
    rules = parse_stylesheet(css)

    all_elements = list(walk(tree))
    active_link = next(e for e in all_elements if e.tag == "a" and "active" in node_classes(e))
    plain_link = next(e for e in all_elements if e.tag == "a" and "active" not in node_classes(e))
    hero_div = next(e for e in all_elements if e.tag == "div")
    paragraph = next(e for e in all_elements if e.tag == "p")

    def report(label, node):
        matched = matching_rules(node, rules)
        selectors = [repr(sel) for r in matched for sel in r.selectors if matches_selector(node, sel)]
        print(f"{label}: {len(matched)} rules matched -> {selectors}")
        return matched

    print("=" * 70)
    print("Matching each node against the full parsed rule list")
    print("=" * 70)
    m_active = report("<a class=active> (inside <nav>)", active_link)
    m_plain = report("<a> (no class, inside <nav>)", plain_link)
    m_div = report("<div class='card featured' id='hero'>", hero_div)
    m_p = report("<p> (inside the div, but not itself styled by .card/#hero)", paragraph)

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"active link matches 3 rules (nav a.active, nav a, *): {len(m_active) == 3}")
    print(f"plain link matches 2 rules (nav a, *) — NOT nav a.active: {len(m_plain) == 2}")
    print(f"hero div matches 3 rules (.card, #hero, *): {len(m_div) == 3}")
    print(f"paragraph matches 2 rules (p, *) — NOT .card or #hero "
          f"(single-compound selectors don't match descendants): {len(m_p) == 2}")
