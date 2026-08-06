"""
Module 12 — Text Layout & Line Breaking
==========================================
Proves: a long run of text correctly wraps into multiple lines within a
given width, word by word — using the same GREEDY, first-fit algorithm
real browsers actually use for ordinary text flow (not the more
expensive globally-optimal algorithm word processors use for justified
paragraphs — see DECISIONS.md).

Text WIDTH MEASUREMENT is deliberately pluggable (a `measure_fn`
callback), because this module has no real font/canvas available yet —
that arrives in Module 15. The wrapping ALGORITHM below is independent of
how width gets measured, and is tested here with a simple, fully
deterministic stand-in measurement.
"""

from dataclasses import dataclass


def fixed_width_measure(word: str, char_width: float = 10.0) -> float:
    """Stand-in for real font metrics: every character is exactly
    `char_width` pixels wide. Deliberately unrealistic (real fonts are
    NOT monospaced) but fully deterministic, which is what makes this
    module's line-break math checkable by hand. See DECISIONS.md."""
    return len(word) * char_width


def wrap_words(words: list, max_width: float, measure_fn, space_width: float) -> list:
    """Greedy line breaking: keep adding words to the current line while
    they fit; the moment one doesn't, start a new line. A word that's
    WIDER than max_width all by itself still gets placed — as the sole
    occupant of its own (overflowing) line — rather than looping forever
    trying to make it fit."""
    lines: list[list[str]] = []
    current: list[str] = []
    current_width = 0.0

    for word in words:
        word_width = measure_fn(word)
        add_width = word_width if not current else space_width + word_width

        if current and current_width + add_width > max_width:
            lines.append(current)
            current = [word]
            current_width = word_width
        else:
            current.append(word)
            current_width += add_width

    if current:
        lines.append(current)
    return lines


def measure_line(words: list, measure_fn, space_width: float) -> float:
    if not words:
        return 0.0
    total = sum(measure_fn(w) for w in words)
    total += space_width * (len(words) - 1)
    return total


@dataclass
class LineBox:
    text: str
    x: float
    y: float
    width: float
    height: float


def layout_text(text: str, max_width: float, origin_x: float, origin_y: float,
                 char_width: float = 10.0, line_height: float = 20.0) -> list:
    """Wrap `text` to `max_width` and assign each resulting line a real
    (x, y) position, stacking lines vertically by `line_height` — the
    inline-content equivalent of Module 11's block-stacking cursor."""
    measure_fn = lambda w: fixed_width_measure(w, char_width)
    space_width = char_width   # a space is treated as one character wide

    words = text.split()
    lines_of_words = wrap_words(words, max_width, measure_fn, space_width)

    boxes = []
    y = origin_y
    for words_in_line in lines_of_words:
        boxes.append(LineBox(
            text=" ".join(words_in_line),
            x=origin_x,
            y=y,
            width=measure_line(words_in_line, measure_fn, space_width),
            height=line_height,
        ))
        y += line_height
    return boxes


if __name__ == "__main__":
    print("=" * 70)
    print("CASE 1 — ordinary word wrapping at a narrow width")
    print("=" * 70)
    sentence = "Hello World this is a test of wrapping"
    lines1 = layout_text(sentence, max_width=100, origin_x=0, origin_y=0, char_width=10.0)
    for lb in lines1:
        print(f"  y={lb.y:5.0f}  width={lb.width:5.0f}  {lb.text!r}")

    expected1 = ["Hello", "World this", "is a test", "of", "wrapping"]
    actual1 = [lb.text for lb in lines1]
    print(f"\nmatches hand-computed expected line groupings: {actual1 == expected1}")
    print(f"5 lines, each 20px apart vertically (y = 0,20,40,60,80): "
          f"{[lb.y for lb in lines1] == [0, 20, 40, 60, 80]}")

    print()
    print("=" * 70)
    print("CASE 2 — a single word wider than max_width doesn't break or hang")
    print("=" * 70)
    long_word_text = "short Supercalifragilisticexpialidocious short2"
    lines2 = layout_text(long_word_text, max_width=100, origin_x=0, origin_y=0, char_width=10.0)
    for lb in lines2:
        print(f"  y={lb.y:5.0f}  width={lb.width:5.0f}  {lb.text!r}")

    expected2 = ["short", "Supercalifragilisticexpialidocious", "short2"]
    actual2 = [lb.text for lb in lines2]
    print(f"\nlong word gets its OWN line (not merged, not crashed): "
          f"{actual2 == expected2}")
    print(f"that line's width (340) legitimately EXCEEDS max_width (100) — "
          f"real, intentional overflow, not a bug: {lines2[1].width == 340.0}")

    print()
    print("=" * 70)
    print("CASE 3 — a wider container produces fewer, longer lines from the SAME text")
    print("=" * 70)
    lines3 = layout_text(sentence, max_width=1000, origin_x=0, origin_y=0, char_width=10.0)
    print(f"  {[lb.text for lb in lines3]}")
    print(f"the whole sentence fits on ONE line when the container is wide enough: "
          f"{len(lines3) == 1 and lines3[0].text == sentence}")
