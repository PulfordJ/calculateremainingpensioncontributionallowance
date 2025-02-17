def calculate_remaining_allowance(latest_year, annual_allowances, contributions):
    """
    Calculates the remaining pension annual allowance in the UK.

    :param annual_allowances: List of annual allowances for the last X years, ordered from oldest to newest.
    :param contributions: List of contributions made in the last X years, ordered from oldest to newest.
    :return: Remaining allowance after considering contributions and 3 previous tax year carry forward rules.
    """
    remaining_allowances = annual_allowances[:]

    for year_index in range(len(contributions)):
        year = latest_year - len(annual_allowances) + 1 + year_index
        contribution_to_process = contributions[year_index]

        if contribution_to_process <= remaining_allowances[year_index]:
            remaining_allowances[year_index] -= contribution_to_process
        else:
            # TODO if first 3 elements in contributions are above annual allowance ask user for more data from previous years.
            contribution_to_process -= remaining_allowances[year_index]
            remaining_allowances[year_index] = 0
            # Attempt to use previous tax years, from oldest to newest per HMRC guidelines.
            for i in range(max(0, year_index-3), year_index):
                if contribution_to_process <= remaining_allowances[i]:
                    remaining_allowances[i] -= contribution_to_process
                    break
                else:
                    contribution_to_process -= remaining_allowances[i]
                    remaining_allowances[i] = 0

    return remaining_allowances


if __name__ == "__main__":
    # Example usage
    latest_year = 2025
    annual_allowances = [40000, 40000, 40000, 40000, 60000, 60000, 60000]  # Example annual allowances per year
    contributions = [0, 0, 0, 10000, 20000, 50000, 70000]  # Example contributions per year


    remaining_allowance = calculate_remaining_allowance(latest_year, annual_allowances, contributions)
    print(f"Remaining Allowances: {remaining_allowance}")


