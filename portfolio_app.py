import streamlit as st
from streamlit.components.v1 import html
import pandas as pd

from prophet import Prophet
from datetime import datetime
from portfolio import Portfolio
from portfolio.presentation import Figure
import os



def st_init():
    st.set_page_config(layout="wide")
    st.markdown("## Portfolio")
    data_tab, history_tab, forecast_tab, help_tab = st.tabs([f"**Summary**", "**History**","**Forecast**","**Help**"])
    with data_tab: pass 
    with history_tab: pass 
    with forecast_tab: pass 
    with help_tab: 
        with open("Readme.md") as fh:
            help = fh.read().split("<!--CUT-->")[-1] 
        st.markdown(help, unsafe_allow_html=True)
    with st.sidebar:
        with open(os.path.join("data","css","sidebar.css"),"r") as fh:
            style=fh.read()
            st.markdown(f"<style>{style}</style>" , unsafe_allow_html=True)

    return data_tab, history_tab, forecast_tab, help_tab
 

if __name__ == "__main__":

    data_tab, history_tab, forecast_tab, help_tab, = st_init()
    with st.sidebar:
        upl_file = st.file_uploader(":blue[**1.Upload Portfolio**]", type=["csv"])

    my_portfolio = Portfolio()
    interval=20

    if upl_file:
        with st.spinner("Your Shares..."):
            my_portfolio.from_csv(upl_file)
            my_portfolio.load_history()
            my_portfolio.aggregate_to(level="portfolio", inplace=True)
            my_portfolio.get_portfolio_tech_indicators(inplace=True, filter_symbols= None, interval=interval)
            
            with data_tab:
                if 'transactions' not in st.session_state: st.session_state.transactions = my_portfolio.transactions
                new_df = st.data_editor(st.session_state.transactions, use_container_width=True, hide_index=False, num_rows="dynamic")
                st.session_state.transactions = new_df
            with history_tab:
                pass
            with st.sidebar:
                selected_shares = st.multiselect(
                    f":blue[**2.Select Symbols from {upl_file.name}**]", 
                    my_portfolio.basedata["SYMBOL"], 
                    default = my_portfolio.basedata["SYMBOL"])


                indicators = st.multiselect(
                    ":blue[**3.Select Indicators**]", 
                    my_portfolio.portfolio_tech_indicators, 
                    default=[], 
                    key="indicators", 
                    format_func=lambda x: str(x))
                
                interval = st.slider(
                    label=":blue[**4.Set Interval for indicators**]",
                    min_value=1, 
                    max_value=365, 
                    value=60, 
                    key="interval")

        if selected_shares or new_df:
            with st.spinner("compute Portfolio history..."):
                # specific Stock Data 
                my_portfolio.load_history()
                my_portfolio.aggregate_to(level="portfolio", inplace=True)
                st.table(my_portfolio.history.columns)
                my_portfolio.get_portfolio_tech_indicators(interval=interval,inplace=True)

                # Display graph
                my_figure = Figure(my_portfolio)
                fig = my_figure.fig()
                with history_tab:
                    st.markdown(f""" <style></style>""", unsafe_allow_html=True)
                    fig.update_layout(title=f'                  History Graph for {", ".join(list(my_portfolio.basedata["SYMBOL"]))}')
                    fig.update_layout(paper_bgcolor="#ffffff")
                    st.plotly_chart(fig,use_container_width=True,height=800, theme="streamlit")
                
                # Analysis and prognosis
                with forecast_tab:
                    st.write("tbd")
