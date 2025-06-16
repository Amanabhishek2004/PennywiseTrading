import numpy as np 

def CalculateCOE(beta=1, riskfreereturn=7.26, equityriskpremium=7.26):
    return (beta * equityriskpremium + riskfreereturn) / 100

def CalculateROE(shareholdersequity, netincome):
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
    if not EBIT or not INTEREST:
        return np.nan
    yearly = [
        ebit / interest if ebit and interest else np.nan
        for ebit, interest in zip(EBIT, INTEREST)
    ]
    return np.nanmedian(yearly)

def CalculateFCFF(operatingCashflow, interest, taxrate, capex):
    if not all([operatingCashflow, interest, taxrate, capex]):
        return np.nan
    yearly = [
        operatingCashflow[i] + interest[i] * (1 - taxrate[i]) - capex[i]
        if i < len(operatingCashflow) and i < len(interest) and i < len(taxrate) and i < len(capex)
        and operatingCashflow[i] is not None and interest[i] is not None
        and taxrate[i] is not None and capex[i] is not None
        else np.nan
        for i in range(len(operatingCashflow))
    ]
    return np.nanmedian(yearly)

def CalculateROIC(InvestedCapital, Earnings):
    if not InvestedCapital or not Earnings:
        return np.nan
    yearly = [
        earn / capital if capital and earn else np.nan
        for capital, earn in zip(InvestedCapital, Earnings)
    ]
    return np.nanmedian(yearly)

def CalculateRORE(changeinearnings, reinvestedearnings):
    print("changeinearnings", changeinearnings)
    print("reinvestedearnings", reinvestedearnings)
    if not reinvestedearnings:
        return np.nan
    return np.nanmedian([
        change / reinvestedearnings
        if reinvestedearnings else np.nan
        for change in changeinearnings
    ])

def CalculateCOI(interest, debt):
    if not interest or not debt:
        return np.nan
    yearly = [
        int_val / debt_val if int_val and debt_val else np.nan
        for int_val, debt_val in zip(interest, debt)
    ]
    return np.nanmedian(yearly)

def CalculateWACC(CostOfDebt, CostOfEquity, Debt, Equity, Taxrate):
    CostOfDebt = CostOfDebt if not np.isnan(CostOfDebt) else 0
    CostOfEquity = CostOfEquity if not np.isnan(CostOfEquity) else 0
    Debt = Debt if not np.isnan(Debt) else 0
    Equity = Equity if not np.isnan(Equity) else 0
    Taxrate = Taxrate if not np.isnan(Taxrate) else 0

    TotalCapital = Debt + Equity
    TotalCapital = TotalCapital if TotalCapital != 0 else 1e-10  # Avoid division by zero

    return (
        CostOfDebt * (1 - Taxrate) * (Debt / TotalCapital) +
        CostOfEquity * (Equity / TotalCapital)
    )

def WACCcalculator(stock_dict):
    # Extract relevant values
    coe = stock_dict.get("COE", 0)
    cod = stock_dict.get("COD", 0)
    equity = stock_dict.get("marketCap", 0)
    
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
