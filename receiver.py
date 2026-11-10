"""Receiver side: verifies an incoming frame and reports a verdict."""
from sender import modulo2_division

NO_ERROR = "No Error Detected"
ERROR = "Error Detected"


def verify_parity(received, parity_type):
    """Return (verdict, one_count) for a frame that includes its parity bit."""
    one_count = 0
    for bit in received:
        if bit == "1":
            one_count += 1

    if parity_type == "EVEN":
        ok = one_count % 2 == 0
    elif parity_type == "ODD":
        ok = one_count % 2 != 0
    else:
        raise ValueError("parity_type must be 'EVEN' or 'ODD'")

    return (NO_ERROR if ok else ERROR), one_count


def verify_crc(received, generator):
    """Return (verdict, remainder). A zero remainder means no error."""
    remainder = modulo2_division(received, generator)
    verdict = ERROR if "1" in remainder else NO_ERROR
    return verdict, remainder