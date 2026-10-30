import argparse
import sys
import tomllib
from pathlib import Path

from . import CARRY_FORWARD_YEARS, forecast
from .allowances import annual_allowance, is_projected, tax_year_label

DEFAULT_FILE = Path("contributions.toml")
YEAR_KEYS = {"contribution", "allowance", "threshold_income", "adjusted_income"}


def money(amount):
    return f"£{amount:,.0f}" if amount == int(amount) else f"£{amount:,.2f}"


def load_file(path):
    """Reads a contributions file into (target_year, {year: settings})."""
    with path.open("rb") as f:
        data = tomllib.load(f)

    unknown = set(data) - {"target_year", "years"}
    if unknown:
        raise ValueError(f"{path}: unknown setting(s) {', '.join(sorted(unknown))}")

    years = {}
    for key, settings in data.get("years", {}).items():
        if not key.isdigit():
            raise ValueError(f"{path}: [years.{key}] should be named by the year the tax year starts, e.g. [years.2026]")
        unknown = set(settings) - YEAR_KEYS
        if unknown:
            raise ValueError(f"{path}: [years.{key}] has unknown setting(s) {', '.join(sorted(unknown))}")
        not_numbers = [k for k, v in settings.items() if isinstance(v, bool) or not isinstance(v, (int, float))]
        if not_numbers:
            raise ValueError(f"{path}: [years.{key}] {', '.join(not_numbers)} should be a number")
        years[int(key)] = settings
    return data.get("target_year"), years


def parse_contribution(text):
    year, sep, amount = text.partition("=")
    if not sep:
        raise argparse.ArgumentTypeError(f"expected YEAR=AMOUNT, got {text!r}")
    try:
        return int(year), float(amount.replace(",", "").lstrip("£"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected YEAR=AMOUNT, got {text!r}") from None


def allowance_for(year, settings):
    if "allowance" in settings:
        return settings["allowance"]
    incomes = settings.keys() & {"threshold_income", "adjusted_income"}
    if len(incomes) == 1:
        raise ValueError(f"{tax_year_label(year)}: the taper needs both threshold_income and adjusted_income")
    try:
        return annual_allowance(year, settings.get("threshold_income"), settings.get("adjusted_income"))
    except KeyError as e:
        raise ValueError(f"{e.args[0]}; set allowance for that year in the file") from None


def build_forecast(target_year, years):
    years = {y: s for y, s in years.items() if y <= target_year}
    years.setdefault(target_year, {})
    first = min(years)
    missing = [y for y in range(first, target_year) if "contribution" not in years.get(y, {})]
    if missing:
        raise ValueError(f"No contribution given for {', '.join(map(tax_year_label, missing))}")

    allowances = {y: allowance_for(y, s) for y, s in years.items()}
    contributions = {y: s.get("contribution", 0) for y, s in years.items()}
    return forecast(allowances, contributions)


def report(result):
    target = result.target_year
    lines = [f"{'Tax year':<10}{'Allowance':>12}{'Paid in':>12}{'Unused':>12}{'Charged':>12}"]
    for row in result.years:
        label = tax_year_label(row.year) + ("*" if is_projected(row.year) else "")
        lines.append(
            f"{label:<10}{money(row.allowance):>12}{money(row.contribution):>12}"
            f"{money(row.unused):>12}{money(row.excess):>12}"
        )

    lines += ["", f"Available to pay in during {tax_year_label(target)}: {money(result.available)}"]
    lines.append(f"  {tax_year_label(target) + ' allowance':<22}{money(result.target_allowance):>10}")
    for year, unused in result.carry_forward.items():
        lines.append(f"  {'unused from ' + tax_year_label(year):<22}{money(unused):>10}")

    if len(result.carry_forward) < CARRY_FORWARD_YEARS:
        lines.append(
            f"  (no figures for years before {tax_year_label(result.years[0].year)}, "
            "so no carry forward from them is counted)"
        )

    planned = result.years[-1]
    if planned.contribution:
        lines.append("")
        if planned.excess:
            lines.append(
                f"The planned {money(planned.contribution)} goes {money(planned.excess)} over: "
                "the annual allowance charge applies to that."
            )
        else:
            lines.append(
                f"The planned {money(planned.contribution)} leaves "
                f"{money(result.available - planned.contribution)} to spare."
            )

    charged = [row for row in result.years[:-1] if row.excess]
    if charged:
        lines.append("")
        lines += [
            f"Warning: {tax_year_label(row.year)} went {money(row.excess)} over its allowance and carry forward."
            for row in charged
        ]

    projected = sorted({row.year for row in result.years if is_projected(row.year)})
    if projected:
        lines.append("")
        lines.append(
            f"* {', '.join(map(tax_year_label, projected))}: not yet published by HMRC, "
            "assumed unchanged from the latest published year."
        )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pension-allowance",
        description="Forecast how much UK pension annual allowance is available in a tax year, "
        "including carry forward from the previous three years. "
        "Tax years are named by the year they start: 2027 is 2027/28.",
    )
    parser.add_argument(
        "file", nargs="?", type=Path,
        help=f"TOML file of contributions by tax year (default: {DEFAULT_FILE} if it exists)",
    )
    parser.add_argument(
        "-t", "--target", type=int, metavar="YEAR",
        help="tax year to forecast (default: target_year from the file, else the latest year given)",
    )
    parser.add_argument(
        "-c", "--contribution", type=parse_contribution, action="append", default=[], metavar="YEAR=AMOUNT",
        help="a year's total contribution, overriding the file; repeat for more years",
    )
    args = parser.parse_args(argv)

    path = args.file or (DEFAULT_FILE if DEFAULT_FILE.exists() else None)
    try:
        target_year, years = load_file(path) if path else (None, {})
        for year, amount in args.contribution:
            years.setdefault(year, {})["contribution"] = amount
        if not years:
            parser.error(f"give a contributions file (none found at {DEFAULT_FILE}) or --contribution YEAR=AMOUNT")

        target_year = args.target or target_year or max(years)
        print(report(build_forecast(target_year, years)))
    except (OSError, ValueError) as e:
        print(f"pension-allowance: {e}", file=sys.stderr)
        return 1
    return 0
