"""
Module 31 — The DOM XSS Sink: innerHTML vs. textContent
============================================================
Proves the actual, final mechanism behind DOM-based XSS: the EXACT SAME
untrusted string is completely safe through one DOM API and genuinely
dangerous through another — not because the string is different, but
because of what the receiving API DOES with it. This is the real-world
`element.innerHTML = untrusted` vs. `element.textContent = untrusted`
distinction, implemented for real against this course's own DOM.

Also proves the fix: running the exact same string through Module 30's
sanitizer FIRST makes the innerHTML-style sink safe too — sanitize,
THEN render, never the other way around.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "05_html_tokenizer"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "30_html_sanitization"))
from html_tokenizer import tokenize                       # noqa: E402
from dom_tree_builder import build_tree, Element, TextNode  # noqa: E402  -- REUSED
from html_sanitization import sanitize_children             # noqa: E402  -- REUSED, unmodified


def set_text(el: Element, text: str) -> None:
    """The SAFE sink — mirrors real element.textContent = value.
    The string is NEVER parsed as markup; it becomes exactly one
    literal TextNode, whatever characters it contains."""
    el.children = [TextNode(text, parent=el)]


def set_inner_html(el: Element, html: str) -> None:
    """The DANGEROUS sink — mirrors real element.innerHTML = value.
    The string is tokenized and tree-built EXACTLY like a real page's
    own HTML (Modules 5 and 6, unmodified) — if it contains real markup,
    real Elements are created, indistinguishable from ones the page's
    own developer wrote."""
    fragment_root = build_tree(tokenize(html))
    for child in fragment_root.children:
        child.parent = el
    el.children = fragment_root.children


def set_inner_html_sanitized(el: Element, html: str) -> None:
    """The FIX: sanitize (Module 30) BEFORE parsing into the live tree.
    Same sink, same parsing, but the untrusted string never gets the
    chance to become a dangerous Element in the first place."""
    fragment_root = build_tree(tokenize(html))
    fragment_root.children = sanitize_children(fragment_root.children)
    for child in fragment_root.children:
        child.parent = el
    el.children = fragment_root.children


if __name__ == "__main__":
    payload = '<img src=x onerror="alert(document.cookie)">'
    container = Element(tag="div", attrs={"id": "comment-box"})

    print("=" * 70)
    print(f"The SAME untrusted string: {payload!r}")
    print("=" * 70)

    print()
    print("--- Routed through set_text() (textContent-equivalent) ---")
    set_text(container, payload)
    print(f"  container.children: {container.children}")
    text_children = container.children

    print()
    print("--- Routed through set_inner_html() (innerHTML-equivalent) ---")
    set_inner_html(container, payload)
    print(f"  container.children: {container.children}")
    html_children = container.children

    print()
    print("--- Routed through set_inner_html_sanitized() (Module 30 first) ---")
    set_inner_html_sanitized(container, payload)
    print(f"  container.children: {container.children}")
    sanitized_children = container.children

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"set_text(): container has exactly ONE child, a TextNode "
          f"(never parsed as markup): "
          f"{len(text_children) == 1 and isinstance(text_children[0], TextNode)}")
    print(f"set_text(): that TextNode's data is the payload EXACTLY, "
          f"literal characters and all: {text_children[0].data == payload}")

    img_elements = [c for c in html_children if isinstance(c, Element) and c.tag == "img"]
    print(f"set_inner_html(): a REAL <img> Element was created — the "
          f"string genuinely became structure, not text: {len(img_elements) == 1}")
    print(f"set_inner_html(): that REAL Element has a REAL 'onerror' "
          f"attribute — the actual DOM-XSS moment, a live, structural "
          f"attribute a real browser would execute on image load failure: "
          f"{len(img_elements) == 1 and 'onerror' in img_elements[0].attrs}")

    img_elements_sanitized = [c for c in sanitized_children if isinstance(c, Element) and c.tag == "img"]
    print(f"set_inner_html_sanitized(): the <img> tag still exists "
          f"(it's on Module 30's allowlist) but its onerror is GONE: "
          f"{len(img_elements_sanitized) == 1 and 'onerror' not in img_elements_sanitized[0].attrs}")
    print(f"the payload is IDENTICAL in all three cases — the only "
          f"difference in outcome is which function received it: "
          f"{True}  (same `payload` variable passed to all three calls above)")
