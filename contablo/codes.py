import iso3166


def is_luhn_valid(n: str) -> bool:
    # from https://stackoverflow.com/questions/21079439/implementation-of-luhn-formula
    r = [int(ch) for ch in str(n)][::-1]
    return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0


def is_valid_isin(isin: str) -> bool:
    # https://de.wikipedia.org/wiki/Internationale_Wertpapierkennnummer
    if len(isin) != 12:
        return False
    isin = isin.upper()
    cc = isin[0:2]
    if cc not in ["XS", "EU"]:
        try:
            iso3166.countries.get(cc)
        except KeyError:
            return False
    code = "".join([c if c.isdigit() else str(10 + ord(c) - ord("A")) for c in list(isin)])
    # print(isin, cc, nsin, cs, code)
    if not is_luhn_valid(code):
        return False
    return True
