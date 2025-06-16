companyswholedata_rowwise = {
    "beta"  : None,
    "marketCap"  : None,
    "twoHundredDayAverage" : None,
    "fiftyDayAverage"  : None,
    "grossProfits" : None,
    "trailingPE"  : None,
    "trailingEps" : None,
    "epsTrailingTwelveMonths" : None,
    "forwardPE"  : None,
    "totalCash"  : None,
    "debtToEquity" : None,
    "operatingMargins" : None,
    "epsForward" : None,
    "grossMargins" : None,
    "bookValue" : None,
    "ebitda" : None,
    "trailingAnnualDividendYield" : None,
    "dividendYield" : None,
    "dividendRate" : None,
    "fiveYearAvgDividendYield" : None,
    "sector" : None,
    "payoutRatio" : None,
    "enterpriseToEbitda" : None ,
    "Capital Expenditure Reported" : None,                 
    "Free Cash Flow" : None,
    "Operating Cash Flow" : None,
    "Net Income From Continuing Operations" : None,
    "Net Tangible Assets"  : None,
    "Invested Capital" : None,
    "Retained Earnings" : None,
    "Total Assets" : None,
    "Current Debt" : None,
    "Stockholders Equity" : None,
    "EBIT" : None,
    "Tax Rate For Calcs" : None,
    "EBITDA" : None,
    "Total Expenses" : None,
    "Net Income" : None,
    "Basic EPS" : None,
    "Operating Revenue" : None,
    "Operating Expense" : None,
    'Interest Expense': None , 
    "tickers" : None
}



companysinfo = [
    "beta" ,
    "marketCap" ,
    "twoHundredDayAverage",
    "fiftyDayAverage" ,
    "grossProfits",
    "trailingPE" ,
    "trailingEps",
    "epsTrailingTwelveMonths",
    "forwardPE" ,
    "totalCash" ,
    "debtToEquity",
    "operatingMargins",
    "epsForward",
    "grossMargins",
    "bookValue",
    "ebitda",
    "trailingAnnualDividendYield",
    "dividendYield",
    "dividendRate",
    "fiveYearAvgDividendYield",
    "sector",
    "payoutRatio",
    "enterpriseToEbitda"
]

companyscashflow = [
    "Capital Expenditure"   ,                
    "Free Cash Flow",
    "Operating Cash Flow" ,
    "Net Income From Continuing Operations",
    "Net Investment Purchase And Sale"
]

companysbalancesheet = [
    "Net Tangible Assets"  ,
    "Invested Capital" ,
    "Retained Earnings"  ,
    "Total Assets" ,
    "Current Debt" ,
    "Stockholders Equity" 
]

companysfinancialsinfo = [
    "EBIT",
    "Tax Rate For Calcs",
    "EBITDA",
    "Total Expenses",
    "Net Income",
    "Basic EPS",
    "Operating Revenue" ,
    "Operating Expense" ,
    "Interest Expense",
]


columns = [
    "beta"  ,
    "marketCap"  ,
    "twoHundredDayAverage",
    "fiftyDayAverage" ,
    "grossProfits",
    "trailingPE"  ,
    "trailingEps" ,
    "epsTrailingTwelveMonths" ,
    "forwardPE"  ,
    "totalCash"  ,
    "debtToEquity" ,
    "operatingMargins",
    "epsForward" ,
    "grossMargins",
    "bookValue" ,
    "ebitda" ,
    "trailingAnnualDividendYield" ,
    "dividendYield" ,
    "dividendRate" ,
    "fiveYearAvgDividendYield" ,
    "sector" ,
    "payoutRatio" ,
    "enterpriseToEbitda" ,
    "Capital Expenditure Reported" ,                 
    "Free Cash Flow" ,
    "Operating Cash Flow" ,
    "Net Income From Continuing Operations" ,
    "Net Tangible Assets"  ,
    "Invested Capital" ,
    "Retained Earnings" ,
    "Total Assets" ,
    "Current Debt" ,
    "Stockholders Equity" ,
    "EBIT" ,
    "Tax Rate For Calcs" ,
    "EBITDA" ,
    "Total Expenses" ,
    "Net Income" ,
    "Basic EPS" ,
    "Operating Revenue" ,
    "Operating Expense" ,
    "Interest Expense"
    ]


CAGR_COLUMNS = ['Free Cash Flow',
 'Operating Cash Flow',
 'Net Income From Continuing Operations',
 'Net Tangible Assets',
 'Invested Capital',
 'Retained Earnings',
 'Total Assets',
 'Current Debt',
 'Stockholders Equity',
 'EBIT',
 'Tax Rate For Calcs',
 'Capital Expenditure Reported' ,
 'EBITDA',
 'Total Expenses',
 'Net Income',
 'Basic EPS',
 'Operating Revenue',
 'Operating Expense',
 'Interest Expense']







eaningparams = [
"EBIT_cagr",
"EBITDA_cagr",
"OperatingRevenue_Cagr",
"BasicEPS_Cagr",
"operatingMargins",
"FreeCashFlow_cagr",
"NetIncomeFromContinuingOperations_cagr",
"NetIncome_cagr" , 
"grossMargins",    
]

comparablesparams = [
    "trailingPE",
    "Free Cash Flow_avggrowth",
    "Free Cash Flow_cagr",
    "debtToEquity",
     "pricetoSales" ,
     "pricetoFreeCashFlow", 
    "trailingAnnualDividendYield",
    "dividendYield",
    "dividendRate",
    "fiveYearAvgDividendYield"
]

expensesparams = [
    "CurrentDebt_cagr",
    "CapitalExpenditure_cagr",
    "InterestExpense_cagr",
    "TotalExpenses_cagr",
    "OperatingExpense_cagr","WACC"
]





financialsparams = [
    "NetTangibleAssets_cagr",
    "InvestedCapital_cagr",
    "RetainedEarnings_cagr",
]


efficiencyparams = [
    "ROE",
    "RORE", 
    "WACC" , 
    "COD" ,
    "ATR" , 
    "ROIC" , 
    "ICR" , 
    "EFF"
]

