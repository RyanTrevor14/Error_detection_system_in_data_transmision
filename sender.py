"""Sender side: computes redundant bits and builds the transmission frame."""


def is_binary(s):
    """True if s is a non-empty string made only of '0' and '1'."""
    return isinstance(s, str) and len(s) > 0 and all(c in "01" for c in s)


def generate_parity_bit(data_bits, parity_type):
    """Return the parity bit ('0' or '1') for data_bits.

    EVEN: the total number of 1s (data + parity bit) must be even.
    ODD:  the total number of 1s (data + parity bit) must be odd.
    """
    if not is_binary(data_bits):
        raise ValueError("data_bits must be a non-empty string of 0s and 1s")

    one_count = 0
    for bit in data_bits:              # Step 2: count the 1s
        if bit == "1":
            one_count += 1

    if parity_type == "EVEN":          # Step 3: choose the bit
        return "0" if one_count % 2 == 0 else "1"
    if parity_type == "ODD":
        return "1" if one_count % 2 == 0 else "0"
    raise ValueError("parity_type must be 'EVEN' or 'ODD'")


def build_parity_frame(data_bits, parity_type):
    """Append the parity bit to the data."""
    return data_bits + generate_parity_bit(data_bits, parity_type)


def modulo2_division(dividend, divisor):
    """Modulo-2 (XOR) long division. Returns the remainder, len(divisor) - 1 bits."""
    if not is_binary(dividend) or not is_binary(divisor):
        raise ValueError("dividend and divisor must be binary strings")
    if divisor[0] != "1":
        raise ValueError("generator polynomial must start with 1")
    if len(divisor) < 2:
        raise ValueError("generator polynomial must have at least 2 bits")
    if len(dividend) < len(divisor):
        raise ValueError("dividend must be at least as long as the divisor")

    temp = list(dividend)              # work on a copy as a list of bits
    divisor_len = len(divisor)

    # Scan from left to right; wherever the leading bit is 1, XOR the divisor in.
    for i in range(len(temp) - divisor_len + 1):
        if temp[i] == "1":
            for j in range(divisor_len):
                temp[i + j] = "0" if temp[i + j] == divisor[j] else "1"

    # The remainder is the last (divisor_len - 1) bits.
    return "".join(temp[-(divisor_len - 1):])


def generate_crc(data_bits, generator):
    """Return the transmitted frame: data_bits followed by its CRC remainder."""
    if not is_binary(data_bits):
        raise ValueError("data_bits must be a non-empty string of 0s and 1s")
    gen_len = len(generator)
    padded = data_bits + "0" * (gen_len - 1)         # Step A: append zeros
    remainder = modulo2_division(padded, generator)  # Steps B and C
    return data_bits + remainder                     # Step D: replace the zeros