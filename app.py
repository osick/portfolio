import streamlit as st
from streamlit.components.v1 import html
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from datetime import datetime

if __name__ == "__main__":
    
    st.set_page_config(layout="wide")
    portfolio = pd.read_csv("account.csv", sep=";")
    fig = go.Figure()
    df_combined = pd.DataFrame()
    lst_symbols=[]

    for index, row in portfolio.iterrows():
        symbol = row["SYMBOL"]
        lst_symbols.append(symbol)
        start_date = datetime.strptime( row["Date"], '%d.%m.%Y')
        amount = row["AMOUNT"]

        try:
            ticker = yf.Ticker(symbol)
            ticker_df = ticker.history(start=start_date, end = datetime.now())
            df_combined[symbol] = ticker_df["Close"] * amount
            #fig.add_trace(go.Scatter(x=ticker_df.index, y=ticker_df['Close'], mode='lines', name=symbol))

        except Exception as e:
            st.warning(f"Failed to retrieve data for {symbol}: {e}")

    st.write(df_combined)
    df_combined['Close'] = df_combined[lst_symbols].sum(axis=1)
    fig.add_trace(go.Scatter(x=df_combined.index, y=df_combined['Close'], mode='lines', name="Total"))

    # Update graph layout
    fig.update_layout(
        title="Stock Closing Prices",
        xaxis_title="Date",
        yaxis_title="Close Price (USD)",
        template="plotly_dark",
        
        height=800
        
    )

        # Display graph
    st.plotly_chart(fig,use_container_width=True,height=800)
