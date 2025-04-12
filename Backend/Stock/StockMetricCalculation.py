import numpy as np 

def CalculateCOE(beta = 1, riskfreereturn=7.26, equityriskpremium=7.26):
    return (beta * equityriskpremium + riskfreereturn)/100

def CalculateROE(shareholdersequity, netincome):
    yearly = []
    for equity , income in zip(shareholdersequity , netincome):
        if income :
            yearly.append(income / equity)
        else:
            yearly.append(np.nan)
    return np.nanmedian(yearly)

def CalculateATR(Assets, Revenue):
    yearly = []
    for asset, rev in zip(Assets, Revenue):
        if asset and rev:
            yearly.append(asset / rev)
        else:
            yearly.append(np.nan)
    return np.nanmedian(yearly)

def CalculateICR(EBIT, INTEREST):
    yearly = []
    for ebit, interest in zip(EBIT, INTEREST):
        if ebit and interest:
            yearly.append(ebit / interest)
        else:
            yearly.append(np.nan)
    return np.nanmedian(yearly)

def CalculateFCFF(operatingCashflow, interest, taxrate, capex):
    yearly = []
    for i in range(len(operatingCashflow)):
        if (
            i < len(interest) and i < len(taxrate) and i < len(capex)
            and operatingCashflow[i] is not None and interest[i] is not None
            and taxrate[i] is not None and capex[i] is not None
        ):
            yearly.append(operatingCashflow[i] + interest[i] * (1 - taxrate[i]) - capex[i])
        else:
            yearly.append(np.nan)
    return np.nanmedian(yearly)

def CalculateROIC(InvestedCapital, Earnings):
    yearly = []
    for capital, earn in zip(InvestedCapital, Earnings):
        if capital and earn:
            yearly.append(earn / capital)
        else:
            yearly.append(np.nan)
    return np.nanmedian(yearly)

def CalculateRORE(changeinearnings, reinvestedearnings):
    if reinvestedearnings:  # Avoid division by zero or None
        return np.nanmedian(changeinearnings / reinvestedearnings)
    else:
        return np.nan

def CalculateCOI(interest, debt):
    print("Intrest" , interest)

    yearly = []
    for int_val, debt_val in zip(interest, debt):
        if int_val and debt_val:
            yearly.append(int_val / debt_val)
        else:
            yearly.append(np.nan)
    return np.nanmedian(yearly)

def CalculateWACC(CostOfDebt, CostOfEquity, Debt, Equity, Taxrate):
    CostOfDebt = CostOfDebt if not np.isnan(CostOfDebt) else 0
    CostOfEquity = CostOfEquity if not np.isnan(CostOfEquity) else 0
    Debt = Debt if not np.isnan(Debt) else 0
    Equity = Equity if not np.isnan(Equity) else 0
    Taxrate = Taxrate if not np.isnan(Taxrate) else 0

    TotalCapital = Debt + Equity
    if TotalCapital == 0:
        TotalCapital = 1e-10  # Avoid division by zero

    return (
        CostOfDebt * (1 - Taxrate) * (Debt / TotalCapital) +
        CostOfEquity * (Equity / TotalCapital)
    )



def WACCcalculator(stock_dict):
    # Extract relevant values
    coe = stock_dict.get("COE", 0)  # Cost of Equity in %
    cod = stock_dict.get("COD", 0)        # Cost of Debt
    equity = stock_dict.get("marketCap", 0)  # Market Capitalization (Equity)
    
    # Handle nested lists for tax rate and interest expense
    tax_rates = stock_dict.get("Tax Rate For Calcs", [])
    interest_expense = stock_dict.get("Interest Expense", [])

    # Take median to reduce multiple-year data to single values
    tax_rate = np.nanmedian(tax_rates) if len(tax_rates) else 0
    debt = np.nanmedian(interest_expense) if len(interest_expense) else 0

    # Handle missing or invalid values
    cost_of_equity = coe if not np.isnan(coe) else 0
    cost_of_debt = cod if not np.isnan(cod) else 0
    equity_value = equity if not np.isnan(equity) else 0
    total_capital = debt + equity_value if (debt + equity_value) != 0 else 1e-10

    # Calculate and return WACC
    return CalculateWACC(
        cost_of_debt,
        cost_of_equity,
        debt,
        equity_value,
        tax_rate
    )

