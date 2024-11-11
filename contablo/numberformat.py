from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NumberFormat:
    """Recognizes a number formatted with specific thousands and fractional separator."""

    # Todo: Decide on how to use sign.
    #   Currently, "-" allows for any sign, "+" enforces positive values
    #
    sign: str  #
    thou_sep: str  # thousands separator
    frac_sep: str  # fractional separator
    trailing_sign: bool = False

    @property
    def is_integer(self):
        return self.frac_sep == ""

    @property
    def format(self) -> str:
        elements = []
        if self.sign and not self.trailing_sign:
            elements.append(self.sign)
        elements.append("1")
        elements.append(self.thou_sep)
        elements.append("000")
        if self.frac_sep:
            elements.append(self.frac_sep)
            elements.append("00")
        if self.sign and self.trailing_sign:
            elements.append(self.sign)
        return "".join(elements)

    @staticmethod
    def from_format(format: str) -> NumberFormat:
        # Todo: This has become way too complicated, there should be a better way
        assert format != "" and format is not None, "Number requires a format"
        if not all([c in "+-.,'_0123456789" for c in format]):
            raise ValueError(f"Invalid character in '{format}'.")

        with_sign = format[0] in ["+", "-"]

        if with_sign:
            sign, number_fmt = format[0], format[1:]
        else:
            sign, number_fmt = "", format

        # fast track for integer values:
        try:
            int(number_fmt, 10)
            return NumberFormat(sign, "_", "")
        except ValueError:
            pass

        seps = [c for c in number_fmt if not c.isdigit()]

        if len(seps) == 1:
            thou_sep, frac_sep = "", seps[0]
        elif len(seps) == 2:
            thou_sep, frac_sep = seps
            if thou_sep == frac_sep:
                raise ValueError(
                    f"A valid number format requires maximal one fractional delimiter, not like '{format}'"
                )
        else:
            # there can be multiple thousands separators but only one in the format
            sepchars = list(set(seps))
            if len(sepchars) != 2:
                raise ValueError(f"More than two different separators in '{format}'.")
            if seps.count(sepchars[0]) == 1:
                thou_sep, frac_sep = sepchars[1], sepchars[0]
            elif seps.count(sepchars[1]) == 1:
                thou_sep, frac_sep = sepchars[0], sepchars[1]
            else:
                raise ValueError(f"There's more than a single decimal separator in '{format}'.")

        return NumberFormat(sign, thou_sep, frac_sep)

    def is_valid_number(self, sample: str, /, raise_on_fail: bool = False):
        """Check if the given number conforms to the format"""
        # if not all([c in "+-.,'_0123456789" for c in sample]):
        #     return False
        try:
            sample_format = NumberFormat.from_format(sample)
            if (sample_format.frac_sep, sample_format.thou_sep) == (self.thou_sep, ""):
                sample_format.frac_sep, sample_format.thou_sep = self.frac_sep, self.thou_sep

        except ValueError as e:
            if raise_on_fail:
                raise ValueError(f"Fractional separator not matched in {sample}: {e}")
            return False

        if sample_format.is_integer:
            return True

        # we expect the same fractional seperator but accept an integer number
        if sample_format.frac_sep and (sample_format.frac_sep != self.frac_sep):
            if raise_on_fail:
                raise ValueError(f"Fractional separator mismatch: {self.frac_sep} != {sample_format.frac_sep}")
            return False

        # numbers smaller than 1000 will not contain a thousands separator
        if sample_format.thou_sep and (sample_format.thou_sep != self.thou_sep):
            if raise_on_fail:
                raise ValueError(f"Thousands separator mismatch: {self.thou_sep} != {sample_format.thou_sep}")
            return False

        # Relax a little on the sign thingy.
        # We want to keep tracvk of signs but won't enforce identical signs
        #
        # if sample_format.sign and not self.sign:
        #     return False

        # last check: there need to be exactly 3 digits betwenn two separators
        if self.thou_sep:
            if self.frac_sep and self.frac_sep in sample:
                full, frac = sample.replace("+", "").replace("-", "").split(self.frac_sep, 1)
            else:
                full, frac = sample.replace("+", "").replace("-", ""), ""
            full_parts = full.split(self.thou_sep)
            frac_parts = frac.split(self.thou_sep)

            if len(full_parts) > 1 and not all([len(p) == 3 for p in full_parts[1:]]):
                if raise_on_fail:
                    raise ValueError(f"Wrong number of digits left of {self.frac_sep}: {full_parts[1:]}")
                return False
            if len(frac_parts) > 1 and not all([len(p) == 3 for p in frac_parts[0:-1]]):
                if raise_on_fail:
                    raise ValueError(f"Wrong number of digits right of {self.frac_sep}: {frac_parts[0:-1]}")
                return False

        return True

    def normalize(self, number: str) -> str:
        """Converts the given number to a format that can be casted to float or decimal."""
        if not self.is_valid_number(number):
            raise ValueError(f"Number {number} does not conform to format {self.format}.")

        is_negative = "-" in number
        number = number.replace("+", "").replace("-", "").strip()
        if is_negative:
            number = "-" + number
        if self.thou_sep:
            number = number.replace(self.thou_sep, "")
        if self.frac_sep:
            number = number.replace(self.frac_sep, ".")

        return number
