import sys
sys.path.insert(0, '..')

import pandas as pd
import portfolio as portfolio

def _p_(txt):
    print("")
    print("### ", txt)
    print("\n"+"*"*100)

if __name__ == "__main__":

    portfolio = portfolio.Portfolio()
    portfolio.target_currency = "EUR"
    
    portfolio.from_csv("portfolio.sample.csv")
    portfolio.load_history(aggregate_to="portfolio", cleanup=False)

    transaction = pd.DataFrame([{"NAME":"ASML","AMOUNT":3.0,"PRICE":2635.0,"DATE":"16.02.2024","SYMBOL":"ASMLF"}])
    portfolio.add_transaction(transaction=transaction)
    
    transaction = pd.DataFrame([{"NAME":"ASML","AMOUNT":6.0,"PRICE":5270.0,"DATE":"16.02.2024","SYMBOL":"ASMLF"}])
    portfolio.add_transaction(transaction=transaction)
    
    portfolio.load_history(aggregate_to="portfolio", cleanup=False)
    
    # portflio calc
    portfolio.aggregate_to(level="portfolio", inplace=True)
    portfolio.get_portfolio_tech_indicators(interval=30, inplace= True)
    _p_(f"{portfolio.portfolio_tech_indicators = }")

    # symbol calc
    portfolio.aggregate_to(level="symbol", inplace=True)
    sym="ASMLF"
    _p_(f"{sym}: {[p for p in portfolio.history.columns if sym in p]}")
    portfolio.get_symbol_tech_indicators(interval=30, inplace=True, symbol=sym)
    _p_(f"{portfolio.symbol_tech_indicators = }")

    portfolio.history_to_csv("tmp_test_history.csv")
