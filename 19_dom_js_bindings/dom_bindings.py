"""
Module 19 — DOM–JS Bindings
==============================
Proves: script running through Module 18's real interpreter can call
DOM-manipulating functions and OBSERVABLY mutate the real DOM tree from
Module 6 — verified by reading the actual Python Element objects
afterward, not just by trusting the script's own printed output.

Module 18's interpreter has no object/property syntax (no `.`, no `[]`)
— see its DECISIONS.md. So these bindings are exposed as flat function
calls (`setText(el, "...")`) rather than property assignment
(`el.textContent = "..."`), the way real JS/DOM does it. This is a real,
named simplification of the real DOM API shape — not a different
capability.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "18_toy_js_interpreter"))
from dom_tree_builder import parse_html, Element, TextNode   # noqa: E402
from js_interpreter import Interpreter, parse                  # noqa: E402


def _find_by_id(node: Element, target_id: str):
    """Depth-first search for an element with a matching id attribute —
    see prereqs/trees_and_recursion.html."""
    if isinstance(node, Element) and node.attrs.get("id") == target_id:
        return node
    for child in node.children:
        if isinstance(child, Element):
            found = _find_by_id(child, target_id)
            if found is not None:
                return found
    return None


def bind_dom(interp: Interpreter, document: Element) -> None:
    """Register DOM-manipulating functions into the interpreter's global
    scope — the exact same mechanism Module 18 used for `print`: these
    are just Python callables stored as JS values. No change to
    js_interpreter.py was needed to support this."""

    def js_getElementById(target_id):
        el = _find_by_id(document, target_id)
        if el is None:
            raise LookupError(f"getElementById: no element with id={target_id!r}")
        return el

    def js_getText(el: Element) -> str:
        return "".join(c.data for c in el.children if isinstance(c, TextNode))

    def js_setText(el: Element, text: str) -> None:
        # A simplified textContent setter: replace ALL children with one
        # text node — real DOM's textContent does exactly this too.
        el.children = [TextNode(text, parent=el)]

    def js_getAttribute(el: Element, name: str):
        return el.attrs.get(name)

    def js_setAttribute(el: Element, name: str, value: str) -> None:
        el.attrs[name] = value

    def js_createElement(tag: str) -> Element:
        return Element(tag=tag)

    def js_appendChild(parent: Element, child: Element) -> None:
        child.parent = parent
        parent.children.append(child)

    def js_getTag(el: Element) -> str:
        return el.tag

    interp.global_env.declare("getElementById", js_getElementById)
    interp.global_env.declare("getText", js_getText)
    interp.global_env.declare("setText", js_setText)
    interp.global_env.declare("getAttribute", js_getAttribute)
    interp.global_env.declare("setAttribute", js_setAttribute)
    interp.global_env.declare("createElement", js_createElement)
    interp.global_env.declare("appendChild", js_appendChild)
    interp.global_env.declare("getTag", js_getTag)


if __name__ == "__main__":
    html = """
    <body>
      <div id="target">original text</div>
    </body>
    """
    document = parse_html(html)
    target = _find_by_id(document, "target")
    print(f"BEFORE running any script — real DOM state:")
    print(f"  target text: {''.join(c.data for c in target.children if isinstance(c, TextNode))!r}")
    print(f"  target attrs: {target.attrs}")
    print(f"  target children count: {len(target.children)}")

    script = """
    let el = getElementById("target");
    print(getText(el));

    setText(el, "Updated by JS!");
    print(getText(el));

    setAttribute(el, "data-touched", "true");
    print(getAttribute(el, "data-touched"));

    let newEl = createElement("span");
    setText(newEl, "I was created by JS");
    appendChild(el, newEl);
    print(getTag(newEl));
    """

    interp = Interpreter()
    bind_dom(interp, document)
    interp.run(parse(script))

    print()
    print("=" * 70)
    print("Script's own print() output")
    print("=" * 70)
    for line in interp.output:
        print(f"  {line}")

    print()
    print("=" * 70)
    print("AFTER running the script — reading the REAL DOM tree directly,")
    print("NOT trusting the script's own printed output")
    print("=" * 70)
    # `target` is the SAME Python object referenced before the script ran —
    # we never re-parsed or re-fetched anything.
    real_text_nodes = [c for c in target.children if isinstance(c, TextNode)]
    real_span = next((c for c in target.children if isinstance(c, Element) and c.tag == "span"), None)
    print(f"  target.attrs: {target.attrs}")
    print(f"  target.children: {target.children}")

    print()
    print("=" * 70)
    print("Checks — against the real Element object, not interp.output")
    print("=" * 70)
    print(f"script's first print() saw the ORIGINAL text: "
          f"{interp.output[0] == 'original text'}")
    print(f"the REAL target Element's attrs dict now contains data-touched=true "
          f"(mutated by the SAME object reference held since before the script ran): "
          f"{target.attrs.get('data-touched') == 'true'}")
    print(f"the REAL target Element now has a <span> CHILD, actually appended "
          f"to its real .children list: "
          f"{real_span is not None and real_span.tag == 'span'}")
    print(f"that real <span> child's real text content is correct: "
          f"{real_span is not None and ''.join(c.data for c in real_span.children if isinstance(c, TextNode)) == 'I was created by JS'}")
