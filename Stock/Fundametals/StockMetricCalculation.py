import numpy as np 

def CalculateCOE(beta=1, riskfreereturn=7.26, equityriskpremium=7.26):
    return (beta * equityriskpremium + riskfreereturn) / 100

def CalculateROE(equitycapital , reserves, netincome):

    shareholdersequity = [
        equity + reserve if equity and reserve else np.nan
        for equity, reserve in zip(equitycapital, reserves)
    ]
    if not shareholdersequity or not netincome:
        return np.nan
    yearly = [
        income / equity if equity and income else np.nan
        for equity, income in zip(shareholdersequity, netincome)
    ]
    return np.nanmedian(yearly)

def CalculateATR(Assets, Revenue):
     
    if not Assets or not Revenue:
        return np.nan
    yearly = [
        asset / rev if asset and rev else np.nan
        for asset, rev in zip(Assets, Revenue)
    ]
    return np.nanmedian(yearly)

def CalculateICR(EBIT, INTEREST):

    # Convert inputs to lists of floats
    if not EBIT or not INTEREST:
        return np.nan

    # Calculate yearly ICR
    yearly = [
        float(ebit) / float(interest) if ebit and interest and interest != 0 else np.nan
        for ebit, interest in zip(EBIT, INTEREST)
    ]

    # Adjust yearly values based on tax rate


    return np.nanmedian(yearly)


import numpy as np

def CalculateFCFF(operatingCashflow, interest, taxrate, fa, wc):

    def safe_to_float(value):
        """Convert value to float if possible, otherwise return NaN."""
        try:
            if isinstance(value, str) and value.strip() == "":
                return np.nan
            return float(value)
        except (ValueError, TypeError):
            return np.nan
    
    print(operatingCashflow , interest , taxrate , fa, wc )
    # Convert inputs to NumPy arrays and replace NaNs with 0
    fa = np.nan_to_num(np.array([safe_to_float(x) for x in fa], dtype=float), nan=0.0)
    wc = np.nan_to_num(np.array([safe_to_float(x) for x in wc], dtype=float), nan=0.0)
    taxrate = np.nan_to_num(np.array([safe_to_float(x) for x in taxrate], dtype=float), nan=0.0)
    interest = np.nan_to_num(np.array([safe_to_float(x) for x in interest], dtype=float), nan=0.0)
    operatingCashflow = np.nan_to_num(np.array([safe_to_float(x) for x in operatingCashflow], dtype=float), nan=0.0)

    # Handle length mismatch using padding
    max_length = max(len(fa), len(wc))
    fa = np.pad(fa, (0, max_length - len(fa)), constant_values=0)
    wc = np.pad(wc, (0, max_length - len(wc)), constant_values=0)

    # Calculate differences with padding
    fa_diff = np.diff(fa, prepend=fa[0])
    wc_diff = np.diff(wc, prepend=wc[0])

    # Calculate CapEx
    capex = [float(-fa_diff[i] - wc_diff[i]) for i in range(len(fa_diff))]

    # Calculate FCFF
    fcff = [
        float(operatingCashflow[i] + interest[i] * (1 - (taxrate[i]/100)) - capex[i])
        for i in range(len(operatingCashflow))
    ]

    # Return the results
    return capex, fcff


def CalculateROIC(ROIC):
    return np.nanmedian(ROIC)



def CalculateCOI(interest, debt):

    if not interest or not debt:
        return np.nan
    yearly = [
        int_val / debt_val if int_val and debt_val else np.nan
        for int_val, debt_val in zip(interest, debt)
    ]
    return np.nanmedian(yearly)

def CalculateWACC(CostOfDebt, beta, Debt, Equity, Taxrate):

    def safe_to_float(value):
        """Convert value to float if possible, otherwise return NaN."""
        try:
            if isinstance(value, str) and value.strip() == "":
                return np.nan
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    Debt = np.array([safe_to_float(x) for x in np.atleast_1d(Debt)], dtype=float)
    Equity = np.array([safe_to_float(x) for x in np.atleast_1d(Equity)], dtype=float)
    Taxrate = np.array([safe_to_float(x) for x in np.atleast_1d(Taxrate)], dtype=float)

    # Handle invalid CostOfDebt or beta
    CostOfDebt = safe_to_float(CostOfDebt)
    coe = CalculateCOE(beta)
    CostOfEquity = coe if not np.isnan(coe) else 0

    # Debug input lengths
    print(f"Debt length: {len(Debt)}, Equity length: {len(Equity)}, Taxrate length: {len(Taxrate)}")

    # Align lengths of all input arrays
    max_length = max(len(Debt), len(Equity), len(Taxrate))
    Debt = np.pad(Debt, (0, max_length - len(Debt)), constant_values=np.nan)
    Equity = np.pad(Equity, (0, max_length - len(Equity)), constant_values=np.nan)
    Taxrate = np.pad(Taxrate, (0, max_length - len(Taxrate)), constant_values=np.nan)

    # Replace NaN in arrays with zeros
    Debt = np.nan_to_num(Debt, nan=0)
    Equity = np.nan_to_num(Equity, nan=0)
    Taxrate = np.nan_to_num(Taxrate, nan=0)

    # Calculate total capital
    TotalCapital = Debt + Equity
    TotalCapital = np.where(TotalCapital == 0, 1e-10, TotalCapital)  # Avoid division by zero

    # Calculate WACC
    WACC = (
        CostOfDebt * (1 - Taxrate / 100) * (Debt / TotalCapital) +
        CostOfEquity * (Equity / TotalCapital)
    )

    # Return scalar WACC if inputs are scalar
    if WACC.size == 1:
        return WACC.item()

    # Return median WACC for array inputs
    return np.nanmedian(WACC)




def convert_to_list(data_string):
    if data_string is None:
        return []

    if isinstance(data_string, (int, float)):
        return [float(data_string)]

    elif isinstance(data_string, str):
        cleaned_data = data_string.strip().replace("[", "").replace("]", "").replace("'", "").replace("%", "")
        elements = cleaned_data.split(",")
        result = []

        for element in elements:
            element = element.strip()
            if element == "":
                element = "0"
            try:
                number = float(element.replace(",", ""))
                result.append(number)
            except ValueError:
                result.append(element)
        return result

    else:
        return []


def calculate_growth_with_rolling(data):
    data = convert_to_list(data)
    try:
        data = np.array(data, dtype=float)
    except ValueError:
        return 0.0

    # Remove NaN values
    data = data[~np.isnan(data)]

    # Check for sufficient data points
    if len(data) < 2:
        return 0.0

    # Calculate percentage changes, avoiding division by zero
    growth_rates = []
    for i in range(1, len(data)):
        if data[i - 1] != 0:  # Check if the denominator is not zero
            growth_rate = ((data[i] - data[i - 1]) / data[i - 1]) * 100
            growth_rates.append(growth_rate)

    # If no valid growth rates were calculated, return 0
    if not growth_rates:
        return 0.0

    # Calculate the average growth rate
    average_growth = np.nanmean(growth_rates)  # Handle cases with NaN in differences

    return average_growth


def WACCcalculator(stock_dict):
    # Extract relevant values
    coe = stock_dict.get("beta", 0)
    cod = stock_dict.get("COD", 0)
    equity = stock_dict.get("regular", 0)
    
    tax_rates = stock_dict.get("Tax Rate For Calcs", [])
    interest_expense = stock_dict.get("Interest Expense", [])

    tax_rate = np.nanmedian(tax_rates) if tax_rates else 0
    debt = np.nanmedian(interest_expense) if interest_expense else 0

    cost_of_equity = coe if not np.isnan(coe) else 0
    cost_of_debt = cod if not np.isnan(cod) else 0
    equity_value = equity if not np.isnan(equity) else 0

    return CalculateWACC(
        cost_of_debt,
        cost_of_equity,
        debt,
        equity_value,
        tax_rate
    )


def calculate_working_capital_from_days(days, sales):

    def safe_to_float(value):
        """Convert value to float if possible, otherwise return NaN."""
        try:
            # Treat empty strings or whitespace as NaN
            if isinstance(value, str) and value.strip() == "":
                return np.nan
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    if not isinstance(days, list) or not isinstance(sales, list):
        raise ValueError("Both 'days' and 'sales' must be lists.")
    
    # Convert all values to float, handling invalid inputs
    days = [safe_to_float(x) for x in days]
    sales = [safe_to_float(x) for x in sales]
    
    # Determine the minimum length to calculate
    min_length = min(len(days), len(sales))
    
    # Calculate working capital for the common length
    working_capital = [
        (days[i] * sales[i]) / 365 if not np.isnan(days[i]) and not np.isnan(sales[i]) else np.nan
        for i in range(min_length)
    ]
    
    # Fill remaining indices with NaN for the longer list
    if len(days) > min_length:
        working_capital.extend([np.nan] * (len(days) - min_length))
    elif len(sales) > min_length:
        working_capital.extend([np.nan] * (len(sales) - min_length))

    return working_capital

