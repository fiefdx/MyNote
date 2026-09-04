# -*- coding: utf-8 -*-
'''
Created on 2014-06-06 (original), ported 2024
@summary: Encrypt / decrypt string layer built on top of the ``tea_encrypt``
          library (https://github.com/fiefdx/tea_encrypt).

Background
----------
MyNote originally depended on the author's older ``tea`` package, whose
``EncryptStr`` returned ``binascii.hexlify(ciphertext)`` i.e. an ASCII hex
*bytes* string (utf-8 decodable), and whose ``DecryptStr`` accepted that hex
string and returned the raw plaintext bytes. All existing MyNote databases
store encrypted fields as these hex strings.

The replacement library ``tea_encrypt`` implements the *identical* TEA cipher,
but its ``EncryptStr`` now returns raw ciphertext bytes instead of a hex string.
Calling ``EncryptStr(...).decode("utf-8")`` on raw ciphertext (as item.py does)
would raise UnicodeDecodeError, and would also break compatibility with
already encrypted notes.

This module restores the original ``tea`` public API on top of ``tea_encrypt``:

    EncryptStr(v, k) -> bytes   # ASCII hex bytes, utf-8 decodable (same as old tea)
    DecryptStr(v, k) -> bytes   # raw plaintext bytes (same as old tea)

so existing databases keep working and the ``.decode("utf-8")`` call sites in
item.py remain valid under Python 3.
'''

import binascii

import tea_encrypt

__version__ = getattr(tea_encrypt, "__version__", "unknown")

# Re-export the low-level cipher helpers for anyone who wants them directly.
raw_encrypt = tea_encrypt.EncryptStr
raw_decrypt = tea_encrypt.DecryptStr


def EncryptStr(v, k, iterations=32):
    """
    Encrypt string/bytes ``v`` with md5-hex key ``k``.

    Returns ASCII hex *bytes* (interleaving + random-padding TEA), matching the
    historical ``tea`` library output so stored values stay compatible.
    """
    return binascii.hexlify(tea_encrypt.EncryptStr(v, k, iterations))


def DecryptStr(v, k, iterations=32):
    """
    Decrypt hex string/bytes ``v`` with md5-hex key ``k``.

    Returns the raw plaintext bytes (empty ``bytes`` if the padding check fails,
    i.e. wrong key / corrupted data), matching the historical ``tea`` library.

    ``tea_encrypt`` returns a ``str`` ``""`` on padding mismatch; the original
    ``tea`` always returned bytes, so callers can safely do ``.decode("utf-8")``.
    Normalize to ``bytes`` to keep that contract under Python 3.
    """
    result = tea_encrypt.DecryptStr(v, k, iterations)
    if isinstance(result, str):
        result = result.encode("utf-8")
    return result
