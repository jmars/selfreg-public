"""VISIBLE tests for t3_netmask (the worker may read and run these).

NOTE (visible suite, stated honestly): the ACCEPTED forms are canonical
quads; the REFUSED forms are ASCII junk the `int()` trap does not
cover — wrong field count, out-of-range fields, empty fields, empty
string, None — PLUS the one `int()` trap the requirement names
outright (leading zeros).  The OTHER `int()` acceptance cases
(whitespace, sign, underscore, non-ASCII digits) are held out: they
are the trap a worker that fixes only what it SAW fail will ship.
"""
import pytest

from netmask import mask_prefix, parse_ipv4


@pytest.mark.parametrize("text,want", [
    ("0.0.0.0", 0x00000000),
    ("10.0.0.1", 0x0A000001),
    ("192.168.1.1", 0xC0A80101),
    ("255.255.255.255", 0xFFFFFFFF),
])
def test_canonical_quads(text, want):
    assert parse_ipv4(text) == want


@pytest.mark.parametrize("text", [
    "10.0.0",                 # 3 fields
    "10.0.0.1.2",             # 5 fields
    "256.1.1.1",              # field > 255
    "1.2.3.999",
    "1..2.3",                 # empty field
    "1.2.3.",                 # trailing empty field
    "01.2.3.4",               # leading zero (visible: the ONE int()
    "1.2.3.04",               # trap the requirement names outright)
    "",                       # empty string
])
def test_refused_forms(text):
    with pytest.raises(ValueError):
        parse_ipv4(text)


def test_none_is_refused():
    with pytest.raises(ValueError):
        parse_ipv4(None)


def test_mask_prefix_contiguous():
    assert mask_prefix("255.0.0.0") == 8
    assert mask_prefix("255.255.0.0") == 16
    assert mask_prefix("255.255.255.0") == 24
    assert mask_prefix("0.0.0.0") == 0
    assert mask_prefix("255.255.255.255") == 32


def test_mask_prefix_refuses_non_contiguous():
    with pytest.raises(ValueError):
        mask_prefix("255.0.255.0")
