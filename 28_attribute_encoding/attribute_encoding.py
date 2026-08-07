"""
Module 28 — Attribute & URL-Scheme Encoding
===============================================
Proves TWO distinct things:

PART A — inserting untrusted text into a double-quoted HTML attribute
without encoding the quote character lets an attacker "break out" of
the attribute entirely and inject a brand-new, real attribute (like an
event handler) — verified by parsing the result with Module 5's real
tokenizer and checking its actual `attrs` dict, not just eyeballing the
string.

PART B — even with quote-breakout fully prevented, a `javascript:` URL
placed as the ENTIRE value of `href`/`src` is dangerous on its own, no
quotes involved at all — and a naive scheme check can itself be bypassed
using a real, documented browser quirk: browsers ignore tab/newline/CR
characters ANYWHERE in a URL when determining its scheme.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "05_html_tokenizer"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "27_entity_encoding"))
from html_tokenizer import tokenize, StartTag        # noqa: E402  -- REUSED, unmodified
from entity_encoding import encode_html_entities        # noqa: E402  -- REUSED, unmodified


# ======================================================= PART A: ATTRIBUTES

def render_attr_UNSAFE(tag: str, attr_name: str, value: str) -> str:
    """Deliberately vulnerable: splices `value` into a double-quoted
    attribute with NO encoding at all."""
    return f'<{tag} {attr_name}="{value}">'


def render_attr_safe(tag: str, attr_name: str, value: str) -> str:
    """Reuses Module 27's encoder wholesale. It already encodes '\"' and
    \"'\", which is exactly what an attribute context additionally needs
    beyond body-text context — see DECISIONS.md for why reusing the
    superset encoder here, rather than writing a narrower
    attribute-only one, is the right call."""
    return f'<{tag} {attr_name}="{encode_html_entities(value)}">'


def find_start_tag(html: str, tag: str) -> StartTag:
    return next(t for t in tokenize(html) if isinstance(t, StartTag) and t.name == tag)


# =================================================== PART B: URL SCHEMES

DANGEROUS_SCHEMES = ("javascript:", "vbscript:", "data:")


def is_dangerous_url_scheme_NAIVE(url: str) -> bool:
    """Looks reasonable. Is not — see the bypass in Case 3."""
    return url.strip().lower().startswith(DANGEROUS_SCHEMES)


def is_dangerous_url_scheme(url: str) -> bool:
    """Real browsers strip ALL tab/newline/carriage-return characters
    from ANYWHERE in a URL — not just the ends — before determining its
    scheme. A scheme check that only strips leading/trailing whitespace
    can be bypassed by hiding one of those characters in the MIDDLE of
    the word 'javascript'."""
    stripped = re.sub(r"[\t\r\n]", "", url).strip()
    return stripped.lower().startswith(DANGEROUS_SCHEMES)


if __name__ == "__main__":
    print("=" * 70)
    print("PART A — CASE 1: the actual vulnerability, attribute breakout")
    print("=" * 70)
    malicious_value = '" onmouseover="alert(document.cookie)'
    unsafe_html = render_attr_UNSAFE("input", "value", malicious_value)
    print(f"  constructed HTML: {unsafe_html}")
    unsafe_tag = find_start_tag(unsafe_html, "input")
    print(f"  Module 5 parses its attrs as: {unsafe_tag.attrs}")
    print(f"  a REAL, INJECTED 'onmouseover' attribute now exists: "
          f"{'onmouseover' in unsafe_tag.attrs}")

    print()
    print("=" * 70)
    print("PART A — CASE 2: the same value, attribute-encoded first")
    print("=" * 70)
    safe_html = render_attr_safe("input", "value", malicious_value)
    print(f"  constructed HTML: {safe_html}")
    safe_tag = find_start_tag(safe_html, "input")
    print(f"  Module 5 parses its attrs as: {safe_tag.attrs}")
    print(f"  NO 'onmouseover' attribute exists — the whole payload stayed "
          f"inside the ORIGINAL 'value' attribute: "
          f"{'onmouseover' not in safe_tag.attrs and 'onmouseover' in safe_tag.attrs.get('value', '')}")

    print()
    print("=" * 70)
    print("PART B — CASE 3: a naive scheme check gets bypassed with a hidden tab")
    print("=" * 70)
    obvious_payload = "javascript:alert(document.cookie)"
    sneaky_payload = "java\tscript:alert(document.cookie)"   # real browsers still treat this as javascript:
    print(f"  obvious payload: {obvious_payload!r}")
    print(f"    naive check flags it as dangerous: {is_dangerous_url_scheme_NAIVE(obvious_payload)}")
    print(f"    fixed check flags it as dangerous: {is_dangerous_url_scheme(obvious_payload)}")
    print(f"  sneaky payload (tab hidden inside 'javascript'): {sneaky_payload!r}")
    print(f"    naive check flags it as dangerous: {is_dangerous_url_scheme_NAIVE(sneaky_payload)}")
    print(f"    fixed check flags it as dangerous: {is_dangerous_url_scheme(sneaky_payload)}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"UNSAFE render lets an attacker inject a REAL 'onmouseover' "
          f"attribute (the vulnerability, reproduced against the real "
          f"tokenizer): {'onmouseover' in unsafe_tag.attrs}")
    print(f"SAFE render keeps the entire payload as inert VALUE text, no "
          f"new attribute created: {'onmouseover' not in safe_tag.attrs}")
    print(f"the safe version's 'value' attribute contains the ENCODED "
          f"payload whole (data preserved, not discarded): "
          f"{'onmouseover' in safe_tag.attrs['value']}")
    print(f"the obvious javascript: payload is caught by BOTH checks: "
          f"{is_dangerous_url_scheme_NAIVE(obvious_payload) and is_dangerous_url_scheme(obvious_payload)}")
    print(f"the sneaky tab-hidden payload BYPASSES the naive check "
          f"(real, documented bypass, reproduced): "
          f"{is_dangerous_url_scheme_NAIVE(sneaky_payload) is False}")
    print(f"the sneaky payload is CAUGHT by the fixed check: "
          f"{is_dangerous_url_scheme(sneaky_payload) is True}")
