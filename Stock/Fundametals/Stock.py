from .StockCRUD import CretaeRawStockInstance    
from Database.models import Stock, EarningMetric, Comparables, Expenses, Financials, ValuationMetrics
from uuid import uuid4
from sqlalchemy.orm import Session


def safe_get_as_float(value, default=0.0, field_name=""):
    try:
        if value is None:
            return default
        if isinstance(value, list):  # Catch the list issue early
            raise TypeError(f"Field '{field_name}' has a list instead of a float: {value}")
        return float(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error in field '{field_name}': Could not convert {value} to float ({e})")


def safe_get_as_string(value, default="0"):
    return str(value) if value is not None else default


def CreateStockDataBaseInstance(Ticker: str, db: Session):

    if db.query(Stock).filter(Stock.Ticker == Ticker).first():
        return  
     
    stock_dict = CretaeRawStockInstance(Ticker)
    if "error" in stock_dict.keys():
        print("Got error in stock_dict for ticker: ", Ticker)   
        return stock_dict
    try:
        stock = Stock(
            id=str(uuid4()),
            Ticker=safe_get_as_string(stock_dict.get("ticker")),
            CurrentPrice=safe_get_as_float(stock_dict.get("CurrentPrice"), 0, "Current Price"),
            marketCap=safe_get_as_float(stock_dict.get("Marketcap"), 0, "marketcap"),
            twoHundredDayAverage=safe_get_as_float(stock_dict.get("twoHundredDayAverage"), 0, "twoHundredDayAverage"),
            fiftyDayAverage=safe_get_as_float(stock_dict.get("fiftyDayAverage"), 0, "fiftyDayAverage"),
            sector=safe_get_as_string(stock_dict.get("sector"), "Unknown"),
            beta=safe_get_as_float(stock_dict.get("beta"), 0, "beta")
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

        earning_metric = EarningMetric(
            id=str(uuid4()),
            stock_id=stock.id,
            EBIT_cagr=safe_get_as_float(stock_dict.get("EBIT_cagr"), 0, "EBIT_cagr"),
            OperatingRevenue = safe_get_as_string(stock_dict.get("OperatingRevenue") ) , 
            EBITDA_cagr=safe_get_as_float(stock_dict.get("EBITDA_cagr"), 0, "EBITDA_cagr"),
            OperatingRevenue_Cagr=safe_get_as_float(stock_dict.get("OperatingRevenue_cagr"), 0, "Operating Revenue_cagr"),
            operatingMargins=safe_get_as_float(stock_dict.get("operatingMargins"), 0, "operatingMargins"),
            epsTrailingTwelveMonths=safe_get_as_float(stock_dict.get("epsTrailingTwelveMonths"), 0, "epsTrailingTwelveMonths"),
            epsForward=safe_get_as_float(stock_dict.get("epsForward"), 0, "epsForward"),    
            FreeCashFlow_cagr=safe_get_as_float(stock_dict.get("FCFF_growth"), 0, "Free Cash Flow_cagr"),
            NetIncomeFromContinuingOperations_cagr=safe_get_as_float(stock_dict.get("Net Income From Continuing Operations_cagr"), 0, "Net Income From Continuing Operations_cagr"),
            NetIncome_cagr=safe_get_as_float(stock_dict.get("Net Income_growth"), 0, "Net Income_cagr") , 
            NetIncome = safe_get_as_string(stock_dict.get("Net Income"), 0, "Net Income") 
        )
        db.add(earning_metric)

        comparables = Comparables(
            id=str(uuid4()),
            stock_id=stock.id,
            trailingPE=safe_get_as_float(stock_dict.get("trailingPE"), 0, "trailingPE"),
            forwardPE=safe_get_as_float(stock_dict.get("forwardPE"), 0, "forwardPE"),
            pricetoBook=safe_get_as_float(stock_dict.get("bookValue"), 0, "bookValue"),
            pricetoFreeCashFlow=safe_get_as_float(stock_dict.get("PCF"), 0, "PCF"),
            pricetoSales=safe_get_as_float(stock_dict.get("PS"), 0, "PS"),
            DebttoEquity=safe_get_as_float(stock_dict.get("debtToEquity"), 0, "debtToEquity"),
            trailingAnnualDividendYield=safe_get_as_float(stock_dict.get("trailingAnnualDividendYield"), 0, "trailingAnnualDividendYield"),
            dividendYield=safe_get_as_float(stock_dict.get("dividendYield"), 0, "dividendYield"),
            dividendRate=safe_get_as_float(stock_dict.get("dividendRate"), 0, "dividendRate"),
            fiveYearAvgDividendYield=safe_get_as_float(stock_dict.get("fiveYearAvgDividendYield"), 0, "fiveYearAvgDividendYield"),
            payoutRatio=safe_get_as_float(stock_dict.get("payoutRatio"), 0, "payoutRatio")
        )
        db.add(comparables)

        expenses = Expenses(
            id=str(uuid4()),
            stock_id=stock.id,
            CurrentDebt_cagr=safe_get_as_float(stock_dict.get("TotalDebt_cagr"), 0, "Current Debt_cagr"),
            CapitalExpenditure_cagr=safe_get_as_float(stock_dict.get("CapitalExpenditure_cagr"), 0, "CapitalExpenditure Reported"),
            InterestExpense_cagr=safe_get_as_float(stock_dict.get("InterestExpense_cagr"), 0, "InterestExpense"),
            TotalExpenses_cagr=safe_get_as_float(stock_dict.get("TotalExpenses_cagr"), 0, "TotalExpenses"),
            WACC=safe_get_as_float(stock_dict.get("WACC"), 0, "WACC") , 
            Intrest_Expense = safe_get_as_string(stock_dict.get("InterestExpense")) , 
            Operating_Expense = safe_get_as_string(stock_dict.get("OperatingExpense")) , 
            OperatingMargin = safe_get_as_float(stock_dict.get("OperatingExpense"))         
        
        )
        db.add(expenses)

        financials = Financials(
            id=str(uuid4()),
            stock_id=stock.id,
            NetTangibleAssets_cagr=safe_get_as_float(stock_dict.get("Net Tangible Assets_cagr"), 0, "Net Tangible Assets_cagr"),
            InvestedCapital=safe_get_as_string(stock_dict.get("Invested Capital"), "0"),
            InvestedCapital_cagr=safe_get_as_float(stock_dict.get("Invested Capital_cagr"), 0, "Invested Capital_cagr"),
            RetainedEarnings_cagr=safe_get_as_float(stock_dict.get("Retained Earnings_cagr"), 0, "Retained Earnings_cagr"),
            TotalAssets=safe_get_as_string(stock_dict.get("Total Assets_cagr"), "0"),
            TaxRateForCalcs=safe_get_as_string(stock_dict.get("Tax Rate For Calcs"), "0")
        )
        db.add(financials)

        metrics = ValuationMetrics(
            id=str(uuid4()),
            stock_id=stock.id,
            ROE=safe_get_as_float(stock_dict.get("ROE"), 0, "ROE") , 
            ROIC=safe_get_as_float(stock_dict.get("ROIC"), 0, "ROIC"),
            WACC=safe_get_as_float(stock_dict.get("WACC"), 0, "WACC"),
            COD=safe_get_as_float(stock_dict.get("COD"), 0, "COD"),
            ICR=safe_get_as_float(stock_dict.get("ICR"), 0, "ICR"),
            ATR=safe_get_as_float(stock_dict.get("ATR"), 0, "ATR")
        )
        db.add(metrics)

        db.commit()
        return {"message": f"Stock data created successfully for {stock.Ticker}",
                "stock_id": stock.id}

    except Exception as e:
        db.rollback()
        return {"error": f"Failed to create stock data: {str(e)}"}