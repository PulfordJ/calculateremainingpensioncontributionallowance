# Remaining Pension Annual Allowance Calculator

## Overview
This script calculates the remaining pension annual allowance in the UK by considering annual allowances, contributions, and the HMRC's three-year carry-forward rule. It helps determine how much of the pension allowance remains available for future contributions.

## Features
- Takes into account annual allowances and contributions for multiple years.
- Automatically applies HMRC's carry-forward rule (up to three previous tax years) if contributions exceed the current year's allowance.
- Prints the remaining allowances after all contributions are processed.

## How It Works
1. **Inputs**:
   - `latest_year`: The most recent tax year for which contributions are being calculated.
   - `annual_allowances`: A list of annual allowances per year, ordered from oldest to newest.
   - `contributions`: A list of contributions made per year, ordered from oldest to newest.
2. The function iterates through contributions and deducts them from the respective year's allowance.
3. If a year's contribution exceeds the available allowance, the script attempts to use unused allowances from the previous three tax years.
4. The final remaining allowances are printed as output.

## Example Usage
```python
latest_year = 2025
annual_allowances = [40000, 40000, 40000, 40000, 60000, 60000, 60000]  # Example allowances per year
contributions = [0, 0, 0, 10000, 20000, 50000, 70000]  # Example contributions per year

remaining_allowance = calculate_remaining_allowance(latest_year, annual_allowances, contributions)
print(f"Remaining Allowances: {remaining_allowance}")
```

## Installation & Running with Poetry
### Prerequisites
Ensure you have Poetry installed. If not, install it using:
```sh
pip install poetry
```

### Running the Script
1. Clone the repository or copy the script to a Python file (e.g., `pension_calculator.py`).
2. Navigate to the script directory and create a Poetry environment:
   ```sh
   poetry install
   ```
3. Run the script using Poetry:
   ```sh
   poetry run python .\src\calculateremainingannualpensionallowance\__init__.py
   ```

## Future Improvements
- Add user input functionality for dynamic calculations.
- Implement logging for better debugging.
- Error if we need earlier tax years to make a true determination of remaining allowances (if the first 3 tax years go over the annual allowance.)

## License
This script is provided under the MIT License.

