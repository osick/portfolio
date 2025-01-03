import sys
sys.path.insert(0, '..')

import pandas as pd
import portfolio.portfolio as portfolio

if __name__ == "__main__":

    portfolio = portfolio.Portfolio()
    portfolio.target_currency = "EUR"
    
    portfolio.from_csv("portfolio.sample.csv")
    portfolio.load_history(aggregate_to="symbol")
    
    transaction = pd.DataFrame([{"NAME":"ASML","AMOUNT":3.0,"PRICE":2635.0,"DATE":"16.02.2024","SYMBOL":"ASMLF"}])
    portfolio.add_transaction(transaction=transaction)
    
    transaction = pd.DataFrame([{"NAME":"ASML","AMOUNT":6.0,"PRICE":5270.0,"DATE":"16.02.2024","SYMBOL":"ASMLF"}])
    portfolio.add_transaction(transaction=transaction)
    
    aggr_prt = portfolio.aggregate_to(level="portfolio", cleanup= False, inplace=False)
    
    aggr_prt = portfolio.aggregate_to(level="symbol", cleanup= False, inplace=False)
    
    portfolio.aggregate_to(level="portfolio", cleanup= True, inplace=True)
    print(portfolio.get_portfolio_tech_indicators(interval=30, inplace= False))

    portfolio.get_portfolio_tech_indicators(interval=30,inplace=True )
    print(portfolio.history[[portfolio._prefix_portfolio_indicator+p for p in portfolio.portfolio_tech_indicators]])
    portfolio.history_to_csv("tmp_test_history.csv")
