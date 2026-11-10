"""Transmission simulation: injects bit errors into a packet."""
import random


def flip_bits(packet, indices):
    """Return a copy of packet with the bits at the given indices inverted."""
    bits = list(packet)
    for index in indices:
        if not 0 <= index < len(bits):
            raise IndexError(f"bit index {index} is out of range 0 to {len(bits) - 1}")
        bits[index] = "1" if bits[index] == "0" else "0"
    return "".join(bits)


def random_flip(packet):
    """Flip one randomly chosen bit. Returns (corrupted_packet, index)."""
    index = random.randrange(len(packet))
    return flip_bits(packet, [index]), index