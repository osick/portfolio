import streamlit as st
from io import StringIO
import pandas as pd
from portfolio import Portfolio
from portfolio.presentation import Figure
from portfolio.ai import AI
import os

def load_css(filepath):
    with open(os.path.join("data","css",filepath),"r") as fh: 
        st.markdown(f"<style>{fh.read()}</style>" , unsafe_allow_html=True)

def get_ai_response(fig, type="Llama"):
    image_path=Figure.fig_to_base64(fig)
    ai = AI()
    #response = ai._ping_Llama()
    response = ai.ask(type=type, image_data=image_path) 
    return response

def get_fig(my_portfolio, date_range, title:str=None):
    calc_portfolio(my_portfolio,selected_only=True)
    my_figure = Figure(my_portfolio)
    exclude = list(set(my_portfolio.portfolio_tech_indicators) -set(st.session_state._indicators))
    exclude = "||".join(exclude)
    exclude = None
    fig = my_figure.fig(date_range, exclude=exclude, secondary_y_stretch=1.0, primary_y_stretch=1.0, sep ="||")
    if title is None: title = f'{", ".join(list(my_portfolio.basedata["SYMBOL"]))}'
    fig.update_layout(title={ 'text': title, 'y':0.95,  'x':0.5, 'xanchor':'center', 'yanchor': 'top'})
    return fig

def section_title(text:str):
    st.markdown(f"<h3 align='center'>{text}</h3>",unsafe_allow_html=True)

def st_reset_session():
    for state  in ["ai_messages","fig"]:
        if state in st.session_state:
            del st.session_state[state]

def reload_transactions(selected_only=True):
    my_portfolio.load_transactions(st_data_editor)
    calc_portfolio(my_portfolio, selected_only=selected_only)

def calc_portfolio(_portfolio, selected_only=True):
    _portfolio.load_history(selected_only=selected_only)
    _portfolio.aggregate_to(level="portfolio", inplace=True, selected_only=selected_only)
    _portfolio.get_portfolio_tech_indicators(inplace=True, symbols= None, interval=interval)

def navbar(entries:dict):
    with open(os.path.join("data","markdown","navbar.header.markdown")) as fh:
        nav_header=fh.read()
        nav_items=[]
    for name, link in entries.items():
        nav_items.append(f'<li class="nav-item"><a class="nav-link" href="{link}"><span style="color:white">{name}</span></a></li>')
    
    nav_header = nav_header.replace("{NAV_ITEMS}", "\n".join(nav_items))

    with open(os.path.join("data","markdown","navbar.bottom.markdown")) as fh:
        nav_bottom=fh.read()

    return nav_header, nav_bottom  

if __name__ == "__main__":

    my_portfolio = Portfolio()

    # initial config
    st.set_page_config(initial_sidebar_state="expanded",layout="wide")
    load_css("dashboard.css")

    # entries = {"DATA":"#DATA", "CHARTS":"#technical-analysis", "AI":"#AI", "SUMMARY":"#SUMMARY", "HELP":"#HELP", "DISCLAIMER":"#DISCLAIMER"}
    # nav_bottom, nav_header= navbar(entries)
    # st.markdown(nav_bottom, unsafe_allow_html=True)


    with st.sidebar:
        # interval of days
        interval = st.slider(label=":blue[**Indicators interval**]", min_value=1, max_value=365, value=60, key="interval")

        # data rage from today on into the past
        date_range = st.slider(label=":blue[**Date Range (from today into the past)**]", min_value=1, max_value=365*3, value=180, key="date_range")

        # selection of indicators
        st_indicators = st.multiselect("Indicator", my_portfolio.portfolio_tech_indicators , placeholder="Choose technical indicator", default=None, key="_indicators", format_func=lambda x: str(x))     
        st.divider()         
        st.markdown("<h3 align='center'>Transactions</h3>",unsafe_allow_html=True)
        st_uploader = st.file_uploader("**Upload**", type=["csv"],label_visibility="collapsed", key="_uploader")
        head1, head2 = st.columns([4,4])
        with head1:
            st_downloader = st.button("**Save Data**",use_container_width=True, key="_downloader")
        with head2:
            st_btn_data_editor = st.button("# **Load Data**", key="st_btn_data_editor", use_container_width=True, type="secondary", on_click=reload_transactions)
        st.divider()  

    # ********START Tabs Init******************************************************
    #
    st_tab_data, st_tab_analysis, st_tab_ai, st_tab_summary, st_tab_help, st_tab_disclaimer = st.tabs(["DATA", "CHARTS", "AI", "SUMMARY", "HELP", "Disclaimer"])    

    with st_tab_disclaimer:
        disclaimer=open("Disclaimer.md","r").read()
        st.markdown(disclaimer, unsafe_allow_html=True)

    with st_tab_help:
        help=open("Readme.md","r").read().split("<!--CUT-->")[-1]
        st.markdown(help, unsafe_allow_html=True)

    with st_tab_data:            
        section_title("Transactions")        
        data_expander= st.expander("Transaction Data", expanded=True)
        with data_expander:
            trans_col, sym_col = st.columns([7,1])
            with trans_col:
                pass
            with sym_col:
                pass

        section_title("History")       
        history_expander=st.expander("Historical Data", expanded=True)
        with history_expander:
            pass

    with st_tab_analysis:            
        section_title("Technical Analysis")
    
    with st_tab_ai:            
        section_title("AI")
        if "ai_messages" not in st.session_state:
            st.session_state.ai_messages = []

    with st_tab_summary:
        c1, c2 = st.columns([7,1])
        with c1:
            section_title("Summary")
        with c2:
            st_downloader = st.download_button("Download", data=my_portfolio.transactions.to_csv().encode("utf-8"), file_name="data.csv", mime="text/csv", key="_download",)
     
    #
    # ********END Tabs Init********************************************************

    if st_uploader:
        st.cache_data.clear()

        with st.sidebar:
            with st.spinner("Loading Portfolio..."):
                st.cache_data.clear()
                st_reset_session()
                my_portfolio._init_data()
                file = StringIO(st_uploader.getvalue().decode("utf-8"))
                my_portfolio.from_csv(st_uploader)
                calc_portfolio(my_portfolio)
        
            with st.spinner("Loading Charts..."):
                fig = get_fig(my_portfolio,date_range)
                st.session_state.fig = fig
        
        with st_tab_data:
            with trans_col:
                my_portfolio.transactions["selected"]=True
                st.session_state.transactions = my_portfolio.transactions
                st_data_editor = st.data_editor(data=st.session_state.transactions, use_container_width=True, num_rows="dynamic", key="st_data_editor", on_change=None)

            with sym_col:
                st.dataframe(pd.DataFrame({"Symbols":my_portfolio.symbol_list}), use_container_width=True, hide_index=True)

            with history_expander:
                data_shown = my_portfolio.history[["price", "close", "high", "low"]]
                st_data_frame = st.dataframe(data=data_shown, use_container_width=True)

        with st_tab_analysis:            
            st_tech_analysis_chart = st.plotly_chart(st.session_state.fig,use_container_width=True,height=600, theme="streamlit", key="_history_chart",)

            section_title("Forecasting")
            st.markdown("**TBD**")

        with st_tab_ai:
            a1, a2,a3=st.columns([8,2,2])
            if "ai_messages" not in st.session_state or len(st.session_state.ai_messages)==0:
                with a2:
                    ai_type = st.selectbox("Choose model", ["chatgpt","llama", "llava"], index=1, label_visibility="collapsed", key="ai_type")
                with a3:
                    ai_button= st.button("**Analyze Chart**", use_container_width=True,)
                    if ai_button:
                        with st.spinner(f"AI Analysis with {ai_type}"):
                            ai_response=get_ai_response(st.session_state.fig, type=ai_type)    
                            st.session_state.ai_messages = [ai_response]
                        with a1:
                            st.markdown(ai_response)
            elif len(st.session_state.ai_messages)>0:            
                    a1, a2=st.columns([8,3])
                    with a2:
                        prompt = st.chat_input(placeholder="Ask the AI", key="ai_prompt")
                        if prompt:
                            st.session_state.ai_messages.append({"user":prompt, "ai":""})
                            with st.spinner("responding ..."):
                                response="Yes!"
                                st.session_state.ai_messages[-1]["ai"]=response
                            for conv in st.session_state.ai_messages[1:]:
                                with st.chat_message("user"):
                                    st.write(conv["user"])
                                with st.chat_message("ai"):
                                    st.write(conv["ai"])
                    with a1:
                        st.markdown(st.session_state.ai_messages[0])

    # st.markdown(nav_header, unsafe_allow_html=True)
