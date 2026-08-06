"""
Module 6 — HTML Tree Builder / DOM Construction
==================================================
Proves: Module 5's flat token stream can be assembled into a real tree
(the DOM), including recovering from the kinds of "broken" HTML that
appear on real pages — an unclosed <p>, a <li> that never got its own
closing tag, a stray end tag with no matching start tag.

Explicitly out of scope (see DECISIONS.md): the WHATWG "adoption agency
algorithm" that lets a real browser reopen implicitly-closed formatting
elements after a misnested close. Our recovery is real and tested, but
simpler than a production parser's.
"""

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "05_html_tokenizer"))
from html_tokenizer import tokenize, StartTag, EndTag, Text, Comment   # noqa: E402


@dataclass
class Element:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    parent: "Element | None" = None

    def __repr__(self):
        return f"<{self.tag}{'' if not self.attrs else ' ' + str(self.attrs)}>"


@dataclass
class TextNode:
    data: str
    parent: "Element | None" = None

    def __repr__(self):
        return f"Text({self.data!r})"


@dataclass
class CommentNode:
    data: str
    parent: "Element | None" = None

    def __repr__(self):
        return f"Comment({self.data!r})"


Node = Element | TextNode | CommentNode

# Elements that never have children or a closing tag — the tree builder
# must never push these onto the open-elements stack, or every following
# sibling would incorrectly become their "child."
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Simplified "implicit close" rule: if the tag on TOP of the open-elements
# stack is in this set for the incoming start tag, close it first. Real
# HTML's actual rule scans further up the stack looking for a boundary
# element (e.g. the nearest <ul> for <li>) — see DECISIONS.md for why this
# module only checks the immediate top.
AUTO_CLOSE_ON_TOP = {
    "p": {"p"},
    "li": {"li"},
    "tr": {"tr"},
    "td": {"td", "th"},
    "th": {"td", "th"},
}


def build_tree(tokens) -> Element:
    """The open-elements stack always starts with a synthetic root, so
    "top of stack" is always well-defined — text or tags before any real
    element still have somewhere correct to attach."""
    root = Element(tag="#document")
    stack = [root]

    for tok in tokens:
        top = stack[-1]

        if isinstance(tok, StartTag):
            closers = AUTO_CLOSE_ON_TOP.get(tok.name)
            if closers and len(stack) > 1 and stack[-1].tag in closers:
                stack.pop()
                top = stack[-1]

            el = Element(tag=tok.name, attrs=dict(tok.attrs), parent=top)
            top.children.append(el)
            if tok.name not in VOID_ELEMENTS and not tok.self_closing:
                stack.append(el)

        elif isinstance(tok, EndTag):
            match_idx = None
            for i in range(len(stack) - 1, 0, -1):   # never match the root itself
                if stack[i].tag == tok.name:
                    match_idx = i
                    break
            if match_idx is not None:
                del stack[match_idx:]   # closes the match AND any unclosed tags above it
            # else: a stray end tag with no open match — ignored, per spec

        elif isinstance(tok, Text):
            top.children.append(TextNode(tok.data, parent=top))

        elif isinstance(tok, Comment):
            top.children.append(CommentNode(tok.data, parent=top))

    return root   # note: `stack` may still have >1 entry here — see tutorial.html 05


def parse_html(html: str) -> Element:
    return build_tree(tokenize(html))


def print_tree(node: Node, depth: int = 0) -> None:
    """Recursive tree printer — see prereqs/trees_and_recursion.html."""
    indent = "  " * depth
    if isinstance(node, Element):
        print(f"{indent}{node!r}")
        for child in node.children:
            print_tree(child, depth + 1)
    else:
        print(f"{indent}{node!r}")


if __name__ == "__main__":
    print("=" * 70)
    print("CASE 1 — unclosed <p> auto-closed by the next <p>")
    print("=" * 70)
    tree1 = parse_html("<p>One<p>Two")
    print_tree(tree1)
    ps = [c for c in tree1.children if isinstance(c, Element) and c.tag == "p"]
    print(f"\ntwo SIBLING <p> elements (not nested): {len(ps) == 2}")

    print()
    print("=" * 70)
    print("CASE 2 — <li> items with no closing tags, inside a <ul>")
    print("=" * 70)
    tree2 = parse_html("<ul><li>A<li>B<li>C</ul>")
    print_tree(tree2)
    ul = tree2.children[0]
    lis = [c for c in ul.children if isinstance(c, Element) and c.tag == "li"]
    print(f"\nthree <li> as direct children of <ul>: {len(lis) == 3}")

    print()
    print("=" * 70)
    print("CASE 3 — a void element (<br>) does not swallow following siblings")
    print("=" * 70)
    tree3 = parse_html("<div>A<br>B</div>")
    print_tree(tree3)
    div = tree3.children[0]
    br = next(c for c in div.children if isinstance(c, Element) and c.tag == "br")
    print(f"\n<br> has zero children: {len(br.children) == 0}")
    print(f"<div> has 3 children (text, br, text): {len(div.children) == 3}")

    print()
    print("=" * 70)
    print("CASE 4 — an unclosed tag at end-of-input still produces a")
    print("correctly NESTED tree (structure is built as we go, not deferred)")
    print("=" * 70)
    tree4 = parse_html("<div><p>Unclosed")
    print_tree(tree4)
    div4 = tree4.children[0]
    p4 = div4.children[0]
    print(f"\n<p> correctly nested inside <div> despite no </p> or </div>: "
          f"{div4.tag == 'div' and p4.tag == 'p' and p4.children[0].data == 'Unclosed'}")

    print()
    print("=" * 70)
    print("CASE 5 — misnested overlapping tags: <b>Bold <i>both</b> more</i>")
    print("(shows this module's REAL limitation — see tutorial.html 05)")
    print("=" * 70)
    tree5 = parse_html("<b>Bold <i>both</b> more</i>")
    print_tree(tree5)
    print("\nNote: real browsers reopen <i> after the misnested </b> (the")
    print("'adoption agency algorithm'), so 'more' would still be italic.")
    print("This module closes <i> early instead — 'more' ends up as plain")
    print("text, a sibling of <b>, not re-wrapped in a new <i>.")
