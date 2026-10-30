"""UK pension annual allowance figures by tax year.

A tax year is named by the calendar year it starts in, so 2027 is
6 April 2027 to 5 April 2028.

Source: GOV.UK "Rates and allowances: pension schemes", which covers up to
2026/27. Years after PUBLISHED_UP_TO are assumptions, not HMRC figures.
"""

from dataclasses import dataclass

PUBLISHED_UP_TO = 2026


@dataclass(frozen=True)
class Rules:
    annual_allowance: int
    # The taper applies only when both incomes are above these limits.
    taper_threshold_income: int
    taper_adjusted_income: int
    minimum_tapered_allowance: int


RULES = {
    **dict.fromkeys(range(2016, 2020), Rules(40_000, 110_000, 150_000, 10_000)),
    **dict.fromkeys(range(2020, 2023), Rules(40_000, 200_000, 240_000, 4_000)),
    **dict.fromkeys(range(2023, 2027), Rules(60_000, 200_000, 260_000, 10_000)),
    # Not yet published. The Autumn Budget on 28 October 2026 announced no
    # change, so assume 2026/27's figures carry on.
    2027: Rules(60_000, 200_000, 260_000, 10_000),
}


def tax_year_label(year):
    return f"{year}/{(year + 1) % 100:02d}"


def is_projected(year):
    return year > PUBLISHED_UP_TO


def annual_allowance(year, threshold_income=None, adjusted_income=None):
    """The annual allowance for a tax year, tapered if both incomes are given and above the limits."""
    if year not in RULES:
        known = f"{tax_year_label(min(RULES))} to {tax_year_label(max(RULES))}"
        raise KeyError(f"No annual allowance known for {tax_year_label(year)} (known: {known})")
    rules = RULES[year]

    if threshold_income is None or adjusted_income is None:
        return rules.annual_allowance
    if threshold_income <= rules.taper_threshold_income or adjusted_income <= rules.taper_adjusted_income:
        return rules.annual_allowance

    # Reduced by £1 for every £2 of adjusted income over the limit.
    tapered = rules.annual_allowance - (adjusted_income - rules.taper_adjusted_income) / 2
    return max(tapered, rules.minimum_tapered_allowance)
