import pytest

from calculateremainingannualpensionallowance import calculate_remaining_allowance

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
    latest_year = 2025

    remaining_allowance = calculate_remaining_allowance(latest_year, annual_allowances, contributions)
    assert remaining_allowance == expected_remaining_allowance

    latest_year = 2025
