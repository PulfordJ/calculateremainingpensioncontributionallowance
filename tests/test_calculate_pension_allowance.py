import pytest

from calculateremainingannualpensionallowance import apply_contributions, calculate_remaining_allowance, forecast
from calculateremainingannualpensionallowance.allowances import annual_allowance, tax_year_label
from calculateremainingannualpensionallowance.cli import build_forecast, main, parse_contribution

"""
([annual_allowances],
[contributions],
[expected_remaining_allowance])
"""
testdata = [
    ([40000, 40000, 40000, 40000],
     [0, 0, 0, 10000],
     [40000, 40000, 40000, 30000]),

    ([40000, 40000, 40000, 40000],
     [0, 0, 0, 50000],
     [30000, 40000, 40000, 0]),

    ( [40000, 40000, 40000, 40000, 60000, 60000, 60000],
      [0, 0, 0, 10000, 20000, 50000, 70000],
      [40000, 40000, 40000, 20000, 40000, 10000, 0])
]

@pytest.mark.parametrize("annual_allowances,contributions,expected_remaining_allowance", testdata)
def test_simple_annual_allowance(annual_allowances, contributions, expected_remaining_allowance):
    remaining_allowance = calculate_remaining_allowance(annual_allowances, contributions)
    assert remaining_allowance == expected_remaining_allowance


def test_excess_beyond_carry_forward_is_reported():
    remaining, excess = apply_contributions([40000] * 5, [0, 0, 0, 0, 180000])
    assert remaining == [40000, 0, 0, 0, 0]  # the first year is more than three years back
    assert excess == [0, 0, 0, 0, 20000]


def test_carry_forward_uses_oldest_year_first():
    remaining, excess = apply_contributions([60000] * 4, [0, 0, 0, 80000])
    assert remaining == [40000, 60000, 60000, 0]
    assert excess == [0, 0, 0, 0]


@pytest.mark.parametrize("year,expected", [(2016, 40000), (2022, 40000), (2023, 60000), (2026, 60000), (2027, 60000)])
def test_standard_annual_allowance(year, expected):
    assert annual_allowance(year) == expected


@pytest.mark.parametrize("threshold_income,adjusted_income,expected", [
    (199000, 300000, 60000),  # threshold income not over £200k: no taper
    (250000, 260000, 60000),  # adjusted income not over £260k: no taper
    (250000, 300000, 40000),
    (400000, 500000, 10000),  # floor
])
def test_tapered_annual_allowance_2027(threshold_income, adjusted_income, expected):
    assert annual_allowance(2027, threshold_income, adjusted_income) == expected


def test_tapered_annual_allowance_floor_before_2023():
    assert annual_allowance(2022, 300000, 500000) == 4000


def test_unknown_year_raises():
    with pytest.raises(KeyError):
        annual_allowance(2014)


def test_tax_year_label():
    assert tax_year_label(2027) == "2027/28"
    assert tax_year_label(2099) == "2099/00"


def test_forecast_2027():
    result = forecast(
        {2023: 60000, 2024: 60000, 2025: 60000, 2026: 60000, 2027: 60000},
        {2023: 90000, 2024: 20000, 2025: 30000, 2026: 25000, 2027: 0},
    )
    # 2023/24's excess has no history to use, so it is charged and nothing carries into 2024/25.
    assert result.carry_forward == {2024: 40000, 2025: 30000, 2026: 35000}
    assert result.available == 165000
    assert result.years[0].excess == 30000


def test_forecast_earlier_excess_uses_oldest_unused_first():
    # 2026/27 overspends by £50k: that comes from 2023/24 first, leaving 2024/25 intact for 2027/28.
    result = forecast(
        {2023: 60000, 2024: 60000, 2025: 60000, 2026: 60000, 2027: 60000},
        {2023: 0, 2024: 0, 2025: 60000, 2026: 110000, 2027: 0},
    )
    assert result.carry_forward == {2024: 60000, 2025: 0, 2026: 0}
    assert result.available == 120000


def test_forecast_rejects_gaps():
    with pytest.raises(ValueError):
        forecast({2024: 60000, 2026: 60000}, {2024: 0, 2026: 0})


def test_build_forecast_defaults_target_contribution_to_zero():
    result = build_forecast(2027, {2025: {"contribution": 10000}, 2026: {"contribution": 10000}})
    assert result.years[-1].contribution == 0
    assert result.available == 60000 + 50000 + 50000


def test_build_forecast_requires_every_year_before_target():
    with pytest.raises(ValueError, match="2025/26"):
        build_forecast(2027, {2024: {"contribution": 0}, 2026: {"contribution": 0}})


def test_build_forecast_allowance_override():
    result = build_forecast(2027, {2026: {"contribution": 0, "allowance": 10000}})
    assert result.carry_forward == {2026: 10000}


def test_parse_contribution():
    assert parse_contribution("2026=£25,000") == (2026, 25000)


def test_cli_with_file(tmp_path, capsys):
    path = tmp_path / "contributions.toml"
    path.write_text(
        "target_year = 2027\n"
        "[years.2024]\ncontribution = 20000\n"
        "[years.2025]\ncontribution = 30000\n"
        "[years.2026]\ncontribution = 25000\n"
    )
    assert main([str(path), "--contribution", "2027=100000"]) == 0
    out = capsys.readouterr().out
    assert "Available to pay in during 2027/28: £165,000" in out
    assert "leaves £65,000 to spare" in out
    assert "2027/28*" in out


def test_cli_rejects_unknown_setting(tmp_path, capsys):
    path = tmp_path / "contributions.toml"
    path.write_text("[years.2026]\ncontributions = 1\n")
    assert main([str(path)]) == 1
    assert "unknown setting" in capsys.readouterr().err
