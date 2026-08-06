"""
Module 21 — Chrome UI: Address Bar, Tabs, History
=====================================================
Proves: a user can navigate to real pages (real network fetches, via
Modules 3/4) and go back/forward through them with CORRECT history
state — including the single trickiest, most commonly-buggy part of
navigation history: visiting a new page after going back must TRUNCATE
the abandoned forward history, not just leave it sitting there.

This module reuses Module 2 (URL parsing), Module 3/4 (fetching), and
Module 5 (tokenizing, to pull a real <title> out of a real response) —
no new networking or parsing logic is written here.
"""

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "02_url_parser"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "03_http_from_scratch"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "04_https_tls"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "05_html_tokenizer"))
from url_parser import parse_url                        # noqa: E402
from http_client import fetch as fetch_http               # noqa: E402
from https_client import fetch_https                        # noqa: E402
from html_tokenizer import tokenize, StartTag, Text          # noqa: E402


def extract_title(html: str) -> str:
    """Reuses Module 5's real tokenizer to find <title>...</title> —
    no separate string-searching/regex logic for this."""
    tokens = tokenize(html)
    for i, tok in enumerate(tokens):
        if isinstance(tok, StartTag) and tok.name == "title":
            if i + 1 < len(tokens) and isinstance(tokens[i + 1], Text):
                return tokens[i + 1].data.strip()
    return "(untitled)"


@dataclass
class HistoryEntry:
    url: str
    title: str
    status: int


class NavigationHistory:
    """The back/forward stack. `index` always points at the CURRENT
    entry. The one rule that makes this correct rather than just
    functional: navigating to a new page while not at the end of the
    list must discard everything past the current index FIRST."""

    def __init__(self):
        self.entries: list = []
        self.index: int = -1

    def push(self, entry: HistoryEntry) -> None:
        # Truncate any abandoned "forward" history before adding the new
        # entry — otherwise a page visited after going back would sit
        # alongside pages that are no longer reachable by forward().
        self.entries = self.entries[: self.index + 1]
        self.entries.append(entry)
        self.index += 1

    def can_go_back(self) -> bool:
        return self.index > 0

    def can_go_forward(self) -> bool:
        return self.index < len(self.entries) - 1

    def back(self):
        if not self.can_go_back():
            return None
        self.index -= 1
        return self.entries[self.index]

    def forward(self):
        if not self.can_go_forward():
            return None
        self.index += 1
        return self.entries[self.index]

    def current(self):
        return self.entries[self.index] if self.index >= 0 else None


class BrowserTab:
    """One tab: an address bar (the `go()` method), backed by a real
    NavigationHistory and real network fetches."""

    def __init__(self):
        self.history = NavigationHistory()

    def go(self, url_string: str) -> HistoryEntry:
        url = parse_url(url_string)
        response = fetch_https(url_string) if url.scheme == "https" else fetch_http(url_string)
        body_text = response.body.decode("utf-8", errors="replace")
        entry = HistoryEntry(url=url_string, title=extract_title(body_text),
                              status=response.status_code)
        self.history.push(entry)
        return entry

    def back(self):
        return self.history.back()

    def forward(self):
        return self.history.forward()


if __name__ == "__main__":
    tab = BrowserTab()

    print("=" * 70)
    print("Real navigation: visiting two genuinely different real pages")
    print("=" * 70)
    e1 = tab.go("http://example.com/")
    print(f"  go(1): {e1.url} -> {e1.status} {e1.title!r}")
    e2 = tab.go("http://info.cern.ch/hypertext/WWW/TheProject.html")
    print(f"  go(2): {e2.url} -> {e2.status} {e2.title!r}")

    print(f"\nhistory has 2 entries, currently at index 1 (the 2nd page): "
          f"{len(tab.history.entries) == 2 and tab.history.index == 1}")

    print()
    print("=" * 70)
    print("Going BACK")
    print("=" * 70)
    back_entry = tab.back()
    print(f"  back() -> {back_entry.url} -> {back_entry.title!r}")
    print(f"can_go_forward() is now True (info.cern.ch is still reachable): "
          f"{tab.history.can_go_forward()}")

    print()
    print("=" * 70)
    print("Visiting a NEW page after going back — must TRUNCATE the abandoned forward entry")
    print("=" * 70)
    e3 = tab.go("https://example.com/")
    print(f"  go(3): {e3.url} -> {e3.status} {e3.title!r}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"history now has exactly 2 entries, not 3 — info.cern.ch was "
          f"correctly discarded: {len(tab.history.entries) == 2}")
    print(f"the surviving 2 entries are example.com (http) then example.com "
          f"(https) — info.cern.ch is GONE: "
          f"{[e.url for e in tab.history.entries] == ['http://example.com/', 'https://example.com/']}")
    print(f"forward() now returns None — there is nothing to go forward to: "
          f"{tab.forward() is None}")
    print(f"current entry is the https version, correctly the most recent: "
          f"{tab.history.current().url == 'https://example.com/'}")

    print()
    back_again = tab.back()
    print(f"back() from here correctly returns to the ORIGINAL http "
          f"example.com entry: {back_again.url == 'http://example.com/'}")
    print(f"back() again is a safe no-op (can't go before the first page): "
          f"{tab.back() is None}")
