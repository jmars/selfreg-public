# Task t3_netmask

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> `netmask.py::parse_ipv4` must return the 32-bit integer value of a
> dotted-quad IPv4 address.  It must REFUSE (ValueError) everything
> that is not a canonical ASCII dotted quad: wrong field count, any
> field outside 0-255, empty fields, leading zeros, whitespace,
> underscores, non-ASCII digits, signs, and an empty/None input.
