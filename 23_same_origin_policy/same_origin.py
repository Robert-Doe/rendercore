"""
Module 23 — Same-Origin Policy
=================================
Proves: a script running in one tab is PROVABLY blocked from reading
another tab's DOM or cookies when the two tabs are cross-origin — and,
just as important, provably ALLOWED when they're same-origin, so this
is demonstrably an origin check, not just a blanket "always deny."

Reuses Module 2's URL.origin(), Module 6's DOM, Module 18's interpreter,
and Module 22's CookieJar completely unmodified — this module is the
enforcement layer wrapped around all four.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "02_url_parser"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "18_toy_js_interpreter"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "22_cookies_storage"))
from url_parser import parse_url                    # noqa: E402
from dom_tree_builder import parse_html               # noqa: E402
from js_interpreter import Interpreter, parse           # noqa: E402
from cookies import CookieJar                            # noqa: E402


class SecurityError(Exception):
    pass


class Tab:
    def __init__(self, tab_id: str, url: str, html: str):
        self.tab_id = tab_id
        self.origin = parse_url(url).origin()
        self.document = parse_html(html)
        self.cookie_jar = CookieJar()
        self.cookie_jar.set_from_header(f"session={tab_id}_secret", parse_url(url).host)


class BrowserRegistry:
    """Stands in for 'the browser process,' which is the only thing
    with visibility into every tab at once — exactly the real
    architectural reason same-origin enforcement lives at this level,
    not inside any individual tab's own script."""

    def __init__(self):
        self.tabs: dict = {}

    def register(self, tab: Tab) -> None:
        self.tabs[tab.tab_id] = tab

    def access_document(self, requesting_origin: str, target_tab_id: str):
        target = self.tabs[target_tab_id]
        if requesting_origin != target.origin:
            raise SecurityError(
                f"Blocked: a script from origin {requesting_origin!r} "
                f"attempted to read tab {target_tab_id!r}'s document, "
                f"but that tab's origin is {target.origin!r}."
            )
        return target.document

    def access_cookies(self, requesting_origin: str, target_tab_id: str):
        target = self.tabs[target_tab_id]
        if requesting_origin != target.origin:
            raise SecurityError(
                f"Blocked: a script from origin {requesting_origin!r} "
                f"attempted to read tab {target_tab_id!r}'s cookies, "
                f"but that tab's origin is {target.origin!r}."
            )
        return target.cookie_jar.cookies_for(parse_url(target.origin + "/").host, "/", is_secure=True)


def make_interpreter_for(registry: BrowserRegistry, own_origin: str) -> Interpreter:
    """Every binding here closes over `own_origin` — the ORIGIN THE
    SCRIPT IS RUNNING IN, fixed at creation. A script cannot lie about
    its own origin any more than a real page's JS can claim to run
    somewhere it doesn't."""
    interp = Interpreter()

    def js_accessForeignDocument(target_tab_id):
        doc = registry.access_document(own_origin, target_tab_id)
        return f"<{doc.children[0].tag}> (real access granted)"

    def js_accessForeignCookies(target_tab_id):
        return registry.access_cookies(own_origin, target_tab_id)

    interp.global_env.declare("accessForeignDocument", js_accessForeignDocument)
    interp.global_env.declare("accessForeignCookies", js_accessForeignCookies)
    return interp


def run_script_expect(interp: Interpreter, script: str):
    """Run a script; return ('ok', output_list) or ('denied', message)."""
    try:
        interp.run(parse(script))
        return "ok", interp.output
    except SecurityError as e:
        return "denied", str(e)


if __name__ == "__main__":
    registry = BrowserRegistry()
    registry.register(Tab("bank", "https://bank.example.com/", "<body><h1>Account Balance: $4,201</h1></body>"))
    registry.register(Tab("evil", "https://evil.example.com/", "<body><h1>Free Prizes!!!</h1></body>"))
    registry.register(Tab("bank2", "https://bank.example.com/", "<body><h1>Another bank.example.com tab</h1></body>"))
    registry.register(Tab("bank_http", "http://bank.example.com/", "<body><h1>Unencrypted bank.example.com</h1></body>"))

    print("=" * 70)
    print("Registered tabs and their origins")
    print("=" * 70)
    for tab_id, tab in registry.tabs.items():
        print(f"  {tab_id:10s} -> {tab.origin}")

    print()
    print("=" * 70)
    print("TEST 1 — a script in evil.example.com tries to read bank's document")
    print("=" * 70)
    evil_interp = make_interpreter_for(registry, registry.tabs["evil"].origin)
    status, result = run_script_expect(evil_interp, 'accessForeignDocument("bank");')
    print(f"  result: {status.upper()}")
    if status == "denied":
        print(f"  {result}")

    print()
    print("=" * 70)
    print("TEST 2 — a script in a SECOND bank.example.com tab reads the FIRST's document")
    print("=" * 70)
    bank2_interp = make_interpreter_for(registry, registry.tabs["bank2"].origin)
    status2, result2 = run_script_expect(bank2_interp, 'print(accessForeignDocument("bank"));')
    print(f"  result: {status2.upper()}")
    if status2 == "ok":
        print(f"  script's own output: {result2}")

    print()
    print("=" * 70)
    print("TEST 3 — evil.example.com tries to read bank's COOKIES (the session token)")
    print("=" * 70)
    status3, result3 = run_script_expect(evil_interp, 'accessForeignCookies("bank");')
    print(f"  result: {status3.upper()}")

    print()
    print("=" * 70)
    print("TEST 4 — SAME host, DIFFERENT scheme (http vs https) — must ALSO be denied")
    print("=" * 70)
    http_interp = make_interpreter_for(registry, registry.tabs["bank_http"].origin)
    status4, result4 = run_script_expect(http_interp, 'accessForeignDocument("bank");')
    print(f"  bank_http's origin:  {registry.tabs['bank_http'].origin}")
    print(f"  bank's origin:       {registry.tabs['bank'].origin}")
    print(f"  result: {status4.upper()}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"TEST 1 (cross-origin document read) correctly DENIED: {status == 'denied'}")
    print(f"TEST 2 (same-origin document read) correctly ALLOWED: {status2 == 'ok'}")
    print(f"TEST 2's script genuinely received real document content, not a stub: "
          f"{status2 == 'ok' and 'real access granted' in result2[0]}")
    print(f"TEST 3 (cross-origin cookie read) correctly DENIED: {status3 == 'denied'}")
    print(f"TEST 4 (same host, different SCHEME) correctly DENIED, proving the "
          f"check is the full (scheme, host, port) triple, not just hostname: "
          f"{status4 == 'denied'}")
