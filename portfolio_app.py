import streamlit as st
from streamlit.components.v1 import html
from streamlit_navigation_bar import st_navbar

import pandas as pd
from portfolio import Portfolio
from portfolio.presentation import Figure
from portfolio.ai import AI
import os

def st_init():
    st.set_page_config(initial_sidebar_state="collapsed",layout="wide")
    st.markdown("### Portfolio")
    expanders_json =get_expanders()
    transaction_exp = expanders_json["transaction"]["exp"] 
    history_exp = expanders_json["history"]["exp"]
    forecast_exp = expanders_json["forecast"]["exp"]
    ai_exp = expanders_json["ai"]["exp"]
    help_exp = expanders_json["help"]["exp"] 


    with st.sidebar:
        with open(os.path.join("data","css","sidebar.css"),"r") as fh: 
            st.markdown(f"<style>{fh.read()}</style>" , unsafe_allow_html=True)
        #with st.expander(f":blue[**Upload Portfolio**]",expanded=False):   
        upl_file = st.file_uploader("Upload", type=["csv"],label_visibility="collapsed")

        main_menu = st.selectbox("Menu", ("Summary","Transactions", "History", "Forecast", "AI"), label_visibility="collapsed", disabled=False, key="command")

    return transaction_exp, history_exp, forecast_exp, ai_exp, help_exp, upl_file
 
def get_expanders():

    ui_json={
        "transaction" :{"exp":None}, 
        "history" :{"exp":None, "btn":None}, 
        "forecast" :{"exp":None, "btn":None}, 
        "ai" :{"exp":None, "btn":None}, 
        "help" :{"exp":None, "btn":None}}

    for exp,o in ui_json.items():
        if "exp" in o:
            exp = exp+"_exp"
            if f"{exp}_expanded" not in st.session_state: st.session_state[f"{exp}_expanded"] = True
            o["exp"] = st.expander(f"### {exp.capitalize()}", expanded=st.session_state[f"{exp}_expanded"])
            with o["exp"]: 
                if "btn" in o:
                    if f"{exp}_btn_disabled" not in st.session_state: st.session_state[f"{exp}_btn_disabled"] = False
                    o["btn"] = st.button("load", disabled = st.session_state[f"{exp}_btn_disabled"], key=f"{exp}_btn_key")
                else:
                    st.write("")
    return ui_json


def prepare_portfolio(p, upl_file):
    p.from_csv(upl_file)
    p.load_history()
    p.aggregate_to(level="portfolio", inplace=True)
    p.get_portfolio_tech_indicators(inplace=True, symbols= None, interval=interval)
            
def get_ai_response(fig, type="Llama"):
    image_data=Figure.chart_to_image(fig)
    ai = AI()
    response = ai.ask(type=type,image_data=image_data) 
    return response
    
def get_command_buttons():
    with st.sidebar:
        c1,c2,c3= st.columns(3)
        with c1:
            load_history_btn = st.button("History",)
        with c2:
            load_forecast_btn = st.button("Forecast")
        with c3:
            load_ai_btn = st.button("AI analysis")
    return load_history_btn, load_forecast_btn, load_ai_btn

def get_fig(my_portfolio):
    my_portfolio.load_history()
    my_portfolio.aggregate_to(level="portfolio", inplace=True)
    my_portfolio.get_portfolio_tech_indicators(interval=interval,inplace=True)
    my_figure = Figure(my_portfolio)
    exclude = list(set(my_portfolio.portfolio_tech_indicators) -set(indicators))
    exclude = "||".join(exclude)
    fig = my_figure.fig(exclude=exclude, secondary_y_stretch=1.2, primary_y_stretch=1.2, sep ="||")
    return fig

if __name__ == "__main__":
    
    transaction_exp, history_exp, forecast_exp, ai_exp, help_exp, upl_file = st_init()
    
    my_portfolio = Portfolio()
    

    if upl_file:
        with st.spinner("Loading Portfolio..."):
            prepare_portfolio(my_portfolio, upl_file)

            with transaction_exp:
                if "my_portfolio" not in st.session_state: st.session_state.my_portfolio = my_portfolio
                data_editor = st.data_editor(st.session_state.my_portfolio.transactions, use_container_width=True, hide_index=False, num_rows="dynamic")
                st.session_state.transactions = data_editor
            
            with st.sidebar:
                with st.expander(f":blue[**Symbols from {upl_file.name}**]"):
                    selected_shares = st.multiselect(" ", my_portfolio.basedata["SYMBOL"], default = my_portfolio.basedata["SYMBOL"])
                with st.expander(":blue[**Indicators**]"):
                    indicators = st.multiselect(" ", my_portfolio.portfolio_tech_indicators, default=my_portfolio.portfolio_tech_indicators, key="indicators", format_func=lambda x: str(x))                
                with st.expander(f":blue[**Config**]"):
                    interval = st.slider(label=":blue[**indicators interval**]", min_value=1, max_value=365, value=60, key="interval")
                    date_range = st.slider(label=":blue[**Date Range**]", min_value=1, max_value=365, value=60, key="date_range")
                st.markdown("## Commands")        
            load_history_btn, load_forecast_btn, load_ai_btn = get_command_buttons()


    with history_exp:
        if load_history_btn:
            st.session_state.history_exp_expanded = True
            with st.spinner("Getting Portfolio graph..."):
                if "fig" not in st.session_state: 
                    fig = get_fig(my_portfolio)
                    st.session_state.fig = fig            
        if "fig" in st.session_state: 
            st.session_state.fig.update_layout(title="\t\t"+f'{", ".join(list(my_portfolio.basedata["SYMBOL"]))}')
            st.session_state.fig.update_layout(paper_bgcolor="#ffffff")
            st.plotly_chart(st.session_state.fig,use_container_width=True,height=600, theme="streamlit")
        else:
            st.empty()


    with forecast_exp:
        if load_forecast_btn:
            st.session_state.forecast_exp_expanded = True
            with st.spinner("Computing Forecast..."):
                if "my_portfolio" in st.session_state:
                    st.write("tbd")
        else:
            st.empty()


    with ai_exp:
        if load_ai_btn:
            st.session_state.ai_exp_expanded = True
            with st.spinner("AI analysis by graph analysis..."):
                if "fig" in st.session_state:
                    response=get_ai_response(st.session_state["fig"])
                    st.markdown(response)
                    if 'response' not in st.session_state: st.session_state.response=response
                else:
                    @st.dialog("Warning")
                    def x(): st.write("First you need to generate a history graph with relevant stocks and indicators, then AI analysis ist possible.")
                    x()
        else:
            st.empty()

