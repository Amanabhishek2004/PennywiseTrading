import numpy as np 

def CalculateCOE(beta=1, riskfreereturn=7.26, equityriskpremium=7.26):
    return (beta * equityriskpremium + riskfreereturn) / 100

import numpy as np

def CalculateROE(equitycapital, reserves, netincome):
    def safe_float(x):
        try:
            if isinstance(x, str):
                x = x.replace(",", "").strip()
                if x == "":
                    return np.nan
            return float(x)
        except (ValueError, TypeError):
            return np.nan

    equitycapital = [safe_float(x) for x in equitycapital]
    reserves = [safe_float(x) for x in reserves]
    netincome = [safe_float(x) for x in netincome]

    shareholdersequity = [
        (equity if equity is not None else 0) +
        (reserve if reserve is not None else 0)
        for equity, reserve in zip(equitycapital, reserves)
    ]

    yearly = [
        (income / equity) if equity not in (0, np.nan) and not np.isnan(equity) and income is not None else np.nan
        for equity, income in zip(shareholdersequity, netincome)
    ]

    return np.nanmedian(yearly), yearly

import numpy as np

def calculate_gross_margin_array(operating_revenue, operating_profit, operating_expenses):
    """
    Calculate Gross Margin (%) for arrays/lists of inputs.
    Returns a list of gross margin percentages (rounded to 2 decimals).
    """

    def safe_float(x):
        try:
            if isinstance(x, str):
                x = x.replace(",", "").strip()
                if x == "":
                    return np.nan
            return float(x)
        except (ValueError, TypeError):
            return np.nan

    # Convert to float arrays
    rev = np.array([safe_float(x) for x in operating_revenue], dtype=float)
    op_profit = np.array([safe_float(x) for x in operating_profit], dtype=float)
    op_exp = np.array([safe_float(x) for x in operating_expenses], dtype=float)
    print(f"Revenue: {rev}, Operating Profit: {op_profit}, Operating Expenses: {op_exp}")
    # Make lengths match
    max_len = max(len(rev), len(op_profit), len(op_exp))
    def pad(arr, length):
        return np.pad(arr, (0, length - len(arr)), constant_values=np.nan)

    rev = pad(rev, max_len)
    op_profit = pad(op_profit, max_len)
    op_exp = pad(op_exp, max_len)

    # Calculate gross profit
    gross_profit = op_profit + op_exp 
    print(f"Gross Profit: {gross_profit}")

    # Calculate gross margin safely
    gross_margin = np.where(rev != 0, (gross_profit / rev) * 100, np.nan)

    return np.round(gross_margin, 2).tolist()



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



def CalculateFCFF(operatingCashflow, interest, taxrate, fa, wc):
    """
    Calculate CapEx and FCFF.
    Returns:
        capex_list, fcff_list
    """
    def safe_to_float(value):
        """Convert value to float if possible, otherwise NaN."""
        try:
            if isinstance(value, str) and value.strip() == "":
                return np.nan
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    # Convert all inputs to float lists with NaN → 0.0
    arrays = {}
    for name, seq in (("fa", fa), ("wc", wc), ("taxrate", taxrate),
                      ("interest", interest), ("ocf", operatingCashflow)):
        arr = [safe_to_float(x) for x in seq]
        arrays[name] = [0.0 if np.isnan(v) else v for v in arr]

    # Determine required lengths
    cap_len = max(len(arrays["fa"]), len(arrays["wc"]))
    fcff_len = max(len(arrays["ocf"]), len(arrays["interest"]),
                   len(arrays["taxrate"]), cap_len)

    # Pad lists
    def pad_to(lst, length):
        return lst + [0.0] * (length - len(lst))

    fa   = pad_to(arrays["fa"], cap_len)
    wc   = pad_to(arrays["wc"], cap_len)
    ocf  = pad_to(arrays["ocf"], fcff_len)
    irt  = pad_to(arrays["interest"], fcff_len)
    txr  = pad_to(arrays["taxrate"], fcff_len)

    # Compute CapEx
    fa_diff = [fa[i] - fa[i-1] if i > 0 else 0.0 for i in range(len(fa))]
    wc_diff = [wc[i] - wc[i-1] if i > 0 else 0.0 for i in range(len(wc))]
    capex = [-fa_diff[i] - wc_diff[i] for i in range(len(fa))]

    # Compute FCFF
    capex_padded = pad_to(capex, fcff_len)
    fcff = [
        ocf[i] + irt[i] * (1 - txr[i] / 100.0) - capex_padded[i]
        for i in range(fcff_len)
    ]

    return capex, fcff



import numpy as np

def calculate_net_profit_margin_array(operating_revenue, net_income):
    """
    Calculate Net Profit Margin (%) for arrays/lists of inputs.
    Returns a list of net profit margin percentages (rounded to 2 decimals).
    """

    def safe_float(x):
        try:
            if isinstance(x, str):
                x = x.replace(",", "").strip()
                if x == "":
                    return np.nan
            return float(x)
        except (ValueError, TypeError):
            return np.nan

    # Convert to float arrays
    rev = np.array([safe_float(x) for x in operating_revenue], dtype=float)
    net_inc = np.array([safe_float(x) for x in net_income], dtype=float)

    # Pad to same length
    max_len = max(len(rev), len(net_inc))
    def pad(arr, length):
        return np.pad(arr, (0, length - len(arr)), constant_values=np.nan)

    rev = pad(rev, max_len)
    net_inc = pad(net_inc, max_len)

    # Calculate net profit margin safely
    net_profit_margin = np.where(rev != 0, (net_inc / rev) * 100, np.nan)

    return np.round(net_profit_margin, 2).tolist()

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


import numpy as np


def calculate_receivables_from_days(receivable_days, sales):
    """
    Calculate receivables using:
    Receivables = (Receivable Days * Sales) / 365
    """
    def safe_to_float(value):
        try:
            if isinstance(value, str) and value.strip() == "":
                return np.nan
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    receivable_days = [safe_to_float(x) for x in receivable_days]
    sales = [safe_to_float(x) for x in sales]

    min_length = min(len(receivable_days), len(sales))
    receivables = []
    for i in range(min_length):
        if np.isnan(receivable_days[i]) or np.isnan(sales[i]):
            receivables.append(np.nan)
        else:
            receivables.append((receivable_days[i] * sales[i]) / 365)

    return receivables


def calculate_working_capital(total_liabilities, total_debt, current_assets):
    """
    Calculate working capital using:
    Current Liabilities = Total Liabilities - Total Debt
    Working Capital = Current Assets - Current Liabilities
    """
    def safe_to_float(value):
        try:
            if isinstance(value, str) and value.strip() == "":
                return np.nan
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    # Convert inputs to lists of floats
    total_liabilities = [safe_to_float(x) for x in total_liabilities]
    total_debt = [safe_to_float(x) for x in total_debt]
    current_assets = [safe_to_float(x) for x in current_assets]

    # Ensure all lists have the same length
    min_length = min(len(total_liabilities), len(total_debt), len(current_assets))
    
    working_capital = []
    for i in range(min_length):
        if np.isnan(total_liabilities[i]) or np.isnan(total_debt[i]) or np.isnan(current_assets[i]):
            working_capital.append(np.nan)
        else:
            current_liabilities = total_liabilities[i] - total_debt[i]
            wc = current_assets[i] - current_liabilities
            working_capital.append(wc)
    
    return working_capital
