import streamlit as st
from streamlit.components.v1 import html
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from datetime import datetime


@st.cache_data
def get_portfolio(csvfile):
    portfolio = pd.read_csv(csvfile, sep=",")
    portfolio["DATE"]= pd.to_datetime(portfolio['DATE'])
    portfolio.sort_values("DATE", inplace=True, ascending=True)
    portfolio.set_index("DATE", inplace=True)
    portfolio.index = portfolio.index.tz_localize(None)
    return portfolio

@st.cache_data
def get_exchange_rates(start,end):
    rates = ['USDEUR=X', 'GBPEUR=X']
    tickers = yf.Tickers(' '.join(rates))
    exchange_rates = []
    for i in tickers.tickers: exchange_rates.append(tickers.tickers[i].history(start=start, end=today).Close)
    ex_df = pd.DataFrame(exchange_rates).T
    ex_df.columns = rates
    ex_df['EUREUR=X'] = 1.0
    ex_df.index = ex_df.index.tz_localize(None)
    return ex_df

def add_help():
    help ="""
    ##### Structure of the CSV file  
    | NAME      | ISIN         | AMOUNT | BUY  | DATE       | SYMBOL | 
    |-----------|--------------|--------|------|------------|--------|  
    | ALLIANZ   | DE0008404005 | 11     | 2000 | 31.10.2021 | ALIZF  |
    | MICROSOFT | US5949181045 | 15     | 1000 | 31.10.2022 | MSFT   |
    | ...       | ...          | ...    | ...  | ...        | ...    |
    | ...       | ...          | ...    | ...  | ...        | ...    |
    
    Each line is a buy or sell transaction

    #### Columns
    **NAME**: arbitrary Identifier  
    **ISIN**: ISIN Number (optional)  
    **AMOUNT**: Number of shares  
    **BUY**: The total price (in EUR)  
    **DATE**: Buying Day (no Time or timezone Info nescessary)  
    **SYMBOL**: The symbol of the share  
    """
    st.divider()
    with st.popover("Help"): 
        st.markdown(help)


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("Portfolio Viewer")
    data_tab, history_tab, forecast_tab = st.tabs(["Portfolio Data 🗃", "Hístory 📈","Forecast"])
    with data_tab:
        st.header("Data")
    with history_tab:
        st.header("History")
    with forecast_tab:
        st.header("Forecast and Recommendation")

    # Upload CSV File
    with st.sidebar:
        st.subheader("Upload Portfolio as CSV")
        uploaded_file = st.file_uploader("", type=["csv"])
        with open("portfolio.sample.csv","r") as fh: 
            text_contents=fh.read()

    if uploaded_file:
        with st.spinner("Computing the Portfolio Chart..."):
            portfolio = get_portfolio(uploaded_file)
            with data_tab:
                st.dataframe(portfolio, use_container_width= True, )
            with st.sidebar:
                st.divider()
                st.subheader("Select Portfolio symbols")
                data_frame = st.dataframe(list(set(portfolio["SYMBOL"])), hide_index=True, use_container_width= True, on_select="rerun", selection_mode="multi-row")
            symbols={s:[] for s in list(set(list(portfolio["SYMBOL"])))}
            options=list(symbols.keys())

            today = datetime.now()
            # portfolio.index[0] is the first date of the portfolio
            ex_df = get_exchange_rates(portfolio.index[0],today)

            fig = go.Figure()    

            df_combined = pd.DataFrame()
            for index, row in portfolio.iterrows():
                try:
                    symbols[row["SYMBOL"]].append(index)
                    ticker = yf.Ticker(row["SYMBOL"])
                    exchange_factor = ex_df[f'{ticker.info["currency"]}EUR=X']

                    ticker_df = ticker.history(start=index, end=today)
                    ticker_df.index = ticker_df.index.tz_localize(None)
                    # TOTAL Value per share
                    df_combined[f'{row["SYMBOL"]}_{index}_close'] = ticker_df["Close"] * row["AMOUNT"] * exchange_factor
                    df_combined[f'{row["SYMBOL"]}_{index}_close'].interpolate(inplace=True) 

                    # BUY Value per share
                    ticker_df["BUY"]= row["BUY"]
                    df_combined[f'{row["SYMBOL"]}_{index}_buy'] = ticker_df["BUY"]
                    df_combined[f'{row["SYMBOL"]}_{index}_buy'].interpolate(inplace=True) 

                except Exception as e:
                    st.warning(f"Failed to retrieve data for {symbols[-1]}: {e}")


            df_combined[f'_close'] = df_combined[[f"{symbol}_{index}_close" for symbol in symbols.keys() for index in symbols[symbol] ]].sum(axis=1)
            df_combined[f'_buy']   = df_combined[[f"{symbol}_{index}_buy"   for symbol in symbols.keys() for index in symbols[symbol] ]].sum(axis=1)   
            df_combined[f'_win']   = df_combined[f'_close'] - df_combined[f'_buy']
            

            fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'_close'], mode='lines', name=f"Total"))
            fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'_buy'], mode='lines', name=f"Buy"))
            fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined[f'_win'], mode='lines', name=f"Win"))

            # Update graph layout
            fig.update_layout(title="", xaxis_title="Date", yaxis_title="EUR", template="plotly_dark", height=800)
            fig.update_layout(yaxis_range=[0,df_combined["_close"].max()])
            # Display graph
            with history_tab:
                st.plotly_chart(fig,use_container_width=True,height=800)
            with forecast_tab:
                st.write("tbd")
    with st.sidebar:
        add_help()
