import numpy as np
import ast


def parse_data(field):
    try:
        return [float(x) for x in ast.literal_eval(field)]
    except (ValueError, SyntaxError, TypeError):
        return []


def calc_qoq_growth(arr):
    arr = np.array(arr)
    if len(arr) < 2:
        return []
    return ((arr[1:] - arr[:-1]) / np.abs(arr[:-1] + 0.001)) * 100


def safe_mean(arr):
    arr = np.array(arr)
    return float(np.nanmean(arr)) if arr.size > 0 else None


def calculate_ratios_from_annual_data(stock):
    # Use relationships to get related objects
    financials = stock.financials[0] if stock.financials else None
    earning_metrics = stock.earning_metrics[0] if stock.earning_metrics else None
    metrics = stock.metrics[0] if stock.metrics else None
    quaterly_results = stock.quaterly_results[0] if stock.quaterly_results else None

    if not (financials and earning_metrics and metrics and quaterly_results):
        return {"error": "Missing related financial data."}

    current_price = stock.CurrentPrice
    shares_outstanding = stock.sharesOutstanding
    market_cap = (
        (current_price * shares_outstanding) / 1e7
        if current_price and shares_outstanding
        else 0
    )

    # Use totalCash if available, else fallback to RetainedEarnings (not ideal, but for demo)
    cash_data = parse_data(
        getattr(financials, "totalCash", "[]")
        or getattr(financials, "RetainedEarnings", "[]")
    )
    cash = cash_data[-1] if cash_data else 0

    total_debt_data = parse_data(financials.TotalDebt)
    total_debt = total_debt_data[-1] if total_debt_data else 0

    ebitda_data = parse_data(earning_metrics.EBITDA)
    ebitda = ebitda_data[-1] if ebitda_data else 0

    revenue_data = parse_data(earning_metrics.OperatingRevenue)
    revenue = revenue_data[-1] if revenue_data else 0

    sales_quarterly = parse_data(quaterly_results.Sales_Quaterly)
    netprofit_quarterly = parse_data(quaterly_results.NetProfit_Quaterly)

    op_quarterly = parse_data(quaterly_results.OperatingProfit_Quaterly)
    eps_quarterly = parse_data(quaterly_results.EPS_in_Rs_Quaterly)

    # Calculate growth ratios
    sales_qoq = calc_qoq_growth(sales_quarterly)
    netprofit_qoq = calc_qoq_growth(netprofit_quarterly)
    op_qoq = calc_qoq_growth(op_quarterly)
    eps_qoq = calc_qoq_growth(eps_quarterly)

    net_income_data = parse_data(earning_metrics.NetIncome)
    net_income = net_income_data[-1] if net_income_data else 0

    totalassets = parse_data(financials.TotalAssets)
    totalassets = totalassets[-1] if totalassets else 0

    fa = parse_data(financials.FixedAssets)
    fa = fa[-1] if fa else 0

    quickassets = totalassets - fa

    total_liabilities = parse_data(financials.TotalLiabilities)
    total_liabilities = total_liabilities[-1] if total_liabilities else 0

    total_debt_list = parse_data(financials.TotalDebt)
    total_debt_last = total_debt_list[-1] if total_debt_list else 0

    quickliabilities = total_liabilities - total_debt_last

    eps_data = parse_data(earning_metrics.epsTrailingTwelveMonths)
    earnings_per_share = eps_data[-1] if eps_data else 0

    fcff_data = parse_data(metrics.FCFF)
    fcff = fcff_data[-1] if fcff_data else 0

    equity_capital = parse_data(financials.EquityCapital)
    equity_capital = equity_capital[-1] if equity_capital else 0

    shareholdersEquity = equity_capital + cash
    growth_rate = getattr(earning_metrics, "OperatingRevenue_Cagr", 0)

    ratios = {}
    try:
        ratios["PE"] = (
            current_price / earnings_per_share if earnings_per_share > 0 else None
        )
        ratios["PS"] = market_cap / revenue if revenue > 0 else None
        ratios["Price_to_Cashflow"] = market_cap / fcff if fcff else None
        ev = market_cap + total_debt - cash
        ratios["EV"] = ev
        ratios["EV/EBITDA"] = ev / ebitda if ebitda > 0 else None
        ratios["PEG"] = (
            (ratios["PE"] / (growth_rate * 100)) if growth_rate > 0 else None
        )
        ratios["FCFF_Yield"] = fcff / market_cap if market_cap > 0 else None
        ratios["CurrentRatio"] = (
            quickassets / quickliabilities if quickliabilities else None
        )
        ratios["DebtToEquity"] = (
            total_debt / shareholdersEquity if shareholdersEquity else None
        )
        ratios["Avg_Sales_QoQ_Growth_Percent"] = safe_mean(sales_qoq)
        ratios["Avg_NetProfit_QoQ_Growth_Percent"] = safe_mean(netprofit_qoq)
        ratios["Avg_OperatingProfit_QoQ_Growth_Percent"] = safe_mean(op_qoq)
        ratios["Avg_EPS_QoQ_Growth_Percent"] = safe_mean(eps_qoq)
        print(ratios)
    except ZeroDivisionError:
        pass

    return ratios


# Example usage


# Example usage
data = {
    "id": "eb15fa85-3115-474f-9499-52df96368a9f",
    "Ticker": "THOMASCOOK",
    "CurrentPrice": 170,
    "marketCap": 0,
    "Description": "Thomas Cook (India) Limited offers integrated travel services in India and internationally. It operates through financial services, travel and related services, vacation ownership and resorts business, and digiphoto imaging services segments. The financial services segment engages in the wholesale, and retail purchase and sale of foreign currencies and paid documents. Its service segment is involved in tour operations, travel management, visa services, and travel insurance and related activities. Thomas Cook (India) Limited was founded in 1881 and is based in Mumbai, India. Thomas Cook (India) Limited operates as a subsidiary of Fairbridge Capital (Mauritius) Limited.",
    "CompanyName": "Thomas Cook (India) Limited",
    "sector": "Consumer Cyclical",
    "beta": 0.421,
    "Industry": "Travel Services",
    "updated": None,
    "FloatShares": 152157579,
    "sharesOutstanding": 465700000,
    "channels": [],
    "technicals": [],
    "earning_metrics": [
        {
            "id": "56061279-874c-4f1c-bb98-a8c90ae3dcfe",
            "OperatingRevenue": "[1287.0, 3244.0, 6094.0, 8762.0, 11248.0, 6603.0, 6833.0, 795.0, 1888.0, 5048.0, 7299.0, 8140.0]",
            "EBIT_cagr": 2184.306803963013,
            "EBITDA": "[147.0, 243.0, 184.0, 338.0, 372.0, 83.0, 107.0, -352.0, -187.0, 178.0, 437.0, 477.0]",
            "EBITDA_cagr": -39.1242355363383,
            "OperatingRevenue_Cagr": 49.71452626903568,
            "operatingMargins": "[11.0, 7.0, 3.0, 4.0, 3.0, 1.0, 2.0, -44.0, -10.0, 4.0, 6.0, 6.0]",
            "OperatingProfit": "[147.0, 243.0, 184.0, 338.0, 372.0, 83.0, 107.0, -352.0, -187.0, 178.0, 437.0, 477.0]",
            "epsTrailingTwelveMonths": "[2.51, 3.31, -2.13, 1.18, 161.21, 2.29, -0.02, -6.72, -5.18, 0.14, 5.5, 5.4]",
            "epsForward": 4570.515311353264,
            "NetIncome_cagr": 954.5846157088806,
            "FCFF_Cagr": 3792.6349730466304,
            "NetIncome": "[69.0, 112.0, -59.0, 86.0, 6131.0, 89.0, -18.0, -295.0, -254.0, 10.0, 271.0, 258.0]",
        }
    ],
    "comparables": [],
    "expenses": [
        {
            "id": "17f2bad7-6301-421b-a400-8a0ee0ecacad",
            "CapitalExpenditure_cagr": 0,
            "dividendPayoutratio": "[0.0, 15.0, -18.0, 32.0, 0.0, 16.0, 0.0, 0.0, 0.0, 291.0, 11.0, 8.0]",
            "CapitalExpenditure": "[0.0,-898.9369863013699,90.34246575342468,-894.9808219178083,1533.2328767123288,-649.6958904109588,-283.0219178082193,-280.1397260273973,94.77260273972604,262.10410958904106,319.36712328767135,-630.709589041096]",
            "InterestExpense_cagr": 17.657961149947923,
            "CurrentDebt_cagr": 0,
            "EBIT": "[102.0, 171.0, 1.0, 199.0, 6091.0, 110.0, -69.0, -416.0, -322.0, 27.0, 345.0, 378.0]",
            "Operating_Expense": "[1140.0, 3001.0, 5910.0, 8425.0, 10876.0, 6520.0, 6726.0, 1147.0, 2075.0, 4870.0, 6862.0, 7663.0]",
            "Intrest_Expense": "[34.0, 71.0, 92.0, 132.0, 149.0, 73.0, 101.0, 62.0, 62.0, 89.0, 99.0, 95.0]",
            "WACC": -2.367210377952314,
        }
    ],
    "financials": [
        {
            "id": "2b4dbe12-d5fb-4b0b-b552-47fcd0c6e0d2",
            "RetainedEarnings_cagr": 40.847069475052024,
            "RetainedEarnings": "[663.0, 1302.0, 1211.0, 1950.0, 8634.0, 8856.0, 1627.0, 1891.0, 1651.0, 1666.0, 2010.0, 2213.0]",
            "EquityCapital": "[25.0, 27.0, 37.0, 37.0, 37.0, 37.0, 38.0, 38.0, 44.0, 47.0, 47.0, 47.0]",
            "UnusualExpense": "[6.0, 41.0, -31.0, 84.0, 6005.0, 168.0, 76.0, 146.0, 55.0, 62.0, 134.0, 138.0]",
            "DepreciationAmortization": "[18.0, 41.0, 61.0, 91.0, 137.0, 67.0, 151.0, 148.0, 129.0, 124.0, 128.0, 142.0]",
            "WorkingCapital": "[-31.734246575342464, 142.2027397260274, -651.1397260273973, -696.158904109589, -1109.3917808219178, -1139.695890410959, -1160.6739726027397, -801.5342465753424, -848.3068493150685, -1106.4109589041095, -1619.7780821917809, -1115.0684931506848]",
            "CashfromFinancingActivities": "[88.0, 565.0, 548.0, 161.0, 477.0, -167.0, -170.0, 335.0, -85.0, -230.0, -291.0, -183.0]",
            "CashfromInvestingActivities": "[-366.0, -607.0, -165.0, -253.0, -458.0, -263.0, -184.0, 351.0, -123.0, -179.0, -437.0, -329.0]",
            "CashFromOperatingActivities": "[219.0, 131.0, 383.0, 273.0, -244.0, 253.0, 120.0, -581.0, -139.0, 649.0, 829.0, 717.0]",
            "TotalReceivablesNet": "0",
            "TotalAssets": "[1523.0, 3126.0, 4899.0, 6965.0, 12096.0, 13008.0, 5492.0, 4736.0, 4615.0, 5657.0, 6364.0, 7116.0]",
            "FixedAssets": "[475.0, 1200.0, 1903.0, 2843.0, 1723.0, 2403.0, 2707.0, 2628.0, 2580.0, 2576.0, 2770.0, 2896.0]",
            "TotalLiabilities": "[1523.0, 3126.0, 4899.0, 6965.0, 12096.0, 13008.0, 5492.0, 4736.0, 4615.0, 5657.0, 6364.0, 7116.0]",
            "TotalDebt": "[182.0, 380.0, 1042.0, 1404.0, 425.0, 361.0, 762.0, 612.0, 598.0, 539.0, 418.0, 465.0]",
        }
    ],
    "metrics": [
        {
            "id": "45fe277d-5ee0-4fe5-80b3-b2abf4fe7388",
            "ROE": 0.026644599997815554,
            "FCFF": "[-869.0, -1313.0630136986301, -587679.3424657534, -6224.0191780821915, -1479.2328767123288, -411.3041095890412, 7978.021917808219, 1559.1397260273973, 1130.2273972602738, -4953.104109589041, -1470.3671232876713, -1692.290410958904]",
            "ROA": 1.0195081673925208,
            "ROIC": "[18.0, 17.0, 9.0, 10.0, 6.0, 2.0, 1.0, -14.0, -11.0, 5.0, 19.0, 19.0]",
            "WACC": -2.367210377952314,
            "COD": 0.17596689025260454,
            "ICR": 1.5072125363221254,
        }
    ],
    "Days": [
        {
            "id": "40f1704c-3527-4e6b-96ed-bbf5cf39bb42",
            "InventoryDays": "['', '', '', '', '', '', '', '', '', '', '', '']",
            "DebtorDays": "[94.0, 73.0, 50.0, 42.0, 28.0, 46.0, 25.0, 59.0, 45.0, 41.0, 32.0, 28.0]",
            "WorkingCapitalDays": "[-9.0, 16.0, -39.0, -29.0, -36.0, -63.0, -62.0, -368.0, -164.0, -80.0, -81.0, -50.0]",
            "CashConversionCycle": "[94.0, 73.0, 50.0, 42.0, 28.0, 46.0, 25.0, 59.0, 45.0, 41.0, 32.0, 28.0]",
        }
    ],
    "support": [],
    "quaterly_results": [
        {
            "id": "031d3f6c-db96-46d7-b138-8e8b1c663cc2",
            "ticker": "THOMASCOOK",
            "Date": "['Mar 2022', 'Jun 2022', 'Sep 2022', 'Dec 2022', 'Mar 2023', 'Jun 2023', 'Sep 2023', 'Dec 2023', 'Mar 2024', 'Jun 2024', 'Sep 2024', 'Dec 2024', 'Mar 2025']",
            "Sales_Quaterly": "[522.0, 976.0, 1222.0, 1536.0, 1313.0, 1899.0, 1843.0, 1893.0, 1664.0, 2106.0, 2004.0, 2061.0, 1969.0]",
            "Expenses_Quaterly": "[530.0, 940.0, 1180.0, 1472.0, 1277.0, 1775.0, 1741.0, 1777.0, 1573.0, 1970.0, 1879.0, 1945.0, 1871.0]",
            "OperatingProfit_Quaterly": "[-8.0, 36.0, 42.0, 64.0, 36.0, 124.0, 103.0, 116.0, 91.0, 136.0, 125.0, 116.0, 98.0]",
            "EPS_in_Rs_Quaterly": "[-1.1, -0.12, 0.02, 0.39, -0.15, 1.55, 1.0, 1.75, 1.2, 1.6, 1.38, 1.05, 1.37]",
            "Profit_before_tax_Quaterly": "[-52.0, -2.0, 5.0, 30.0, -6.0, 101.0, 77.0, 107.0, 61.0, 109.0, 110.0, 71.0, 88.0]",
            "NetProfit_Quaterly": "[-50.0, -6.0, 0.0, 27.0, -10.0, 71.0, 51.0, 91.0, 58.0, 73.0, 72.0, 47.0, 66.0]",
            "Interest_Quaterly": "[17.0, 20.0, 19.0, 28.0, 23.0, 26.0, 23.0, 24.0, 26.0, 22.0, 24.0, 26.0, 24.0]",
            "OPM_Percent_Quaterly": "0",
            "Depreciation_Quaterly": "[31.0, 30.0, 31.0, 32.0, 30.0, 30.0, 31.0, 33.0, 33.0, 34.0, 35.0, 37.0, 36.0]",
        }
    ],
    "shareholdings": [
        {
            "id": "ca14fd49-e2f8-483c-803c-fbaf6f1d87ad",
            "Date": "['Mar 2017', 'Mar 2018', 'Mar 2019', 'Mar 2020', 'Mar 2021', 'Mar 2022', 'Mar 2023', 'Mar 2024', 'Mar 2025']",
            "Promoters": "[67.66, 67.03, 66.94, 65.6, 65.6, 70.58, 72.34, 63.83, 63.83]",
            "FIIs": "[7.6, 6.42, 3.8, 2.51, 0.94, 0.41, 0.51, 2.29, 4.52]",
            "DIIs": "[13.05, 14.51, 16.71, 16.86, 12.98, 9.88, 9.2, 8.64, 8.1]",
            "Public": "[11.69, 12.04, 12.55, 13.08, 18.59, 17.64, 16.63, 24.07, 22.44]",
            "Government": "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.08, 0.1]",
            "Others": "[0.0, 0.0, 0.0, 1.94, 1.89, 1.5, 1.33, 1.08, 1.0]",
            "ShareholdersCount": "[46333.0, 46558.0, 62833.0, 57816.0, 75575.0, 90995.0, 79766.0, 93080.0, 117253.0]",
        }
    ],
}

