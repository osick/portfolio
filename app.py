import streamlit as st
from streamlit.components.v1 import html
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from prophet import Prophet
from datetime import datetime

@st.cache_data
def get_portfolio(csvfile):
    try:
        portfolio = pd.read_csv(csvfile, sep=",")
        portfolio["DATE"]= pd.to_datetime(portfolio['DATE'])
        portfolio = portfolio.sort_values("DATE", ascending=True)
        portfolio = portfolio.set_index("DATE")
        portfolio.index = portfolio.index.tz_localize(None)
        return portfolio
    except Exception as e:
        st.error(f"Portfolio could not be loaded from {csvfile} ")
        return pd.DataFrame()

@st.cache_data
def get_exchange_rates(start,end):
    rates = ['USDEUR=X', 'GBPEUR=X']
    try:
        tickers = yf.Tickers(' '.join(rates))
        exchange_rates = []
        for i in tickers.tickers: exchange_rates.append(tickers.tickers[i].history(start=start, end=end).Close)
        ex_df = pd.DataFrame(exchange_rates).T
        ex_df.columns = rates
        ex_df['EUREUR=X'] = 1.0
        ex_df.index = ex_df.index.tz_localize(None)
        return ex_df
    except Exception as e:
        st.error(f"Error: Exchange rates not found")
        return pd.DataFrame()

def add_help():
    help ="""
    ### :red[Usage]
    * *Step 1* : Upload a file describing the Portfolio. CSV informations see below
    * *Step 2* :Select the shares you are interested in
    * *Step 3* :Select the indicators you are interested in

    All derived informations are then given on the three tabs 
    * *Summary* : List of all portfolio transactions with basic data for each transaction
    * *History* : Chart of historical Data beginning with the start of the portfolio
    * *Forecast*: Forecast based on imes series analysis and AI  

    #### :red[CSV Structure example]
        | NAME      | ISIN         | AMOUNT | BUY  | DATE       | SYMBOL | 
        |-----------|--------------|--------|------|------------|--------|  
        | ALLIANZ   | DE0008404005 | 11     | 2000 | 31.10.2021 | ALIZF  |
        | MICROSOFT | US5949181045 | 15     | 1000 | 31.10.2022 | MSFT   |
        | ...       | ...          | ...    | ...  | ...        | ...    |
        | ...       | ...          | ...    | ...  | ...        | ...    |
    
    Each line is a buy or sell transaction. The :red[Columns] are defined as follows:

        | FIELD      | Description                                          |
        |------------|------------------------------------------------------| 
        | **NAME**   | arbitrary Identifier                                 |  
        | **ISIN**   | ISIN Number (optional)                               |  
        | **AMOUNT** | Number of shares                                     |  
        | **BUY**    | The total price (in EUR)                             |   
        | **DATE**   | Buying Day (no Time or timezone Info nescessary)     | 
        | **SYMBOL** | The symbol of the share                              | 
    """
    st.markdown(help)

def get_history(_portfolio, _exchange_rates):
    df_combined = pd.DataFrame()
    try:
        symbols={s:[] for s in list(set(list(portfolio["SYMBOL"])))}    
        for index, row in _portfolio.iterrows():
            symbols[row["SYMBOL"]].append(index)
            ticker = yf.Ticker(row["SYMBOL"])
            exchange_factor = _exchange_rates[f'{ticker.info["currency"]}EUR=X']

            ticker_df = ticker.history(start=index, end=today)
            ticker_df.index = ticker_df.index.tz_localize(None)
            
            # TOTAL Value per share
            df_combined[f'{row["SYMBOL"]}_{index}_close'] = ticker_df["Close"] * row["AMOUNT"] * exchange_factor
            df_combined[f'{row["SYMBOL"]}_{index}_close'] = df_combined[f'{row["SYMBOL"]}_{index}_close'].interpolate()
            
            # BUY Value per share
            ticker_df["BUY"]= row["BUY"]
            df_combined[f'{row["SYMBOL"]}_{index}_buy'] = ticker_df["BUY"]
            df_combined[f'{row["SYMBOL"]}_{index}_buy'] = df_combined[f'{row["SYMBOL"]}_{index}_buy'].interpolate() 
        return df_combined, symbols
    except Exception as e:
        st.error(f"could not do history analysis on the portfolio: {e}")
        return pd.DataFrame(), {}

@st.cache_data
def get_ticker_history(symbol,  start, end):
    df = pd.DataFrame()
    ticker = yf.Ticker(symbol)
    ticker_df = ticker.history(start=start, end=end)
    ticker_df.index = ticker_df.index.tz_localize(None)
    df[f'{symbol}_{start}_close'] = ticker_df["Close"]
    return df, ticker.info["currency"]

def refine_for_symbols(df_combined, symbols,interval):
    try:
        df_combined[f'_close'] = df_combined[[f"{symbol}_{index}_close" for symbol in symbols.keys() for index in symbols[symbol] ]].sum(axis=1)
        df_combined[f'_buy']   = df_combined[[f"{symbol}_{index}_buy"   for symbol in symbols.keys() for index in symbols[symbol] ]].sum(axis=1)   
        df_combined[f'_win']   = df_combined[f'_close'] - df_combined[f'_buy']
        df_combined["sma"] = df_combined['_close'].rolling(window=interval).mean()
        df_combined["ema"] = df_combined['_close'].ewm(span=interval).mean()
        df_combined["std"] = df_combined['_close'].rolling(window=interval).std()
        df_combined["bb_upper"] = df_combined["sma"] + 2 * df_combined["std"]
        df_combined["bb_lower"] = df_combined["sma"] - 2 * df_combined["std"]


        df_combined[f'performance'] = df_combined[f'_win'] / df_combined[f'_buy']
        df_combined["performance_sma"] = df_combined['performance'].rolling(window=interval).mean()
        df_combined["performance_ema"] = df_combined['performance'].ewm(span=interval).mean()
        df_combined["performance_std"] = df_combined['performance'].rolling(window=interval).std()
        df_combined["performance_bb_upper"] = df_combined["performance_sma"] + 2 * df_combined["performance_std"]
        df_combined["performance_bb_lower"] = df_combined["performance_sma"] - 2 * df_combined["performance_std"]
        return df_combined
    except Exception as e:
        st.error(f"cannot refine for symbols{symbols}. Error:{e}")
        return df_combined

@st.cache_data
def make_portfolio_fig(df_combined, interval, indicators=[], ):
    try:
        fig = make_subplots(specs=[[{"secondary_y": True}]])  
        fig.update_layout(legend=dict(x=0, y=1.11, orientation='h', font=dict(family="Times New Roman", size=14, color="#404040"), bordercolor="Black", bgcolor="#ffffff", borderwidth=0),)

        # primary yaxis
        fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'_buy'], mode='lines',  name=f"€ Buy", line=dict(color="#ffe490"), fill="tonexty",  ), secondary_y=False,)
        fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'_close'], line=dict(color="#a0ff90"),  fill="tonexty",  mode='lines', name=f"€ Win" ), secondary_y=False,)
        if "SMA"  in indicators: fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'sma'], mode='lines', name=f"SMA ({interval}d)" ), secondary_y=False,)
        if "EMA"  in indicators: fig.add_trace(go.Scatter( x=df_combined.index, y=df_combined[f'ema'],  mode='lines',  name=f"EMA ({interval}d)" ), secondary_y=False,)
        if "BB"   in indicators:
            fig.add_trace(go.Scatter( x=df_combined.index,  y=df_combined["bb_lower"], mode='lines', name=f"BB_lower ({interval}d)"), secondary_y=False,)
            fig.add_trace(go.Scatter( x=df_combined.index,  y=df_combined["bb_upper"], mode='lines',  name=f"BB_upper ({interval}d)"), secondary_y=False,)

        # secondary yaxis
        if "% Perf." in indicators: fig.add_trace(go.Scatter( x=df_combined.index,  y=df_combined[f'performance'],  mode='lines',  name=f"Win in %" ), secondary_y=True,)
        if "% SMA"   in indicators: fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'performance_sma'], mode='lines', name=f"% SMA ({interval}d)" ), secondary_y=True,)
        if "% EMA"   in indicators: fig.add_trace(go.Scatter( x=df_combined.index, y=df_combined[f'performance_ema'],  mode='lines',  name=f"% EMA ({interval}d)" ), secondary_y=True,)
        if "% BB"    in indicators:
            fig.add_trace(go.Scatter( x=df_combined.index,  y=df_combined["performance_bb_lower"], mode='lines', name=f"% BB_lower ({interval}d)"), secondary_y=True,)
            fig.add_trace(go.Scatter( x=df_combined.index,  y=df_combined["performance_bb_upper"], mode='lines',  name=f"% BB_upper ({interval}d)"), secondary_y=True,)
        
        fig.update_xaxes(title_text="<b>History</b>")
        fig.update_yaxes(title_text="<b>EUR</b>", secondary_y=False, tickprefix='€', range=[0, df_combined[f'_close'].max()*1.2])
        fig.update_yaxes(title_text="<b>Yield in %</b>", secondary_y=True, tickformat=".0%", range=[0, df_combined[f'performance'].max()*1.2])
        return fig
    except Exception as e:
        st.error("cannof create figure for Portfolio, Error:{e}")
        return make_subplots(specs=[[{"secondary_y": True}]])  

if __name__ == "__main__":

    st.set_page_config(layout="wide")
    st.header("Portfolio")
    data_tab, history_tab, forecast_tab, help_tab = st.tabs([f"**Summary**", "**History**","**Forecast**","**Help**"])
    with data_tab:      pass # st.header("Data")
    with history_tab:   pass # st.header("History")
    with forecast_tab:  pass # st.header("Forecast and Recommendation")
    with help_tab:      add_help()

    # Upload CSV File
    with st.sidebar:
        st.markdown("""<style>.block-container {padding-top: 2.5rem; padding-bottom: 1rem;}</style>""", unsafe_allow_html=True, )

        css = '''
            <style>
                [data-testid='stFileUploader'] * {padding:0;margin:4px;vertical-align:center}
                [data-testid='stFileUploader'] section > input + div {display:none;}
                [data-testid='stFileUploader'] section + div {float: right; padding: 0;display:none;}
                [data-testid='stSidebarHeader'] {float: right; padding: 0;display:visible ;}
                .stTextInput > span {font-size:60%;  font-weight:bold; color:blue;}
                .stMultiSelect > span {font-size:60%; font-weight:bold; color:blue;} 
                .stTabs [data-baseweb="tab"] {height: 20px; white-space: pre-wrap; background-color: #eeeeee; color: #000000; padding: 15px;}
                .stTabs [aria-selected="true"] {background-color: #404040; color: #ffff00;}
            </style>'''
        st.markdown(css, unsafe_allow_html=True)
        upl_file = st.file_uploader(":blue[**1.Upload Portfolio**]", type=["csv"])

    if upl_file:
        with st.spinner("Your Shares..."):
            portfolio = get_portfolio(upl_file)
            today = datetime.now()
            begin = portfolio.index[0]
            ex_df = get_exchange_rates(begin,today)
            
            with data_tab:
                st.dataframe(portfolio, use_container_width= True, )
            with history_tab:
                pass
            with st.sidebar:
                st.markdown(
                    """
                    <style> 
                        span[data-baseweb="tag"] {background-color: #e0e0e0 !important; color: #000000 !important; font-size:90%;padding:8px; width:4.5rem}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                lst_indicators =["% Perf.", "% SMA", "% EMA", "% BB", "SMA", "EMA", "BB"]
                lst_portfolio = list(set(portfolio["SYMBOL"]))
                selected_shares = st.multiselect(f":blue[**2.Select Symbols from {upl_file.name}**]", lst_portfolio, default=lst_portfolio)
                indicators = st.multiselect(":blue[**3.Select Indicators**]", lst_indicators , default=["% Perf."], key="indicators", format_func=lambda x: str(x))
                interval = st.slider(label=":blue[**4.Set Interval for indicators**]",min_value=1, max_value=365, value=60,  key="interval")
                #share_selector = st.button("Load Data into Chart", use_container_width=True, type="primary")

        if indicators:
            with st.spinner("compute Portfolio history..."):

                # specific Stock Data 
                df_combined, symbols = get_history(portfolio, ex_df)
                symbols = {s:i for s,i in symbols.items() if s in selected_shares}
                df_combined =  refine_for_symbols(df_combined, symbols, interval)

                # Display graph
                fig = make_portfolio_fig(df_combined, interval=interval, indicators=indicators)
                with history_tab:
                    PLOT_BGCOLOR = "#ffffff"
                    st.markdown(
                        f"""
                        <style>
                        .stPlotlyChart {{
                        border-radius: 6px;
                        box-shadow: 0 8px 12px 0 rgba(0, 0, 0, 0.20), 0 6px 20px 0 rgba(0, 0, 0, 0.30);
                        }}
                        </style>
                        """, unsafe_allow_html=True
                    )
                    fig.update_layout(title=f'                  History Graph for {", ".join(list(symbols.keys()))}')
                    fig.update_layout(paper_bgcolor=PLOT_BGCOLOR)
                    st.plotly_chart(fig,use_container_width=True,height=800, theme="streamlit")
                
                # Analysis and prognosis
                with forecast_tab:
                    st.write("tbd")

