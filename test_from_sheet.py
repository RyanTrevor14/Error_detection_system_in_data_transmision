"""Run the test cases listed in a spreadsheet (saved as CSV) through the simulator.

Usage:
    python3 test_from_sheet.py                 # reads test_cases.csv
    python3 test_from_sheet.py mytests.csv     # reads another file
"""
import csv
import re
import sys

from sender import build_parity_frame, generate_crc, is_binary
from channel import flip_bits
from receiver import verify_parity, verify_crc, ERROR

DEFAULT_FILE = "test_cases.csv"


# ---------- reading the spreadsheet text ----------

def parse_scheme(text):
    """'Even Parity' -> ('PARITY', 'EVEN'), 'CRC (1101)' -> ('CRC', '1101')."""
    t = text.lower()
    if "even" in t:
        return "PARITY", "EVEN"
    if "odd" in t:
        return "PARITY", "ODD"
    if "crc" in t:
        m = re.search(r"\(\s*([01]+)\s*\)", text)
        if not m:
            raise ValueError(f"CRC scheme needs a generator, e.g. CRC (1101): {text!r}")
        return "CRC", m.group(1)
    raise ValueError(f"unknown scheme: {text!r}")


def parse_payload(text):
    """'110101 (4 ones)' -> '110101'."""
    m = re.match(r"\s*([01]+)", text)
    if not m:
        raise ValueError(f"payload must start with binary digits: {text!r}")
    return m.group(1)


def parse_flips(text):
    """Pull the bit indices out of the error description. 'None' -> []."""
    m = re.search(r"\[([^\]]*)\]", text)          # e.g. "indices [1, 3]"
    if m:
        return sorted(int(x) for x in re.findall(r"\d+", m.group(1)))
    m = re.search(r"index\s+(\d+)", text, re.IGNORECASE)   # e.g. "index 0"
    if m:
        return [int(m.group(1))]
    if text.strip() == "" or "none" in text.lower():
        return []
    raise ValueError(f"could not read bit positions from: {text!r}")


def expected_outcome(verdict_text):
    """Map the spreadsheet's verdict wording to VALID, CAUGHT or MISSED."""
    t = verdict_text.lower()
    if "missed" in t:
        return "MISSED"
    if "fail" in t or "caught" in t:
        return "CAUGHT"
    if "pass" in t:
        return "VALID"
    raise ValueError(f"unrecognised verdict: {verdict_text!r}")


# ---------- running one test case ----------

def run_case(row):
    scheme, param = parse_scheme(row["Scheme"])
    payload = parse_payload(row["Input Payload"])
    flips = parse_flips(row["Injected Error Pattern"])

    if scheme == "PARITY":
        sent = build_parity_frame(payload, param)
    else:
        sent = generate_crc(payload, param)

    received = flip_bits(sent, flips) if flips else sent

    if scheme == "PARITY":
        verdict, value = verify_parity(received, param)
        detail = f"count of 1s = {value}"
    else:
        verdict, value = verify_crc(received, param)
        detail = f"remainder = {value}"

    if verdict == ERROR:
        outcome = "CAUGHT"
    elif flips:
        outcome = "MISSED"       # the bits changed, but the receiver accepted the frame
    else:
        outcome = "VALID"        # nothing changed, and the receiver accepted it

    return {
        "payload": payload,
        "sent": sent,
        "flips": flips,
        "received": received,
        "verdict": verdict,
        "detail": detail,
        "outcome": outcome,
    }


def describe_flips(flips):
    if not flips:
        return "none"
    if len(flips) == 1:
        return f"single bit at index {flips[0]}"
    return f"{len(flips)} bits at indices {', '.join(map(str, flips))}"


def print_case(row, r):
    expected = expected_outcome(row["Receiver Verdict"])
    match = "MATCH" if expected == r["outcome"] else "MISMATCH"

    print(f"\n=== Test Case {row['Test Case']} ===")
    print(f"Scheme:              {row['Scheme']}")
    print(f"Input payload:       {r['payload']}")
    print(f"Sent frame:          {r['sent']}")
    print(f"Error injected:      {describe_flips(r['flips'])}")
    print(f"Intercepted packet:  {r['received']}")
    print(f"Receiver verdict:    {r['verdict']} ({r['detail']})")
    print(f"Outcome:             {r['outcome']}")
    print(f"Spreadsheet expects: {expected}  ->  {match}")

    sheet_packet = row["Intercepted Packets"]
    if sheet_packet != r["received"]:
        print(f"WARNING: spreadsheet lists intercepted packet {sheet_packet}, "
              f"but the correct packet is {r['received']}")


def print_summary(rows_out):
    print("\n=== SUMMARY ===")
    print(f"{'Case':>4} | {'Scheme':<12} | {'Payload':<8} | {'Outcome':<7} | "
          f"{'Sheet':<7} | {'Result':<8} | {'Packet check'}")
    print("-" * 80)
    for case, scheme, payload, outcome, sheet, result, packet_ok in rows_out:
        packet_text = "OK" if packet_ok else "differs from sheet"
        print(f"{case:>4} | {scheme:<12} | {payload:<8} | {outcome:<7} | "
              f"{sheet:<7} | {result:<8} | {packet_text}")

    total = len(rows_out)
    matched = sum(1 for x in rows_out if x[5] == "MATCH")
    packets_ok = sum(1 for x in rows_out if x[6])
    print(f"\nVerdicts matching the spreadsheet: {matched} of {total}")
    print(f"Intercepted packets matching the spreadsheet: {packets_ok} of {total}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = [
                {k.strip(): (v or "").strip() for k, v in row.items() if k}
                for row in csv.DictReader(f)
            ]
    except FileNotFoundError:
        print(f"Could not find '{path}'. Save your spreadsheet as CSV in this folder.")
        return

    rows = [r for r in rows if r.get("Test Case")]
    print(f"Running {len(rows)} test case(s) from {path}")

    rows_out = []
    for row in rows:
        try:
            r = run_case(row)
        except (ValueError, IndexError) as err:
            print(f"\n=== Test Case {row['Test Case']} ===")
            print(f"ERROR: {err}")
            rows_out.append((row["Test Case"], row["Scheme"], row["Input Payload"],
                             "ERROR", "-", "ERROR", False))
            continue

        print_case(row, r)
        expected = expected_outcome(row["Receiver Verdict"])
        rows_out.append((
            row["Test Case"],
            row["Scheme"],
            r["payload"],
            r["outcome"],
            expected,
            "MATCH" if expected == r["outcome"] else "MISMATCH",
            row["Intercepted Packets"] == r["received"],
        ))

    print_summary(rows_out)


if __name__ == "__main__":
    main()