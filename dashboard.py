import streamlit as st
from io import StringIO
import pandas as pd
from portfolio import Portfolio
from portfolio.presentation import Figure
from portfolio.ai import AI
from portfolio.sentiment import Sentiment

import os
import time
import datetime

def load_css(filepath):
    with open(os.path.join("data","css",filepath),"r") as fh: 
        st.markdown(f"<style>{fh.read()}</style>" , unsafe_allow_html=True)

def get_ai_response(fig, type="Llama"):
    image_path=Figure.fig_to_base64(fig)
    ai = AI()
    response = ai.ask(type=type, image_data=image_path) 
    return response

def get_fig(_portfolio, date_range, title:str=None):
    calc_portfolio(_portfolio,selected_only=True)
    my_figure = Figure(_portfolio)
    exclude = list(set(_portfolio.portfolio_tech_indicators) -set(st.session_state._indicators))
    exclude = "||".join(exclude)
    exclude = None
    fig = my_figure.fig(date_range, exclude=exclude, secondary_y_stretch=1.0, primary_y_stretch=1.0, sep ="||")
    if title is None: title = f'{", ".join(list(_portfolio.basedata["SYMBOL"]))}'
    fig.update_layout(title={ 'text': title, 'y':0.95,  'x':0.5, 'xanchor':'center', 'yanchor': 'top'})
    return fig

def section_title(text:str, level=1):
    """
        Generates a h3 header and returns th corresponding anchor id

        Input:
        ------
        text: str
            he text of the header

        Return:
        -------

        id:str
            The anchor id

    """
    id=f"{text.replace(' ','')}"

    if level==1:
        st.markdown(f"<h3 class='sectiontitle_1' id='{id.lower()}'>{text}</h3>",unsafe_allow_html=True)
    elif level==2:
        st.markdown(f"<h3 class='sectiontitle_1 sectiontitle_2' id='{id.lower()}'>{text}</h3>",unsafe_allow_html=True)
    return id

def st_reset_session():
    for state  in ["ai_response","fig","portfolio","recommendation","sentiment","sentiment_value""sentiment_result","forecast","forecast_delta"]:
        if state in st.session_state:
            del st.session_state[state]

def reload_transactions(_portfolio, selected_only=True):
    _portfolio.load_transactions(st_data_editor)
    calc_portfolio(_portfolio, selected_only=selected_only)

def calc_portfolio(_portfolio, selected_only=True):
    _portfolio.load_history(selected_only=selected_only)
    _portfolio.aggregate_to(level="portfolio", inplace=True, selected_only=selected_only)
    _portfolio.get_portfolio_tech_indicators(inplace=True, symbols= None, interval=interval)

def navbar(entries:dict):
    with open(os.path.join("data","markdown","navbar.header.markdown")) as fh:
        nav_header=fh.read()
        nav_items=[]
    for name, link in entries.items():
        nav_item =f'<li class="nav-item"><a class="nav-link" href="{link.lower()}" id="id_{name.upper()}"><span style="color:white">{name.upper()}</span></a></li>'
        nav_items.append(nav_item)
        
    nav_bar = nav_header.replace("{NAV_ITEMS}", "\n".join(nav_items))

    with open(os.path.join("data","markdown","navbar.bottom.markdown")) as fh:
        nav_bottom=fh.read()

    return nav_bar, nav_bottom  

def load_portfolio(_portfolio:Portfolio, reset = True, uploader = None, df = None):
    if reset:
        st.cache_data.clear()
        st_reset_session()
        if "portfolio" in st.session_state: del st.session_state["portfolio"]
    _portfolio._init_data()
    if uploader is not None:
        _portfolio.from_csv(st_uploader)
        calc_portfolio(_portfolio)
    if df is not None:
        if "file_uploader_key" in  st.session_state: st.session_state["file_uploader_key"] += 1
        _portfolio.load_transactions(df=df)
        calc_portfolio(_portfolio)
    
    st.session_state.portfolio = _portfolio

if __name__ == "__main__":

    if "portfolio" not in st.session_state: st.session_state.portfolio=Portfolio()

    # initial config
    st.set_page_config(initial_sidebar_state="expanded",layout="wide")
    load_css("dashboard.css")

    entries = {"SUMMARY":"#Summary", "DATA":"#Data", "CHARTS":"#technical-analysis", "AI Analysis":"#AI", "HELP & DISCLAIMER":"#Help", "ABOUT":"#About"}
    nav_bottom, nav_header= navbar(entries)
    st.markdown(nav_bottom, unsafe_allow_html=True)

    with st.sidebar:
        section_title("Load")
        ticker1,ticker2,ticker3 = st.columns([3,3,3])
        if "file_uploader_key" not in st.session_state: st.session_state["file_uploader_key"] = 0
        with ticker1:   st_uploader = st.file_uploader("**Upload**", type=["csv"],label_visibility="collapsed", key=f'upload_{st.session_state["file_uploader_key"]}')
        with ticker2:   st_load_ticker=st.button("**Load Ticker**", use_container_width=True,)
        with ticker3:   st_ticker_text = st.text_input("Ticker Symbol", label_visibility="collapsed", placeholder="Ticker Symbol", key="ticker_symbol",max_chars=10)

        section_title("Commands")
        head1, head2 = st.columns([2,2])
        with head1:     analyze_btn= st.button("**Analyze**", use_container_width=True,)
        with head2:     st_downloader = st.button("**Save**",use_container_width=True, key="_downloader")

        st_commands=st.container(border=False, height=20, key="commands")

        section_title("Configuration")
        # interval of days
        interval = st.slider(label=":blue[**Indicators interval**]", min_value=1, max_value=365, value=30, key="interval")

        # data rage from today on into the past
        date_range = st.slider(label=":blue[**Date Range**]", min_value=1, max_value=365*3, value=365, key="date_range")

        # selection of indicators
        st_indicators = st.multiselect("Choose Indicators", st.session_state.portfolio.portfolio_tech_indicators , placeholder="Choose technical indicator", default=None, key="_indicators", format_func=lambda x: str(x))     
        
        ai_type = st.selectbox("Choose AI model", ["chatgpt","llama", "llava"], index=0, label_visibility="visible", key="ai_type")
        
        # p1, p2, p3 = st.columns(3)
        # with p1:
        #     with st.popover("App help "):
        #         section_title("Help")
        #         help=open("Readme.md","r").read().split("<!--CUT-->")[-1]
        #         st.markdown(help, unsafe_allow_html=True)
        # with p2:
        #     with st.popover("Disclaimer"):
        #         disclaimer=open("Disclaimer.md","r").read()
        #         st.markdown(disclaimer, unsafe_allow_html=True)
        # with p3:
        #     if st.button("id_SUMMARY"):
        #         with st.popover("About it"):        
        #             st.markdown("""
        #             This simple app can be used to view and analyse your stock portfolio with different approaches. 
        #             * For more see the <a href='#Help'>Help section</a>. 
        #             * And be careful, see the <a href='#Disclaimer'>Disclaimer</a>
        #             """, unsafe_allow_html=True)


    section_title("Portfolio")
    portfolio_container = st.container()
    with portfolio_container:
        col_metrics,col_chart=st.columns([2,5])
        with col_metrics:
            section_title("Metrics and Chart",2)
            m1,m2,m3 = st.columns(3)
            m4,m5,m6 = st.columns(3)

        
    section_title("Analysis")    
    t1,t2,t3 = st.columns([1,50,1])
    with t2:
        #analysis_container = st.expander("History, Forecast, Sentiment and AI")
        analysis_container = st.container()
        with analysis_container:
            section_title("Transaction List",2)
            exp_data = st.container(border=False)
            with exp_data:    
                trans_col, sym_col = st.columns([7,1])
                with trans_col: st.write(" ")
                with sym_col: st.write(" ")

            section_title("History",2)
            with st.container(border=False):
                st_cont_history=st.container()
                with st_cont_history: st.write(" ")
                st_cont_chart = st.container()
                with st_cont_chart: st.write(" ")

            section_title("Forecast (TBD)",2)
            st_cont_forecast=st.container(border=False)
            with st_cont_forecast: st.write(" ")

            section_title("Sentiment",2)
            st_cont_sentiment = st.container(border=False)
            with st_cont_sentiment: st.write(" ")
            
            section_title("AI Analysis",2)
            st_cont_ai = st.container(border=False)
            with st_cont_ai: st.write(" ")
        
    if st_uploader or st_load_ticker or analyze_btn:
        with st_commands:
            if st_uploader or st_load_ticker:
                with st.spinner("Loading Portfolio..."):
                    if st_uploader:
                        load_portfolio(_portfolio= st.session_state.portfolio, uploader=st_uploader)
                    if st_load_ticker and st_ticker_text!="":
                        try:
                            today = datetime.datetime.now()
                            _date = datetime.datetime(today.year-1,today.month,today.day)
                            data ={"NAME":[st_ticker_text],"VOLUME":[1],"PRICE":[0],"DATE":[_date],"SYMBOL":[st_ticker_text], "selected":True}
                            df = pd.DataFrame(data)
                            load_portfolio(_portfolio=st.session_state.portfolio, df=df)
                        except Exception as e:
                            print (f" cannot load ticker '{st_ticker_text}'. Error:{e}")
                with st.spinner("Loading Charts..."):
                    fig = get_fig(st.session_state.portfolio,date_range)
                    st.session_state.fig = fig  

        with portfolio_container:
            with m1:
                total = int(st.session_state.portfolio.history['close'].iloc[-1]) 
                delta = int(st.session_state.portfolio.history['close'].iloc[-1] -  st.session_state.portfolio.history['price'].iloc[-1])
                perf_metric = st.metric("Total",value=f"{total} €", delta=f"{delta:,} €", border=True)
            with m2:
                quarter_price = int(st.session_state.portfolio.history['close'].iloc[-90]) 
                delta_1 = int(st.session_state.portfolio.history['close'].iloc[-1] -  st.session_state.portfolio.history['price'].iloc[-1])
                delta_2 = int(st.session_state.portfolio.history['close'].iloc[-90] - st.session_state.portfolio.history['price'].iloc[-90])
                perf = int(100 * (delta_1 - delta_2)/quarter_price)
                perf_metric = st.metric("Last 90 days",value=f"{(delta_1-delta_2):,} €", delta=f"{perf} %", border=True)
            with m3:
                week_price = int(st.session_state.portfolio.history['close'].iloc[-8]) 
                delta_1 = int(st.session_state.portfolio.history['close'].iloc[-1] -  st.session_state.portfolio.history['price'].iloc[-1])
                delta_2 = int(st.session_state.portfolio.history['close'].iloc[-8] - st.session_state.portfolio.history['price'].iloc[-8])
                perf = int(100 * (delta_1 - delta_2)/week_price)
                perf_metric = st.metric("Last week",value=f"{(delta_1-delta_2):,} €", delta=f"{perf} %", border=True)
            with m4: # "forecast"
                pass
            with m5: # "sentiment"
                pass
            with m6: # "recommendation"
                pass
            
            with trans_col:            
                st.session_state.portfolio.transactions["selected"]=True
                st_data_editor = st.data_editor(data=st.session_state.portfolio.transactions, use_container_width=True, num_rows="dynamic", key="st_data_editor", on_change=None)
            
            with sym_col:
                st.dataframe(pd.DataFrame({"Symbols":st.session_state.portfolio.symbol_list}), use_container_width=True, hide_index=True)

            with st_cont_history:
                data_shown = st.session_state.portfolio.history[["price", "close", "high", "low"]]
                st_data_frame = st.dataframe(data=data_shown, use_container_width=True)
                
            #with st_cont_chart:   
            with col_chart:
                st_tech_analysis_chart = st.plotly_chart(st.session_state.fig,use_container_width=True,height=600, theme="streamlit", key="_history_chart",)

    if analyze_btn:
        for state in ["ai_response","forecast","forecast_delta","sentiment","sentiment_result","sentiment_value","recommendation"]:
            if state not in st.session_state: st.session_state[state] = None
        
        with st_commands:            
            with st.spinner(f"AI Analysis with {ai_type}..."):
                ai_response=get_ai_response(st.session_state.fig, type=ai_type)    
                st.session_state.ai_response = ai_response
                st.session_state.recommendation = st.session_state.ai_response.split()[2]
            
            with st.spinner(f"Sentiment Analysis..."):
                if "sentiment" not in st.session_state or  st.session_state.sentiment is None:
                    sentiment = Sentiment([st_ticker_text])
                    st.session_state.sentiment = sentiment
                    # if st_ticker_text.strip() !="":
                    #     sentiment.eval()
                    #     st.session_state.sentiment_value = sentiment.sentiment["POSITIVE"] - sentiment.sentiment["NEGATIVE"]
                    #     total = sentiment.news_df.shape[0]
                    #     st.session_state.sentiment = sentiment
                    #     if abs(st.session_state.sentiment_value)<0.1* total: st.session_state.sentiment_result = "Neutral"
                    #     elif st.session_state.sentiment_value > 0: st.session_state.sentiment_result = "Positive"
                    #     elif st.session_state.sentiment_value < 0: st.session_state.sentiment_result = "Negative"
                    
            with st.spinner(f"Forecast..."):
                time.sleep(2.0)
                plus = 100
                st.session_state.forecast = f"{int(st.session_state.portfolio.history['close'].iloc[-1])+plus} €"
                st.session_state.forecast_delta = f"{plus} €"
        
        with st_cont_ai:
            st.markdown(st.session_state.ai_response)
        
        with st_cont_forecast:
            st.write(st.session_state.forecast)            
        
        with st_cont_sentiment:
            my_sentiment = Sentiment({row["SYMBOL"]:row["amount"] for _, row in st.session_state.portfolio.basedata.iterrows()})
            fig_sent = my_sentiment.get_treemap()
            st.session_state.sentiment.news_df = my_sentiment.news_df
            st.plotly_chart(fig_sent)
            st.dataframe(st.session_state.sentiment.news_df, hide_index=True, column_config={"Date":st.column_config.DateColumn("Date", format="DD.MM.YYYY"), "Title": "Title", "sentiment":"Sentiment", "Link": st.column_config.LinkColumn("Link"), "Source": "Source", "ticker": "Ticker"}, use_container_width=True)
    
        with m4:
            forc_metric = st.metric("Forecast (TBD)",value=st.session_state.forecast, delta=st.session_state.forecast_delta, border=True)
        
        with m5:
            sent_metric = st.metric("Sentiment",value=st.session_state.sentiment_result, delta=st.session_state.sentiment_value, border=True)
        
        with m6:
            ai_metric   = st.metric("AI Recommendation",value=st.session_state.recommendation, delta=f"by {ai_type}", border=True, delta_color="off")

    st.markdown(nav_header, unsafe_allow_html=True)
