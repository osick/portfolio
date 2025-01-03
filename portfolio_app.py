import streamlit as st
from streamlit.components.v1 import html
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from prophet import Prophet
from datetime import datetime
from portfolio.portfolio import Portfolio
import os


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
        upl_file = st.file_uploader(":blue[**1.Upload Portfolio**]", type=["csv"])

    return data_tab, history_tab, forecast_tab, help_tab, upl_file


if __name__ == "__main__":

    data_tab, history_tab, forecast_tab, help_tab, upl_file = st_init()
    my_portfolio = Portfolio()
    interval=20

    if upl_file:
        with st.spinner("Your Shares..."):
            my_portfolio.from_csv(upl_file.name)
            my_portfolio.compute_tech_indicators(interval = interval)
            
            with data_tab:
                    if 'portfolio' not in st.session_state: st.session_state.portfolio = my_portfolio.basedata
                    new_df = st.data_editor(st.session_state.portfolio, use_container_width=True, hide_index=False, num_rows="dynamic")
                    st.session_state.portfolio = new_df
            with history_tab:
                pass
            with st.sidebar:
                selected_shares = st.multiselect(f":blue[**2.Select Symbols from {upl_file.name}**]", my_portfolio.basedata["SYMBOL"], default = my_portfolio.basedata["SYMBOL"])
                indicators = st.multiselect(":blue[**3.Select Indicators**]", my_portfolio.tech_indicators, default=[], key="indicators", format_func=lambda x: str(x))
                interval = st.slider(label=":blue[**4.Set Interval for indicators**]",min_value=1, max_value=365, value=60, key="interval")

        if selected_shares or new_df:
            with st.spinner("compute Portfolio history..."):
                # specific Stock Data 
                df_combined, symbols = get_history(st.session_state.portfolio, ex_df)
                symbols = {s:i for s,i in symbols.items() if s in selected_shares}
                df_combined =  refine_for_symbols(df_combined, symbols, interval)

                # Display graph
                fig = make_portfolio_fig(df_combined, interval=interval, indicators=indicators)

                with history_tab:
                    st.markdown(f""" <style>.stPlotlyChart {{ border-radius: 6px; box-shadow: 0 8px 12px 0 rgba(0, 0, 0, 0.20), 0 6px 20px 0 rgba(0, 0, 0, 0.30); }}</style>""", unsafe_allow_html=True)
                    fig.update_layout(title=f'                  History Graph for {", ".join(list(symbols.keys()))}')
                    fig.update_layout(paper_bgcolor="#ffffff")
                    st.plotly_chart(fig,use_container_width=True,height=800, theme="streamlit")
                
                # Analysis and prognosis
                with forecast_tab:
                    st.write("tbd")
