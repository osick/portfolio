import plotly.graph_objects as go
from plotly.subplots import make_subplots
from portfolio import Portfolio, logging
import pandas as pd


class Figure():

    indicators ={
        "price":{"secondary": False, "fill":"tonexty", "name":"PRICE", "line":{"color":"#ffe490"}, }, 
        "close":{"secondary": False, "fill":"tonexty", "name":"CLOSE", "line":{"color":"#a0ff90"}, }, 
        }

    symbol_tech_indicators ={}

    portfolio_tech_indicators ={
        "win":{"secondary": False, "name":"WIN"}, 
        "ema":{"secondary": False, "name":"EMA"}, 
        "sma":{"secondary": False, "name":"SMA"}, 
        "bb_lower":{"secondary": False, "name":"BB_LOW"}, 
        "bb_upper":{"secondary": False, "name":"BB_up"}, 
        "perf":{"secondary": True, "name":"% WIN"}, 
        "perf_ema":{"secondary": True, "name":"% EMA"}, 
        "perf_sma":{"secondary": True, "name":"% EMA"}, 
        "perf_bb_lower":{"secondary": True, "name":"% BB_LOW"}, 
        "perf_bb_upper":{"secondary": True, "name":"% BB_UP"},
        "rsi":{"secondary": True, "name":"RSI"}, 
        "mfi":{"secondary": True, "name":"MFI"}, 
        "macd":{"secondary": False, "name":"MACD"}, 
        "signal_line":{"secondary": False, "name":"SIGNAL"}, 
        "histogram":{"secondary": False, "name":"HISTO"}
        }

    def __init__(self,portfolio: Portfolio):
        self.portfolio = portfolio

    def fig(self, interval=20, level="portfolio"):

        if level in ["portfolio","symbol"]: 
            self.portfolio.aggregate_to(level=level, inplace=True)

        prefix_prt_ind = self.portfolio._prefix_portfolio_indicator 
        indicators = self.portfolio.portfolio_tech_indicators


        fig = make_subplots(specs=[[{"secondary_y": True}]])  
        fig.update_layout(legend=dict(
            x=0, 
            y=1.11, 
            orientation='h', 
            font=dict(family="Times New Roman", size=14, color="#404040"), 
            bordercolor="Black", 
            bgcolor="#ffffff", 
            borderwidth=0
        ),)


        # primary yaxis
        for key, config in Figure.indicators.items():
            col = key
            if col in self.portfolio.history.columns:
                fig.add_trace(go.Scatter(
                x=self.portfolio.history.index, 
                y=self.portfolio.history[f'price'], 
                mode='lines',  
                name=f"€ Price", 
                line=dict(color="#ffe490"), 
                fill="tonexty",  
                ), secondary_y=False,)




        # price
        fig.add_trace(go.Scatter(
            x=self.portfolio.history.index, 
            y=self.portfolio.history[f'price'], 
            mode='lines',  
            name=f"€ Price", 
            line=dict(color="#ffe490"), 
            fill="tonexty",  
            ), secondary_y=False,)
        
        # close
        fig.add_trace(go.Scatter(
            x=self.portfolio.history.index, 
            y=self.portfolio.history[f'close'], 
            line=dict(color="#a0ff90"),  
            fill="tonexty",  
            mode='lines', 
            name=f"€ Win" 
            ), secondary_y=False,)
        
        if "sma"  in indicators: 
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index,
                y=self.portfolio.history[f'{prefix_prt_ind}sma'],
                mode='lines',
                name=f"SMA ({interval}d)" ), secondary_y=False,)
        
        if "ema"  in indicators: 
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index, 
                y=self.portfolio.history[f'{prefix_prt_ind}ema'],  
                mode='lines',  
                name=f"EMA ({interval}d)" ), 
                secondary_y=False,)
        
        if "bb_lower" in indicators:
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index,
                y=self.portfolio.history[f"{prefix_prt_ind}bb_lower"], 
                mode='lines', 
                name=f"bb_lower ({interval}d)"), 
                secondary_y=False,)

        if "bb_upper" in indicators:
            fig.add_trace(go.Scatter( 
                x=self.portfolio.history.index,  
                y=self.portfolio.history[f"{prefix_prt_ind}bb_upper"], 
                mode='lines',  
                name=f"bb_upper ({interval}d)"), 
                secondary_y=False,)

        # secondary yaxis
        if "perf" in indicators: 
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index, 
                y=self.portfolio.history[f'{prefix_prt_ind}perf'],  
                mode='lines',  
                name=f"Win in %" ), secondary_y=True,)
        
        if "perf_sma"  in indicators: 
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index, 
                y=self.portfolio.history[f'{prefix_prt_ind}perf_sma'], 
                mode='lines', 
                name=f"% SMA ({interval}d)" ), secondary_y=True,)

        if "pert_ema"   in indicators: 
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index,
                y=self.portfolio.history[f'{prefix_prt_ind}perf_ema'], 
                mode='lines',  
                name=f"% EMA ({interval}d)" ), secondary_y=True,)

        if "perf_bb_lower"    in indicators:
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index,  
                y=self.portfolio.history[f"{prefix_prt_ind}perf_bb_lower"], 
                mode='lines', 
                name=f"% BB_lower ({interval}d)"), 
                secondary_y=True,)

        if "perf_bb_upper"    in indicators:
            fig.add_trace(go.Scatter(
                x=self.portfolio.history.index,  
                y=self.portfolio.history[f"{prefix_prt_ind}perf_bb_upper"], 
                mode='lines',  
                name=f"% BB_upper ({interval}d)"), 
                secondary_y=True,)
        
        fig.update_xaxes(title_text="<b>History</b>")

        fig.update_yaxes(
            title_text=f"<b>{self.portfolio.target_currency}</b>", 
            secondary_y=False, 
            tickprefix='€', 
            range=[0, self.portfolio.history[f"close"].max()*1.2])
        
        fig.update_yaxes(
            title_text="<b>Yield in %</b>", 
            secondary_y=True, tickformat=".0%", 
            range=[0, self.portfolio.history[f"{prefix_prt_ind}perf"].max()*1.2])
        
        return fig
