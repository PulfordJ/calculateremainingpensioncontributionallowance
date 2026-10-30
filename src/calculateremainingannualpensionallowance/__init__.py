from dataclasses import dataclass

CARRY_FORWARD_YEARS = 3


def apply_contributions(annual_allowances, contributions):
    """
    Uses each year's contribution against the UK pension annual allowance.

    A contribution uses its own year's allowance first, then any unused allowance
    from the previous three tax years, oldest first, per HMRC's carry forward rules.

    :param annual_allowances: Annual allowance per year, ordered from oldest to newest.
    :param contributions: Contribution per year, ordered from oldest to newest.
    :return: (remaining, excess): the unused allowance left in each year, and the part of
        each year's contribution that no allowance covered, which the annual allowance
        charge applies to.
    """
    remaining = list(annual_allowances)
    excess = []

    for year_index, contribution in enumerate(contributions):
        # The current year first, then previous tax years from oldest to newest.
        for i in [year_index, *range(max(0, year_index - CARRY_FORWARD_YEARS), year_index)]:
            used = min(contribution, remaining[i])
            remaining[i] -= used
            contribution -= used
        excess.append(contribution)

    return remaining, excess


def calculate_remaining_allowance(annual_allowances, contributions):
    """Unused annual allowance left in each year, ordered from oldest to newest."""
    return apply_contributions(annual_allowances, contributions)[0]


@dataclass(frozen=True)
class YearResult:
    year: int
    allowance: float
    contribution: float
    unused: float
    excess: float


@dataclass(frozen=True)
class Forecast:
    target_year: int
    years: list[YearResult]
    # Unused allowance from each of the previous three years that the target year can use.
    carry_forward: dict[int, float]
    target_allowance: float

    @property
    def available(self):
        """How much can be paid in during the target year before the annual allowance charge."""
        return self.target_allowance + sum(self.carry_forward.values())


def forecast(allowances, contributions):
    """
    Forecasts the annual allowance available in the latest year given.

    :param allowances: Annual allowance by tax year (named by its starting year).
    :param contributions: Contribution by tax year, for the same years as allowances.
    """
    years = sorted(allowances)
    if sorted(contributions) != years:
        raise ValueError("allowances and contributions must cover the same tax years")
    if years != list(range(years[0], years[-1] + 1)):
        raise ValueError("tax years must be consecutive")

    target_year = years[-1]
    allowance_list = [allowances[y] for y in years]
    contribution_list = [contributions[y] for y in years]

    # What the earlier years leave over, before the target year uses any of it.
    remaining_before, _ = apply_contributions(allowance_list[:-1], contribution_list[:-1])
    previous_years = years[:-1][-CARRY_FORWARD_YEARS:]
    carry_forward = dict(zip(previous_years, remaining_before[-len(previous_years):]))

    remaining, excess = apply_contributions(allowance_list, contribution_list)
    return Forecast(
        target_year=target_year,
        years=[YearResult(*row) for row in zip(years, allowance_list, contribution_list, remaining, excess)],
        carry_forward=carry_forward,
        target_allowance=allowances[target_year],
    )
