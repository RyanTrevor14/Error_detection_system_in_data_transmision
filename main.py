"""Interactive testing lab for error detection (parity and CRC)."""
import random

from sender import build_parity_frame, generate_crc, is_binary
from channel import flip_bits
from receiver import verify_parity, verify_crc, NO_ERROR, ERROR

DEFAULT_GENERATOR = "1101"


# ---------- input helpers ----------

def ask(prompt, valid=None):
    """Keep asking until the answer is non-empty (and in 'valid', if given)."""
    while True:
        answer = input(prompt).strip()
        if answer and (valid is None or answer in valid):
            return answer
        print("  Invalid input, please try again.")


def ask_yes_no(prompt):
    return ask(prompt, valid=("y", "n", "Y", "N")).lower() == "y"


def ask_binary(prompt):
    """Ask for a non-empty string of 0s and 1s."""
    while True:
        value = input(prompt).strip()
        if is_binary(value):
            return value
        print("  Message must contain only 0s and 1s.")


def ask_generator():
    """Ask for the generator polynomial, defaulting to DEFAULT_GENERATOR."""
    print(f"\nEnter the generator polynomial (press Enter for {DEFAULT_GENERATOR}).")
    while True:
        generator = input("Generator: ").strip() or DEFAULT_GENERATOR
        if is_binary(generator) and generator[0] == "1" and len(generator) >= 2:
            return generator
        print("  Generator must be a binary string starting with 1, at least 2 bits long.")


def ask_positions(length, min_count, max_count):
    """Ask for bit positions, with a count between min_count and max_count."""
    if min_count == max_count:
        print(f"  Enter {min_count} bit position(s). Positions run from 0 to {length - 1}.")
    else:
        print(f"  Enter {min_count} to {max_count} bit positions. "
              f"Positions run from 0 to {length - 1}.")
    while True:
        raw = input("  Positions (separated by commas): ").strip()
        try:
            indices = [int(x) for x in raw.split(",") if x.strip() != ""]
            if (min_count <= len(indices) <= max_count
                    and len(set(indices)) == len(indices)
                    and all(0 <= i < length for i in indices)):
                return sorted(indices)
        except ValueError:
            pass
        print("  Invalid positions, please try again (no repeats, within range).")


def ask_flip_count(length):
    """Ask how many bits to flip randomly, from 2 up to the packet length."""
    while True:
        raw = input(f"  How many bits to flip (2 to {length}): ").strip()
        if raw.isdigit() and 2 <= int(raw) <= length:
            return int(raw)
        print("  Invalid number, please try again.")


# ---------- channel ----------

def inject_errors(packet):
    """Simulate the channel. Returns (received_packet, flipped_positions)."""
    print("\nSimulate channel transmission...")
    if not ask_yes_no("Would you like to inject a bit error? (y/n): "):
        print("[CHANNEL] No errors injected. Packet passed through unchanged.")
        return packet, []

    print("  [1] Single-bit error")
    print("  [2] Multiple-bit errors (two or more bits)")
    multi = ask("  Enter choice (1 or 2): ", valid=("1", "2")) == "2"

    print("  [1] Choose the bit position(s) yourself")
    print("  [2] Pick random position(s)")
    manual = ask("  Enter choice (1 or 2): ", valid=("1", "2")) == "1"

    length = len(packet)
    if manual:
        if multi:
            positions = ask_positions(length, 2, length)
        else:
            positions = ask_positions(length, 1, 1)
    else:
        count = ask_flip_count(length) if multi else 1
        positions = sorted(random.sample(range(length), count))

    received = flip_bits(packet, positions)
    label = "Bit flipped at index" if len(positions) == 1 else "Bits flipped at indices"
    print(f"[CHANNEL] {label} {', '.join(map(str, positions))}. "
          f"Received Packet: {received}")
    return received, positions


# ---------- verdict helpers ----------

def count_ones(bits):
    return bits.count("1")


def print_verdict(verdict, error_note):
    if verdict == NO_ERROR:
        print(f"[RECEIVER] Status: {verdict} (data accepted)")
    else:
        print(f"[RECEIVER] Status: {verdict} ({error_note})")


# ---------- parity test ----------

def run_parity():
    print("\nSelect Parity Type:")
    print("[1] Even Parity")
    print("[2] Odd Parity")
    parity_type = "EVEN" if ask("Enter choice (1 or 2): ", valid=("1", "2")) == "1" else "ODD"

    data = ask_binary("Enter binary message payload (e.g., 1011): ")

    parity_frame = build_parity_frame(data, parity_type)
    print(f"\n[SENDER] Original Data: {data}")
    print(f"[SENDER] Calculated Parity Bit: {parity_frame[-1]}")
    print(f"[SENDER] Transmitted Packet: {parity_frame}")

    received, positions = inject_errors(parity_frame)

    print(f"\n[RECEIVER] Intercepted Packet: {received}")
    print("[RECEIVER] Running Parity Verification...")
    verdict, one_count = verify_parity(received, parity_type)
    print(f"[RECEIVER] Count of 1s: {one_count}")
    print_verdict(verdict, "Data corrupted during transit")

    if not positions:
        return

    # Lab notes: reveal what really happened so the limitation is visible.
    print(f"\n[LAB] Ones in sent packet: {count_ones(parity_frame)}, "
          f"ones in received packet: {count_ones(received)}")
    if verdict == NO_ERROR:
        print(f"[LAB] Parity MISSED the error: {len(positions)} bits changed, but the "
              f"number of 1s still has the expected parity.")
    else:
        print("[LAB] Parity caught the error.")

    if ask_yes_no("\nRetest the same data and error positions with CRC? (y/n): "):
        generator = ask_generator()
        run_crc_with(data, generator, positions)


# ---------- CRC test ----------

def run_crc_with(data, generator, positions=None):
    """Send data with CRC. If positions is given, flip those same bits instead of asking."""
    frame = generate_crc(data, generator)
    crc_bits = frame[len(data):]
    print(f"\n[SENDER] Original Data: {data}")
    print(f"[SENDER] Generator: {generator}")
    print(f"[SENDER] CRC Bits: {crc_bits}")
    print(f"[SENDER] Transmitted Frame: {frame}")

    if positions is None:
        received, positions = inject_errors(frame)
    else:
        received = flip_bits(frame, positions)
        print("\nSimulate channel transmission...")
        print(f"[CHANNEL] Same error positions as the parity test: "
              f"{', '.join(map(str, positions))}. Received Frame: {received}")

    print(f"\n[RECEIVER] Intercepted Frame: {received}")
    print("[RECEIVER] Running CRC Verification...")
    verdict, remainder = verify_crc(received, generator)
    print(f"[RECEIVER] Remainder: {remainder}")
    print_verdict(verdict, "Frame corrupted during transit, discard and request retransmission")

    if positions:
        if verdict == ERROR:
            print("[LAB] CRC caught the error.")
        else:
            print("[LAB] CRC MISSED this error.")


def run_crc():
    generator = ask_generator()
    data = ask_binary("\nEnter binary message payload (e.g., 10100110): ")
    run_crc_with(data, generator)


# ---------- menu ----------

def main():
    print("=== ERROR DETECTION SIMULATION LAB ===")
    while True:
        print("\nSelect Error Detection Scheme:")
        print("[1] Parity Check (Even/Odd)")
        print("[2] Cyclic Redundancy Check (CRC)")
        print("[q] Quit")
        choice = ask("Enter choice (1, 2 or q): ", valid=("1", "2", "q", "Q"))
        if choice.lower() == "q":
            print("Goodbye.")
            break
        if choice == "1":
            run_parity()
        else:
            run_crc()

        if not ask_yes_no("\nRun another test? (y/n): "):
            print("Goodbye.")
            break


if __name__ == "__main__":
    main()