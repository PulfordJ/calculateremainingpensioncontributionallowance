# Remaining Pension Annual Allowance Calculator

## Overview
Forecasts how much you can pay into UK pensions in a tax year without an annual allowance charge. It uses the year's own annual allowance plus unused allowance from the previous three tax years (HMRC's carry forward rule).

Tax years are named by the year they start: `2027` is 2027/28 (6 April 2027 to 5 April 2028).

## Features
- Built-in annual allowances from 2016/17 to 2027/28, from GOV.UK's [pension schemes rates](https://www.gov.uk/government/publications/rates-and-allowances-pension-schemes/pension-schemes-rates).
- Carry forward applied in HMRC's order: the current year's allowance first, then unused allowance from the previous three years, oldest first.
- Tapered annual allowance for years where you give your threshold and adjusted income.
- Flags any contribution that goes over the allowance and carry forward, because the annual allowance charge applies to it.

### 2027/28 is an assumption
HMRC hasn't published 2027/28 figures yet. The Autumn Budget on 28 October 2026 announced no change, so 2027/28 uses 2026/27's figures:
- £60,000 annual allowance.
- Tapering starts above £200,000 threshold income and £260,000 adjusted income, down to a minimum of £10,000.

Output marks 2027/28 with `*`. When HMRC publishes the figures, update `RULES` in `src/calculateremainingannualpensionallowance/allowances.py` and `PUBLISHED_UP_TO`.

## Usage
Everything runs through Nix, so you don't need Python or uv installed.

1. Copy the example and fill in your figures. `contributions.toml` is gitignored, so your numbers stay out of this public repo.
   ```sh
   cp contributions.example.toml contributions.toml
   ```
2. Run it:
   ```sh
   nix run
   ```

`contribution` is the total paid into all your defined contribution pensions in the tax year: your own contributions grossed up for basic-rate relief, plus salary sacrifice and employer contributions. Give at least the three years before the target year. Earlier years help when a later year went over its own allowance, because carry forward uses the oldest unused allowance first. Without earlier years, the forecast assumes they had nothing unused, which is the cautious answer.

To try other amounts without editing the file, use `--contribution YEAR=AMOUNT`. It overrides the file and can be repeated:
```sh
nix run -- --contribution 2026=40000            # what if I pay £40k in 2026/27?
nix run -- --contribution 2027=100000           # does a planned £100k in 2027/28 fit?
nix run -- other.toml --target 2026             # a different file and target year
```

Example output:
```
Tax year     Allowance     Paid in      Unused     Charged
2023/24        £60,000     £15,000     £45,000          £0
2024/25        £60,000     £20,000     £40,000          £0
2025/26        £60,000     £30,000     £30,000          £0
2026/27        £60,000     £25,000     £35,000          £0
2027/28*       £60,000          £0     £60,000          £0

Available to pay in during 2027/28: £165,000
  2027/28 allowance        £60,000
  unused from 2024/25      £40,000
  unused from 2025/26      £30,000
  unused from 2026/27      £35,000

* 2027/28: not yet published by HMRC, assumed unchanged from the latest published year.
```

## Library use
```python
from calculateremainingannualpensionallowance import forecast
from calculateremainingannualpensionallowance.allowances import annual_allowance

years = range(2024, 2028)
result = forecast(
    {y: annual_allowance(y) for y in years},
    {2024: 20000, 2025: 30000, 2026: 25000, 2027: 0},
)
print(result.available)  # 165000
```

## Development
Dependencies are managed with uv and locked in `uv.lock`. The flake builds them into a virtual environment with [uv2nix](https://github.com/pyproject-nix/uv2nix).

```sh
nix develop                    # shell with the venv and uv
pytest                         # tests, run against src/
nix flake check                # runs the tests in the Nix sandbox
```

After changing dependencies in `pyproject.toml`, update the lock file:
```sh
nix develop .#bootstrap --command uv lock
```

## License
This script is provided under the MIT License.
