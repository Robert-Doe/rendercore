"""
Module 27 — HTML Entity Encoding
====================================
Proves: encoding untrusted text before inserting it into HTML body
content prevents it from being tokenized as markup at all — verified by
feeding both the raw and the encoded version of a real exploit payload
through Module 5's REAL tokenizer and confirming the difference in what
actually comes out: a real StartTag token vs. a single inert Text token.

This is the actual mechanism behind the most common form of XSS: a
server (or client-side script) inserts untrusted text into an HTML
page. If that text is inserted RAW, and it happens to contain
`<script>...</script>`, Module 5's tokenizer — the same tokenizer any
real browser uses — will produce a real StartTag('script') token, and a
real browser would run it.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "05_html_tokenizer"))
from html_tokenizer import tokenize, StartTag, Text   # noqa: E402  -- REUSED, unmodified

# Order doesn't matter here BECAUSE we look up each character
# independently rather than doing sequential string replacements — see
# DECISIONS.md for the real, classic bug this design choice avoids.
ENTITY_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
}


def encode_html_entities(s: str) -> str:
    return "".join(ENTITY_MAP.get(ch, ch) for ch in s)


def naive_wrong_order_encode(s: str) -> str:
    """A real, classic bug: replacing < and > BEFORE &. The & introduced
    by &lt;/&gt; gets encoded AGAIN on the final .replace('&', '&amp;')
    pass, double-encoding the output. See DECISIONS.md."""
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("&", "&amp;")
    return s


def has_real_tag(html: str, tag_name: str) -> bool:
    """The actual proof mechanism: tokenize with Module 5's REAL
    tokenizer and check whether a StartTag token for `tag_name` exists
    anywhere in the output."""
    return any(isinstance(tok, StartTag) and tok.name == tag_name for tok in tokenize(html))


if __name__ == "__main__":
    payload = '<script>alert(document.cookie)</script>'

    print("=" * 70)
    print("CASE 1 — the actual vulnerability: raw insertion into HTML body")
    print("=" * 70)
    print(f"  payload: {payload}")
    raw_tokens = tokenize(payload)
    print(f"  tokenized (UNENCODED) produces: {raw_tokens}")
    print(f"  a REAL <script> StartTag token exists: {has_real_tag(payload, 'script')}")

    print()
    print("=" * 70)
    print("CASE 2 — the same payload, entity-encoded first")
    print("=" * 70)
    encoded_payload = encode_html_entities(payload)
    print(f"  encoded: {encoded_payload}")
    encoded_tokens = tokenize(encoded_payload)
    print(f"  tokenized (ENCODED) produces: {encoded_tokens}")
    print(f"  a <script> StartTag token exists: {has_real_tag(encoded_payload, 'script')}")

    print()
    print("=" * 70)
    print("CASE 3 — which character actually matters most: '<' or '>'?")
    print("=" * 70)
    missing_lt = payload.replace(">", "&gt;")            # forgot to encode '<'
    missing_gt = payload.replace("<", "&lt;")             # forgot to encode '>'
    print(f"  forgot to encode '<' : {missing_lt!r} -> "
          f"real <script> tag forms: {has_real_tag(missing_lt, 'script')}")
    print(f"  forgot to encode '>' : {missing_gt!r} -> "
          f"real <script> tag forms: {has_real_tag(missing_gt, 'script')}")

    print()
    print("=" * 70)
    print("CASE 4 — a real, classic bug: encoding in the WRONG order")
    print("=" * 70)
    correct = encode_html_entities("<b>")
    wrong = naive_wrong_order_encode("<b>")
    print(f"  correct (char-by-char, order-independent): {correct!r}")
    print(f"  WRONG order (< and > replaced BEFORE &):    {wrong!r}")
    print(f"  the wrong-order version double-encodes the '&' that '&lt;' "
          f"itself introduced — a real display-corruption bug, distinct "
          f"from (though related to) the security issue in Cases 1-3")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"UNENCODED payload produces a REAL <script> tag (the vulnerability, "
          f"reproduced against the real tokenizer): {has_real_tag(payload, 'script')}")
    print(f"ENCODED payload produces NO <script> tag at all: "
          f"{not has_real_tag(encoded_payload, 'script')}")
    print(f"encoded payload is a SINGLE Text token, nothing else: "
          f"{len(encoded_tokens) == 1 and isinstance(encoded_tokens[0], Text)}")
    print(f"forgetting to encode '<' STILL lets the tag form (the load-bearing "
          f"character): {has_real_tag(missing_lt, 'script')}")
    print(f"forgetting to encode '>' does NOT let the tag form (a real tag "
          f"needs an actual '<' to even begin): {not has_real_tag(missing_gt, 'script')}")
    print(f"wrong-order encoding double-encodes '&' (correctness bug, verified): "
          f"{wrong == '&amp;lt;b&amp;gt;' and correct == '&lt;b&gt;'}")
