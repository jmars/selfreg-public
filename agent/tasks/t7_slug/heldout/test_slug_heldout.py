"""HELD-OUT tests for t7_slug.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): the CHARACTER
POLICY — what survives into a word.  The requirement says letters,
digits and spaces (so "C++" -> "c", "snake_case" -> "snakecase",
"3 blind mice" -> "3-blind-mice", "naïve" -> "naïve" with the accented
letter KEPT as a letter).  A worker that repairs only the separator and
the lowercasing it SAW fail still emits punctuation-laden slugs; that
gap is the class-(C) split.
"""
import pytest

from slug import slugify


@pytest.mark.parametrize("title,want", [
    ("Hello World", "hello-world"),
    ("  leading and trailing  ", "leading-and-trailing"),
    ("multiple   spaces\tbetween", "multiple-spaces-between"),
    ("C++ Reference", "c-reference"),
    ("snake_case keys", "snakecase-keys"),
    ("3 blind mice", "3-blind-mice"),
    ("naïve café", "naïve-café"),
    ("Hello, World!", "hello-world"),
    ("!!!", ""),
    ("a---b", "ab"),
])
def test_character_policy(title, want):
    assert slugify(title) == want


def test_max_words_applies_after_collapsing():
    assert slugify("Hello,  Brave New   World!", max_words=2) \
        == "hello-brave"


def test_no_leading_or_trailing_separator():
    assert slugify(" !!! hello !!! ") == "hello"
    assert slugify("---") == ""
