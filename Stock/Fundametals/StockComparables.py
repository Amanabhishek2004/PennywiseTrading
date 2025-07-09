import numpy as np
import ast


def parse_data(data_string):
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
       financials.RetainedEarnings
    )
    cash = cash_data[-1] if cash_data else 0
    print(getattr(financials, "RetainedEarnings", "[]"))

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
    print(total_debt , equity_capital)
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
            
            ( (ratios["PE"]  if ratios["PE"] else 0)/ (growth_rate)) if growth_rate > 0 else None
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
    
    except ZeroDivisionError:
        pass

    return ratios


# Example usage


# Example usage
data = {
    "id": "76f99c46-d23b-431f-8513-ca52c967366e",
    "Ticker": "RELIANCE",
    "CurrentPrice": 1444,
    "marketCap": 19534163703808,
    "Description": "Reliance Industries Limited engages in hydrocarbon exploration and production, oil and chemicals, textile, retail, digital, material and composites, renewables, and financial services businesses worldwide. It operates through Oil to Chemicals, Oil and Gas, Retail, Digital Services, and Others segments. The company produces and markets petroleum products, such as liquefied petroleum gas, propylene, naphtha, gasoline, jet/aviation turbine fuel, kerosene oil, diesel, sulphur, and petroleum coke. It also provides petrochemicals, including high-density and low-density polyethylene (PE), linear low-density PE, polyester fibers and yarns, polypropylene, polyvinyl chloride, purified terephthalic acid, ethylene glycols and oxide, paraxylene, ortho xylene, benzene, linear alkyl benzene and paraffin, poly butadiene rubber, styrene butadiene rubber, butyl rubber, and polyethylene terephthalate. In addition, the company manufactures and markets yarns, fabrics, apparel, and auto furnishings; explores, develops, and produces crude oil and natural gas; and operates various stores comprising neighborhood, supermarket, hypermarket, wholesale cash and carry, specialty, online stores, as well as stores that offer apparel, beauty and cosmetics, accessories, footwear, consumer electronics, connectivity products, and others. Further, the company provides range of digital television, gaming, broadband, and telecommunication services under the Jio brand name; and non-banking financial and insurance broking services. Additionally, it operates news and entertainment platforms, and Network18 and television channels; publishes magazines; and offers highway hospitality and fleet management services. The company was founded in 1957 and is based in Mumbai, India.",
    "CompanyName": "Reliance Industries Limited",
    "sector": "Energy",
    "beta": 0.332,
    "Industry": "Oil & Gas Refining & Marketing",
    "updated": None,
    "FloatShares": 5807754519,
    "sharesOutstanding": 13532499968,
    "channels": [],
    "technicals": [],
    "earning_metrics": [
      {
        "id": "4f409413-c436-4692-8617-9d52dbbd9a51",
        "OperatingRevenue": "[433521.0, 374372.0, 272583.0, 303954.0, 390823.0, 568337.0, 596679.0, 466307.0, 694673.0, 876396.0, 899041.0, 964693.0]",
        "EBIT_cagr": 13.424547169082,
        "EBITDA": "[34935.0, 37449.0, 41781.0, 46307.0, 64315.0, 84250.0, 89266.0, 80790.0, 108581.0, 142318.0, 162498.0, 165444.0]",
        "EBITDA_cagr": 16.1274201640351,
        "OperatingRevenue_Cagr": 10.2574768773343,
        "operatingMargins": "[8.0, 10.0, 15.0, 15.0, 16.0, 15.0, 15.0, 17.0, 16.0, 16.0, 18.0, 17.0]",
        "OperatingProfit": "[34935.0, 37449.0, 41781.0, 46307.0, 64315.0, 84250.0, 89266.0, 80790.0, 108581.0, 142318.0, 162498.0, 165444.0]",
        "epsTrailingTwelveMonths": "[16.31, 17.07, 21.51, 21.55, 26.69, 29.28, 29.1, 38.75, 44.87, 49.29, 51.45, 51.47]",
        "epsForward": 11.5476205721181,
        "NetIncome_cagr": 12.934727201538,
        "FCFF_Cagr": 0,
        "NetIncome": "[22548.0, 23640.0, 29861.0, 29833.0, 36080.0, 39837.0, 39880.0, 53739.0, 67845.0, 74088.0, 79020.0, 81309.0]"
      }
    ],
    "comparables": [],
    "expenses": [
      {
        "id": "9c0d7f90-9513-4ece-a45e-b6ef8a5e2349",
        "CapitalExpenditure_cagr": 0,
        "dividendPayoutratio": "[12.0, 12.0, 10.0, 11.0, 10.0, 10.0, 10.0, 9.0, 9.0, 9.0, 10.0, 11.0]",
        "CapitalExpenditure": "[np.float64(-0.0), np.float64(19345.852054794523), np.float64(20973.882191780824), np.float64(16425.92602739726), np.float64(-168589.14246575342), np.float64(-44351.830136986304), np.float64(-73500.43835616438), np.float64(-189039.07671232877), np.float64(-46467.58082191781), np.float64(-100139.01369863014), np.float64(-52158.50410958904), np.float64(-392190.14520547946)]",
        "InterestExpense_cagr": 24.7223252908391,
        "CurrentDebt_cagr": 0,
        "EBIT": "[28763.0, 31114.0, 38737.0, 40034.0, 49426.0, 55227.0, 53606.0, 55461.0, 83815.0, 94464.0, 104727.0, 106017.0]",
        "Operating_Expense": "[398586.0, 336923.0, 230802.0, 257647.0, 326508.0, 484087.0, 507413.0, 385517.0, 586092.0, 734078.0, 736543.0, 799249.0]",
        "Intrest_Expense": "[3836.0, 3316.0, 3691.0, 3849.0, 8052.0, 16495.0, 22027.0, 21189.0, 14584.0, 19571.0, 23118.0, 24269.0]",
        "WACC": 0.0741038100902498
      }
    ],
    "financials": [
      {
        "id": "055c26ed-74a4-489c-b5f7-96e02479bd20",
        "RetainedEarnings_cagr": 15.041967092728,
        "RetainedEarnings": "[195747.0, 215556.0, 228608.0, 260750.0, 287584.0, 381186.0, 442827.0, 693727.0, 772720.0, 709106.0, 786715.0, 829668.0]",
        "EquityCapital": "[2940.0, 2943.0, 2948.0, 2959.0, 5922.0, 5926.0, 6339.0, 6445.0, 6765.0, 6766.0, 6766.0, 13532.0]",
        "UnusualExpense": "[8865.0, 8528.0, 12212.0, 9222.0, 9869.0, 8406.0, 8570.0, 22432.0, 19600.0, 12020.0, 16179.0, 17978.0]",
        "DepreciationAmortization": "[11201.0, 11547.0, 11565.0, 11646.0, 16706.0, 20934.0, 22203.0, 26572.0, 29782.0, 40303.0, 50832.0, 53136.0]",
        "WorkingCapital": "[-3563.186301369863, -37950.03835616438, -87375.9205479452, -117417.84657534247, -154187.70410958905, -104324.87397260274, -165108.43561643836, 15330.64109589041, -24741.77808219178, -21609.764383561644, -24631.260273972603, 55502.88493150685]",
        "CashfromFinancingActivities": "[13713.0, 8444.0, -3210.0, 8617.0, -2001.0, 55906.0, -2541.0, 101904.0, 17289.0, 10455.0, -16646.0, -31891.0]",
        "CashfromInvestingActivities": "[-73070.0, -64706.0, -36186.0, -66201.0, -68192.0, -94507.0, -72497.0, -142385.0, -109162.0, -93001.0, -113581.0, -137535.0]",
        "CashFromOperatingActivities": "[43261.0, 34374.0, 38134.0, 49550.0, 71459.0, 42346.0, 94877.0, 26958.0, 110654.0, 115032.0, 158788.0, 178703.0]",
        "TotalReceivablesNet": "0",
        "TotalAssets": "[428843.0, 504486.0, 598997.0, 706802.0, 811273.0, 997630.0, 1163015.0, 1320065.0, 1498622.0, 1605882.0, 1755048.0, 1950121.0]",
        "FixedAssets": "[141417.0, 156458.0, 184910.0, 198526.0, 403885.0, 398374.0, 532658.0, 541258.0, 627798.0, 724805.0, 779985.0, 1092041.0]",
        "TotalLiabilities": "[428843.0, 504486.0, 598997.0, 706802.0, 811273.0, 997630.0, 1163015.0, 1320065.0, 1498622.0, 1605882.0, 1755048.0, 1950121.0]",
        "TotalDebt": "[138761.0, 168251.0, 194714.0, 217475.0, 239843.0, 307714.0, 355133.0, 278962.0, 319158.0, 451664.0, 458991.0, 369575.0]"
      }
    ],
    "metrics": [
      {
        "id": "4ca3a1bd-dddd-4db4-8461-0da855b3ea96",
        "ROE": 0.103200782109588,
        "FCFF": "[np.float64(46253.08), np.float64(17548.30794520548), np.float64(20002.187808219176), np.float64(36010.82397260274), np.float64(245926.10246575344), np.float64(98574.2301369863), np.float64(184677.41835616436), np.float64(236550.40671232878), np.float64(168934.6208219178), np.float64(230436.39369863016), np.float64(228285.00410958903), np.float64(589337.5852054795)]",
        "ROA": 1.98681366227422,
        "ROIC": "[10.0, 9.0, 10.0, 10.0, 11.0, 12.0, 11.0, 8.0, 8.0, 9.0, 10.0, 9.0]",
        "WACC": 0.0741038100902498,
        "COD": 0.044513059361504,
        "ICR": 5.28689249773803
      }
    ],
    "Days": [
      {
        "id": "740bf95b-2c20-4051-bea5-b540c95c721f",
        "InventoryDays": "[57.0, 66.0, 90.0, 84.0, 83.0, 63.0, 67.0, 102.0, 83.0, 87.0, 95.0, 85.0]",
        "DebtorDays": "[8.0, 5.0, 6.0, 10.0, 16.0, 19.0, 12.0, 15.0, 12.0, 12.0, 13.0, 16.0]",
        "WorkingCapitalDays": "[-3.0, -37.0, -117.0, -141.0, -144.0, -67.0, -101.0, 12.0, -13.0, -9.0, -10.0, 21.0]",
        "CashConversionCycle": "[4.0, -2.0, -21.0, -38.0, -46.0, -18.0, -9.0, -19.0, -27.0, 7.0, -3.0, -8.0]"
      }
    ],
    "support": [],
    "quaterly_results": [
      {
        "id": "2d03aa1b-946e-4565-b7ba-a82c35456aac",
        "ticker": "RELIANCE",
        "Date": "['Mar 2022', 'Jun 2022', 'Sep 2022', 'Dec 2022', 'Mar 2023', 'Jun 2023', 'Sep 2023', 'Dec 2023', 'Mar 2024', 'Jun 2024', 'Sep 2024', 'Dec 2024', 'Mar 2025']",
        "Sales_Quaterly": "[207375.0, 218855.0, 229409.0, 216737.0, 212834.0, 207559.0, 231886.0, 225086.0, 236533.0, 231784.0, 231535.0, 239986.0, 261388.0]",
        "Expenses_Quaterly": "[176009.0, 181157.0, 198438.0, 181728.0, 174478.0, 169466.0, 190918.0, 184430.0, 194017.0, 193019.0, 192477.0, 196197.0, 217556.0]",
        "OperatingProfit_Quaterly": "[31366.0, 37698.0, 30971.0, 35009.0, 38356.0, 38093.0, 40968.0, 40656.0, 42516.0, 38765.0, 39058.0, 43789.0, 43832.0]",
        "EPS_in_Rs_Quaterly": "[11.98, 13.27, 10.09, 11.67, 14.26, 11.83, 12.85, 12.76, 14.01, 11.19, 12.24, 13.7, 14.34]",
        "Profit_before_tax_Quaterly": "[22411.0, 27034.0, 20347.0, 23002.0, 24081.0, 24294.0, 26493.0, 25833.0, 27720.0, 23234.0, 25037.0, 28643.0, 29103.0]",
        "NetProfit_Quaterly": "[18021.0, 19443.0, 15512.0, 17806.0, 21327.0, 18258.0, 19878.0, 19641.0, 21243.0, 17445.0, 19323.0, 21930.0, 22611.0]",
        "Interest_Quaterly": "[3556.0, 3997.0, 4554.0, 5201.0, 5819.0, 5837.0, 5731.0, 5789.0, 5761.0, 5918.0, 6017.0, 6179.0, 6155.0]",
        "OPM_Percent_Quaterly": "[15.0, 17.0, 14.0, 16.0, 18.0, 18.0, 18.0, 18.0, 18.0, 17.0, 17.0, 18.0, 17.0]",
        "Depreciation_Quaterly": "[8001.0, 8942.0, 9726.0, 10183.0, 11452.0, 11775.0, 12585.0, 12903.0, 13569.0, 13596.0, 12880.0, 13181.0, 13479.0]"
      }
    ],
    "shareholdings": [
      {
        "id": "501c8b50-5e13-4adc-9ea6-1af2ed0d2008",
        "Date": "['Mar 2017', 'Mar 2018', 'Mar 2019', 'Mar 2020', 'Mar 2021', 'Mar 2022', 'Mar 2023', 'Mar 2024', 'Mar 2025']",
        "Promoters": "[46.32, 47.45, 47.27, 50.07, 50.58, 50.66, 50.41, 50.31, 50.1]",
        "FIIs": "[22.58, 24.46, 24.39, 24.08, 25.66, 24.23, 22.49, 22.06, 19.07]",
        "DIIs": "[11.85, 11.23, 11.86, 13.78, 12.62, 14.23, 16.06, 16.98, 19.36]",
        "Public": "[19.12, 16.72, 16.29, 11.87, 10.94, 10.71, 10.89, 10.46, 11.29]",
        "Government": "[0.14, 0.15, 0.18, 0.2, 0.2, 0.17, 0.16, 0.19, 0.17]",
        "Others": "nan",
        "ShareholdersCount": "[2501302.0, 2266000.0, 2211231.0, 2632168.0, 3031272.0, 3327847.0, 3639396.0, 3463276.0, 4765728.0]"
      }
    ]
}
