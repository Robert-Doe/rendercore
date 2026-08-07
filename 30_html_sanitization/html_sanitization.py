"""
Module 30 — HTML Sanitization (Allowlist-Based)
====================================================
Proves: untrusted HTML can be sanitized down to a SAFE SUBSET — keeping
real structure (bold text, links, paragraphs) while removing dangerous
tags, dangerous attributes, and dangerous URL schemes — verified by
walking the REAL sanitized DOM tree (Module 6) afterward and confirming,
structurally, that nothing dangerous survived anywhere in it.

Unlike Modules 27-29 (which fully neutralize ALL markup), this module
solves the harder problem: some real markup must be ALLOWED through.
Allowlisting — deciding what's permitted and rejecting everything else
by default — is the only approach that stays safe as new, unanticipated
dangerous tags/attributes are invented; a denylist has to be updated
every time a new attack surface is discovered, an allowlist doesn't.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "28_attribute_encoding"))
from dom_tree_builder import parse_html, Element, TextNode, CommentNode   # noqa: E402
from attribute_encoding import is_dangerous_url_scheme                      # noqa: E402  -- REUSED

# Tags whose entire subtree (including text/code content) is removed —
# their CONTENT is inherently unsafe, not just the tag wrapping it.
DANGEROUS_TAGS = {"script", "style", "iframe", "object", "embed", "form"}

# Tags allowed to remain AS TAGS. Anything else that isn't dangerous
# gets "unwrapped" — the tag is discarded, but its (sanitized) children
# survive in its place.
ALLOWED_TAGS = {"p", "b", "i", "strong", "em", "a", "ul", "ol", "li",
                 "br", "span", "div", "img"}

# Attributes allowed to remain, per tag. Anything not listed here
# (including every "on*" event handler) is stripped.
ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt"},
    "*": set(),   # every other allowed tag: no attributes survive by default
}

URL_ATTRS = {"href", "src"}   # attributes whose VALUE also needs scheme checking


def _sanitize_attrs(tag: str, attrs: dict) -> dict:
    allowed_names = ALLOWED_ATTRS.get(tag, ALLOWED_ATTRS["*"])
    clean = {}
    for name, value in attrs.items():
        if name not in allowed_names:
            continue   # not on the allowlist for this tag — dropped, no exceptions
        if name in URL_ATTRS and is_dangerous_url_scheme(value):
            continue   # allowed ATTRIBUTE, but a dangerous URL VALUE — dropped anyway
        clean[name] = value
    return clean


def sanitize_children(children: list) -> list:
    """Bottom-up: sanitize each child's OWN children first, then decide
    that child's own fate (keep as-is, unwrap, or drop)."""
    result = []
    for child in children:
        if isinstance(child, TextNode):
            result.append(child)
        elif isinstance(child, CommentNode):
            continue   # comments dropped entirely — see DECISIONS.md
        elif isinstance(child, Element):
            if child.tag in DANGEROUS_TAGS:
                continue   # whole subtree gone, content included

            child.children = sanitize_children(child.children)   # recurse first

            if child.tag in ALLOWED_TAGS:
                child.attrs = _sanitize_attrs(child.tag, child.attrs)
                result.append(child)
            else:
                result.extend(child.children)   # UNWRAP: tag gone, children survive
    return result


def sanitize_html(html: str) -> Element:
    tree = parse_html(html)
    tree.children = sanitize_children(tree.children)
    return tree


def walk(node) -> list:
    out = [node] if isinstance(node, Element) else []
    for c in getattr(node, "children", []):
        out.extend(walk(c))
    return out


def all_text(node) -> str:
    if isinstance(node, TextNode):
        return node.data
    return "".join(all_text(c) for c in getattr(node, "children", []))


if __name__ == "__main__":
    payload = (
        '<p>Hello <b>world</b></p>'
        '<script>alert(document.cookie)</script>'
        '<a href="javascript:alert(1)">click here</a>'
        '<img src="x.png" onerror="alert(1)">'
        '<fancybox>weird custom tag</fancybox>'
        '<div onclick="alert(1)">Click me</div>'
    )

    print("=" * 70)
    print("Untrusted input HTML")
    print("=" * 70)
    print(f"  {payload}")

    clean_tree = sanitize_html(payload)
    clean_elements = walk(clean_tree)

    print()
    print("=" * 70)
    print("Sanitized tree (every surviving Element)")
    print("=" * 70)
    for el in clean_elements:
        print(f"  <{el.tag}> attrs={el.attrs}")

    print()
    print("=" * 70)
    print("Checks — walking the REAL sanitized tree, not the output string")
    print("=" * 70)
    tags_present = {el.tag for el in clean_elements}
    print(f"NO dangerous tag survived anywhere in the tree: "
          f"{tags_present.isdisjoint(DANGEROUS_TAGS)}")
    all_attr_names = {name for el in clean_elements for name in el.attrs}
    print(f"NO 'on*' event handler attribute survived anywhere: "
          f"{not any(name.startswith('on') for name in all_attr_names)}")
    all_url_values = [v for el in clean_elements for k, v in el.attrs.items() if k in URL_ATTRS]
    print(f"NO surviving href/src value uses a dangerous scheme: "
          f"{not any(is_dangerous_url_scheme(v) for v in all_url_values)}")
    print(f"the javascript: href was dropped entirely (not just the tag): "
          f"{not any('href' in el.attrs for el in clean_elements if el.tag == 'a')}")
    print(f"safe structure was PRESERVED — <b>world</b> still exists as a "
          f"real Element: {'b' in tags_present}")
    print(f"the unknown <fancybox> tag was unwrapped, but its TEXT survived: "
          f"{'fancybox' not in tags_present and 'weird custom tag' in all_text(clean_tree)}")
    print(f"the allowed <div> survived, but its onclick did not: "
          f"{'div' in tags_present and 'onclick' not in [n for el in clean_elements if el.tag == 'div' for n in el.attrs]}")
    print(f"'Click me' text (from inside the sanitized div) survived: "
          f"{'Click me' in all_text(clean_tree)}")
    print(f"'Hello world' text survived: "
          f"{'Hello ' in all_text(clean_tree) and 'world' in all_text(clean_tree)}")
    print(f"the <script>'s CONTENT ('alert(document.cookie)') does NOT "
          f"survive anywhere, even as stray text: "
          f"{'alert(document.cookie)' not in all_text(clean_tree)}")
