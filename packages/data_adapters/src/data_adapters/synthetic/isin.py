"""ISIN (ISO 6166) calculation and validation with Luhn check digit."""

import re

_ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def calculate_isin_check_digit(base11: str) -> str:
    """Calculate Luhn check digit for an 11-character ISIN base string."""
    if len(base11) != 11:
        raise ValueError(f"ISIN base must be exactly 11 alphanumeric characters, got {len(base11)}")

    digits: list[int] = []
    for char in base11.upper():
        if char.isdigit():
            digits.append(int(char))
        elif "A" <= char <= "Z":
            val = ord(char) - ord("A") + 10
            digits.extend([val // 10, val % 10])
        else:
            raise ValueError(f"Invalid character in ISIN base: {char}")

    s = 0
    double = True
    for d in reversed(digits):
        if double:
            val = d * 2
            if val > 9:
                val -= 9
            s += val
        else:
            s += d
        double = not double

    check = (10 - (s % 10)) % 10
    return str(check)


def make_isin(country_code: str, nsin: str) -> str:
    """Generate a complete 12-character ISIN with valid check digit."""
    country = country_code.upper()
    if len(country) != 2 or not country.isalpha():
        raise ValueError(f"Country code must be 2 letters, got '{country_code}'")
    
    nsin_clean = nsin.upper()
    if len(nsin_clean) != 9 or not nsin_clean.isalnum():
        raise ValueError(f"NSIN must be 9 alphanumeric characters, got '{nsin}'")

    base = f"{country}{nsin_clean}"
    return f"{base}{calculate_isin_check_digit(base)}"


def validate_isin(isin: str) -> bool:
    """Verify that a string is a syntactically valid ISIN with correct Luhn check digit."""
    if not isinstance(isin, str) or not _ISIN_PATTERN.match(isin.upper()):
        return False
    base = isin.upper()[:11]
    expected_check = calculate_isin_check_digit(base)
    return isin[-1] == expected_check
