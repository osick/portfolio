import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import sys
from prophet import Prophet

from .ticker import _get_history_ticker, _get_rates, _get_ticker_info


from warnings import simplefilter
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{", 
    datefmt="%Y-%m-%d %H:%M",
    filename="portfolio.log"
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

class Portfolio:

    def __init__(self):
        """
        Attributes
        ----------
            self.basedata               : The total asset in your portfolio
            self.transactions           : The list of transations (sell and buy)
            self.start_date             : The start date of the portfolip
            self.end_date               : The last date the portfolio is analyzed (typically today or later)
            self.history                : The historical development of the portfolio from start to end
            self.target_currency        : For simplicity the portfolio is calcluated in one currency. Defaults to "USD"      
            self.selected_info_fields   : Minimal List of (default) info fields from yfinance which will be stored in basedata
        """

        # The total asset in your portfolio
        self.basedata = None

        # The list of transations (sell and buy)
        self.transactions = None 

        # The start date of the portfolio
        self.start_date = None
        
        # The last date the portfolio is analyzed (typically today or later)
        self.end_date = None

        # for simplicity the portfolio is calcluated in one currency
        self.target_currency = "EUR"

        # The historical development of the portfolio from start to end
        self.history = None

        # default info values from yfinance which will be stored in basedata
        self.selected_info_fields=["longName", "country", "currency", "sector", "industry", "marketCap"] 

        self._exchange_rates = None
        self._currencies = []
        self._prefix_portfolio_indicator="__port_ind__"
        self._prefix_symbol_indicator="__symb_ind__"
        self._prefix_ticker="__tck__"

# ----------------------------
# PUBLIC methods
# ----------------------------
    def from_csv(self,csvfile):
        """
        loads transactions from csvfile and save them to self.transactions. Also self.basedata will be filled.
        Columns: NAME, VOLUME, PRICE, DATE, SYMBOL, 

        Parameters
        ----------
        csvfile : str
            The file name of the CSV file.

        Returns
        -------
        
        Raises
        -------
        
        """
        try:
            # self.transactions
            self.transactions  = pd.read_csv(csvfile, sep=",", dayfirst=True,date_format="%d.%m.%Y")
            self.transactions  = Portfolio._set_structure(self.transactions)

            # self.start_date
            self.start_date = self.transactions.index.min()
            self._load_basedata()
            logging.info(f"Data loaded from CSV file {csvfile}:")

        except Exception as e:
            logging.error(f"Data could not be loaded from CSV file {csvfile}: {e} ")

    def to_csv(self, csvfile, precision = None):
        """
        write transations to csvfile
        Columns: NAME, VOLUME, PRICE, DATE, SYMBOL, 


        Parameters
        ----------
        csvfile : str
            The file name of the CSV file.
        
        precision: str (optional)
            default: None
            corresponds to float_format, for example precision ="%0.4e" 
        
        Returns
        -------
        -
        
        Raises
        -------
        -
        
        """
        try:
            self.transactions.to_csv(csvfile, float_format=precision)
        except Exception as e:
            logging.error(f"transactions could not be written to CSV file {csvfile}: {e.with_traceback()} ")
        
    def history_to_csv(self, csvfile, precision = None):
        """
        write history of portfolio to csvfile
        Columns: depend on configuration 


        Parameters
        ----------
        csvfile : str
            The file name of the CSV file.
        precision: str (optional)
            default: None
            corresponds to float_format, for example precision ="%0.4e" 
        

        
        Returns
        -------
        -
        
        Raises
        -------
        -
        
        """
        try:
            self.history.to_csv(csvfile, float_format= precision)
        except Exception as e:
            logging.error(f"History could not be written to CSV file {csvfile}: {e.with_traceback()} ")

    def load_history(self, start = None, end = None, aggregate_to = None, cleanup = False, symbols:list= None):
        """
        computes history and saves to self.history

        Parameters
        ----------
        start: datetime
            default: None
            The start date of computation.
            If None (default), then it is min datetime of portfolio
        
        end: datetime (optional)
            default: None 
            The end date of computation. 
            If None (default), then it is datetime.today()

        aggregate_to: str (optional)
            Allowed values are "symbol" or "portfolio" or None (default)
            if not None it aggregates data to the given level
                
        Returns
        -------
        -
        
        Raises
        -------
        -
        
        """
        logging.info(f"started loading history data")
        if start is None:   start = self.start_date
        if end   is None:   end = datetime.today()
        
        days = pd.date_range(start=start, end=end, freq='D')
        
        self.history = pd.DataFrame({'Date': days})
        self.history = self.history.set_index('Date')
           
        for index, row in self.transactions.iterrows():
            # filter only for symbols list
            if symbols is not None and row["SYMBOL"] not in symbols: continue 

            symbol = row["SYMBOL"]
            
            ticker_df, _currency = _get_history_ticker(symbol,index,end)

            ticker_df.index = ticker_df.index.tz_localize(None)
            exchange_factor = self._exchange_rates[f'{_currency}{self.target_currency}=X']
            exchange_factor = exchange_factor.tz_localize(None)
            exchange_factor = exchange_factor[start:end]
            ticker_df["PRICE"] = row["PRICE"]

            self.history[f"{self._prefix_ticker}{symbol}_close"]=ticker_df["Close"]
            self.history[f"{self._prefix_ticker}{symbol}_high"]=ticker_df["High"]
            self.history[f"{self._prefix_ticker}{symbol}_low"]=ticker_df["Low"]
            self.history[f"{self._prefix_ticker}{symbol}_volume"]=ticker_df["Volume"]

            self.history[f'{symbol}_volume_{index.date()}'] = 0.0
            self.history.loc[index:end, f'{symbol}_volume_{index.date()}'] =  row["VOLUME"]

            self.history[f'{symbol}_close_{index.date()}'] = ticker_df["Close"] * row["VOLUME"] * exchange_factor
            self.history[f'{symbol}_close_{index.date()}'] = self.history[f'{symbol}_close_{index.date()}'].interpolate()
            
            self.history[f'{symbol}_high_{index.date()}'] = ticker_df["High"] * row["VOLUME"] * exchange_factor
            self.history[f'{symbol}_high_{index.date()}'] = self.history[f'{symbol}_high_{index.date()}'].interpolate()

            self.history[f'{symbol}_low_{index.date()}'] = ticker_df["Low"] * row["VOLUME"] * exchange_factor
            self.history[f'{symbol}_low_{index.date()}'] = self.history[f'{symbol}_low_{index.date()}'].interpolate()

            self.history[f'{symbol}_price_{index.date()}'] = ticker_df["PRICE"]
            self.history[f'{symbol}_price_{index.date()}'] = self.history[f'{symbol}_price_{index.date()}'].interpolate() 

        self.aggregate_to(level = aggregate_to, symbols= symbols, cleanup = cleanup, inplace=True)
        logging.info(f"loading history data done!")
    
    def aggregate_to(self, level = None, symbols= None, cleanup = False, inplace=False):
        if inplace == False: 
            aggregate = pd.DataFrame()
        if level == "portfolio":                
            cols={"price":[],"close":[], "volume":[]}

            filtered_history_columns =self.history.columns
            if symbols is not None:
                filtered_history_columns=[col for col in self.history.columns if "_" in col and col.split("_")[0] in symbols]
                logging.info(f"aggregate_to('portfolio') {filtered_history_columns = }")
            for col_type in cols.keys(): 
                cols[col_type] = [col for col in filtered_history_columns if "_"+col_type+"_" in col]
                if col_type != "volume":
                    if inplace == False:
                        aggregate[f'{col_type}'] = self.history[cols[col_type]].sum(axis=1)
                    else:
                        self.history[f'{col_type}'] = self.history[cols[col_type]].sum(axis=1)
                if cleanup == True and inplace == True:
                    self.history = self.history.drop(cols[col_type], axis=1) 
        elif level == "symbol":
            symbol_list=list(set(self.transactions["SYMBOL"])) if symbols is None else symbols
            for symbol in symbol_list:                
                col_per_symbol={"price":[],"close":[], "volume":[]}
                for col_type in col_per_symbol.keys(): 
                    col_per_symbol[col_type] = [col for col in self.history.columns if col.startswith(symbol+"_"+col_type+"_")]
                    if inplace == False:
                       aggregate[f'{symbol}_{col_type}'] = self.history[col_per_symbol[col_type]].sum(axis=1)
                    else:
                        self.history[f'{symbol}_{col_type}'] = self.history[col_per_symbol[col_type]].sum(axis=1)
                    if cleanup == True and inplace==True:
                        self.history = self.history.drop(col_per_symbol[col_type], axis=1) 
        elif level is not None:
            logging.error(f"No Aggregation possible. The attribute level= must be either 'symbol' or 'portfolio', not '{level}'. ")
        
        if inplace == False:
            return aggregate
        else:
            return

    def add_transaction(self, transaction: pd.DataFrame):
        """
        add transation to portfolio and saves it to self.transactions

        Parameters
        ----------
        transaction: pd.Dataframe
            structure is pd.DataFrame([{"NAME":NAME,"VOLUME":VOLUME,"PRICE":BUY,"DATE":DATE,"SYMBOL":SYMBOL}])
                        
        Returns
        -------
        -
        
        Raises
        -------
        -
        
        Examples
        --------
            portfolio = Portfolio("prtf.csv")
            transaction = pd.DataFrame([{"NAME":NAME,"VOLUME":VOLUME,"PRICE":BUY,"DATE":DATE,"SYMBOL":SYMBOL}])
            portfolio.add_transation(transaction)

        """

        struct = Portfolio._set_structure(struct=transaction)
        self.transactions = pd.concat([self.transactions, struct])
        self._load_basedata(added_item = transaction)

    def filter_history(self, symbols: list):
        pass

    def get_portfolio_tech_indicators(self, interval=20, symbols = None, inplace= True):
        if inplace == True: indicators=self.history
        else: indicators = pd.DataFrame()
        indicators[f"{self._prefix_portfolio_indicator}win"]   = self.history[f'close'] - self.history[f'price']
        indicators[f"{self._prefix_portfolio_indicator}sma"] = self.history['close'].rolling(window=interval).mean()
        indicators[f"{self._prefix_portfolio_indicator}ema"] = self.history['close'].ewm(span=interval).mean()
        indicators[f"{self._prefix_portfolio_indicator}std"] = self.history['close'].rolling(window=interval).std()
        indicators[f"{self._prefix_portfolio_indicator}bb_upper"] = indicators[f"{self._prefix_portfolio_indicator}sma"] + 2 * indicators[f"{self._prefix_portfolio_indicator}std"]
        indicators[f"{self._prefix_portfolio_indicator}bb_lower"] = indicators[f"{self._prefix_portfolio_indicator}sma"] - 2 * indicators[f"{self._prefix_portfolio_indicator}std"]
        indicators[f"{self._prefix_portfolio_indicator}perf"] = indicators[f'{self._prefix_portfolio_indicator}win'] / self.history[f'price']
        indicators[f"{self._prefix_portfolio_indicator}perf_sma"] = indicators[f'{self._prefix_portfolio_indicator}perf'].rolling(window=interval).mean()
        indicators[f"{self._prefix_portfolio_indicator}perf_ema"] = indicators[f'{self._prefix_portfolio_indicator}perf'].ewm(span=interval).mean()
        indicators[f"{self._prefix_portfolio_indicator}perf_std"] = indicators[f'{self._prefix_portfolio_indicator}perf'].rolling(window=interval).std()
        indicators[f"{self._prefix_portfolio_indicator}perf_bb_upper"] = indicators[f"{self._prefix_portfolio_indicator}perf_sma"] + 2 * indicators[f"{self._prefix_portfolio_indicator}perf_std"]
        indicators[f"{self._prefix_portfolio_indicator}perf_bb_lower"] = indicators[f"{self._prefix_portfolio_indicator}perf_sma"] - 2 * indicators[f"{self._prefix_portfolio_indicator}perf_std"]
        indicators[f"{self._prefix_portfolio_indicator}rsi"] = Portfolio.calculate_rsi(self.history, interval=interval)
        indicators[f"{self._prefix_portfolio_indicator}macd"], indicators[f"{self._prefix_portfolio_indicator}signal_line"], indicators[f"{self._prefix_portfolio_indicator}histogram"],  = Portfolio.calculate_macd(self.history)
        # indicators[f"{self._prefix_portfolio_indicator}mfi"] = Portfolio.calculate_mfi()
        
        if inplace == True:
            self.portfolio_tech_indicators=[col[len(self._prefix_portfolio_indicator):] for col in self.history.columns if col.startswith(self._prefix_portfolio_indicator)]
            return
        else:
            return indicators
        
    def get_symbol_tech_indicators(self, symbol, interval=14, inplace = True):
        if inplace == True:
            self.history[f"{self._prefix_symbol_indicator}{symbol}_mfi"] = Portfolio.calculate_mfi(self.history[f"{self._prefix_ticker}{symbol}_high"], self.history[f"{self._prefix_ticker}{symbol}_low"], self.history[f"{self._prefix_ticker}{symbol}_close"], self.history[f"{self._prefix_ticker}{symbol}_volume"], interval=interval)
            self.symbol_tech_indicators=[col[len(self._prefix_symbol_indicator):] for col in self.history.columns if col.startswith(self._prefix_symbol_indicator)]
            return
        else:
            indicators= pd.DataFrame()
            indicators[f"{self._prefix_symbol_indicator}{symbol}_mfi"] = Portfolio.calculate_mfi(self.history[f"{self._prefix_ticker}{symbol}_high"], self.history[f"{self._prefix_ticker}{symbol}_low"], self.history[f"{self._prefix_ticker}{symbol}_close"], self.history[f"{self._prefix_ticker}{symbol}_volume"], interval=interval)
            return indicators

# ----------------------------
# PRIVATE methods
# ----------------------------
    def _load_currencies(self):
        try:
            if isinstance(self.basedata, pd.DataFrame) and "currency" in  self.basedata.columns:
                self._currencies = {s:[] for s in list(set(list(self.basedata["currency"])))}
            return self._currencies
        except Exception as e:
            logging.error(f"Error: _currencies not found: {e}")
            return []

    def _load_basedata(self, added_item = None):
        """
            Fill self.basedata including currency info and exchange rates
        """
        if added_item is None:
            self.basedata = pd.DataFrame({"SYMBOL":list(set(list(self.transactions["SYMBOL"])))})
            infos = []
            for _, row in self.basedata.iterrows():
                ticker_info= _get_ticker_info(row["SYMBOL"])
                info = {"SYMBOL":row["SYMBOL"]}
                for k in self.selected_info_fields:
                    info[k] = ticker_info.get(k,None)
                infos.append(info)
            self.basedata = pd.DataFrame(infos)
            self._load_currencies()
            self._load_exchange_rates(rates_symbols=[f"{curr.upper()}{self.target_currency.upper()}=X" for curr in self._currencies])

        elif isinstance(added_item, pd.DataFrame) and isinstance(self.basedata, pd.DataFrame):
            if added_item["SYMBOL"].iloc[0] not in set(self.basedata["SYMBOL"]):
                ticker_info= _get_ticker_info(added_item["SYMBOL"].iloc[0])
                info = {"SYMBOL":added_item["SYMBOL"].iloc[0]}
                for k in self.selected_info_fields:
                    info[k] = ticker_info.get(k,None)
                added_item = pd.DataFrame([info])
                self.basedata = pd.concat([self.basedata,added_item])
                self.basedata.reindex()
                self._load_currencies()
                self._load_exchange_rates(rates_symbols=[f"{info['currency'].upper()}{self.target_currency.upper()}=X"])                         

    def _load_exchange_rates(self, rates_symbols, start = None, end = None, append = False):
        """
            Fill self._exchange_rates

        """
        if start is None: start = self.start_date
        if end  is None: end = datetime.today()
        joined_rates_symbols = ' '.join(rates_symbols)
        _rates = _get_rates(joined_rates_symbols, start, end)
        
        if not append:
            self._exchange_rates = pd.DataFrame(_rates).T
            self._exchange_rates.columns = rates_symbols
            self._exchange_rates[f"{self.target_currency.upper()}{self.target_currency.upper()}=X"] = 1.0
        else:
            df_rates=pd.DataFrame(_rates).T
            self.df_rates.columns = rates_symbols
            self._exchange_rates = pd.concat([self._exchange_rates, df_rates], axis=1)

        self._exchange_rates.index = self._exchange_rates.index.tz_localize(None)

# ----------------------------
# TECH INDICATOR methods
# ----------------------------
    @staticmethod
    def calculate_rsi(data, interval, symbol=""):
        # from https://www.pyquantnews.com/free-python-resources/python-for-trading-key-technical-indicators
        # makes sense for a single symbol and a portfolio
        if symbol!="": symbol+="_"
        delta = data[f"{symbol}close"].diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=interval).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=interval).mean()
        rs = gain / loss
        rsi=1-1/(1+rs)
        return rsi
    
    @staticmethod
    def calculate_macd(data, interval_1=12, interval_2=26, interval_3=9, symbol=""):
        # from https://www.pyquantnews.com/free-python-resources/python-for-trading-key-technical-indicators
        # makes sense for a single symbol and a portfolio
        if symbol!="": symbol+="_"
        data['EMA1'] = data['close'].ewm(span=interval_1, adjust=False).mean()
        data['EMA2'] = data['close'].ewm(span=interval_2, adjust=False).mean()
        data[f'{symbol}macd'] = data['EMA1'] - data['EMA2']
        data[f'{symbol}signal_line'] = data[f'{symbol}macd'].ewm(span=interval_3, adjust=False).mean()
        data[f'{symbol}histogram'] = data[f'{symbol}macd'] - data[f'{symbol}signal_line']
        data = data.drop(columns=["EMA1","EMA2"], axis=1)
        return data[f'{symbol}macd'], data[f'{symbol}signal_line'], data[f'{symbol}histogram']

    @staticmethod
    def calculate_mfi(high, low, close, volume, interval = 14):
        # from https://blog.quantinsti.com/build-technical-indicators-in-python/
        # makes only sense for a single symbol, not a portfolio
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume.astype(dtype=np.float64)
        mf_sign = np.where(typical_price > typical_price.shift(1), 1, -1)
        signed_mf = money_flow * mf_sign
        positive_mf = np.where(signed_mf > 0, signed_mf, 0)
        negative_mf = np.where(signed_mf < 0, -signed_mf, 0)
        mf_avg_gain = pd.Series(positive_mf).rolling(interval, min_periods=1).sum()
        mf_avg_loss = pd.Series(negative_mf).rolling(interval, min_periods=1).sum()
        return (1-1/(1+mf_avg_gain/mf_avg_loss)).to_numpy()

# ----------------------------
# HELPER static methods
# ----------------------------
    @staticmethod
    def _set_structure(struct):
        struct["DATE"]= pd.to_datetime(struct['DATE'], format="%d.%m.%Y")
        struct = struct.sort_values("DATE", ascending=True)
        struct = struct.set_index("DATE")
        struct.index = struct.index.tz_localize(None)
        return struct
