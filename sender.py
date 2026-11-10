# sender.py - Encoding Module
# This module handles the sender-side logic: generating parity bits and computing CRC remainders.

def generate_parity_bit(data_bits, parity_type="EVEN"):
    """
    Generates an Even or Odd parity bit for the given binary string.
    """
    # Step 1: Count how many '1's are in the data payload
    one_count = data_bits.count('1')
    
    # Step 2: Apply the parity rule based on user choice
    if parity_type == "EVEN":
        # For Even parity: if 1s count is even, append '0'; if odd, append '1' to make it even
        return "0" if one_count % 2 == 0 else "1"
    elif parity_type == "ODD":
        # For Odd parity: if 1s count is odd, append '0'; if even, append '1' to make it odd
        return "0" if one_count % 2 != 0 else "1"

def modulo_2_division(dividend, divisor):
    """
    Performs modulo-2 division (XOR shifting) to find the CRC remainder.
    This is the mathematical core of the CRC algorithm.
    """
    # Python strings are immutable, so we convert the binary string into a list of characters
    temp = list(dividend)
    divisor_len = len(divisor)
    
    # Slide across the dividend from left to right, bit by bit
    for i in range(len(temp) - divisor_len + 1):
        # If the current leading bit is '1', perform XOR with the generator polynomial (divisor)
        if temp[i] == '1':
            for j in range(divisor_len):
                # XOR operation rule:
                # If bits match (0 and 0, or 1 and 1), result is '0'
                # If bits differ (0 and 1), result is '1'
                temp[i + j] = '0' if temp[i + j] == divisor[j] else '1'
                
    # The final remainder is always the last (divisor_len - 1) bits of the temp list
    return "".join(temp[-(divisor_len - 1):])

def generate_crc(data_bits, generator_polynomial="1011"):
    """
    Appends the CRC remainder to the data bits based on a chosen generator polynomial.
    """
    gen_len = len(generator_polynomial)
    
    # Step 1: Pad the data with zeros equal to (length of generator polynomial - 1)
    padded_data = data_bits + ("0" * (gen_len - 1))
    
    # Step 2: Calculate the CRC remainder using our modulo-2 division function
    remainder = modulo_2_division(padded_data, generator_polynomial)
    
    # Step 3: Combine original data with the remainder to form the final transmitted frame
    return data_bits + remainder