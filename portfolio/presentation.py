import plotly.graph_objects as go
from plotly.subplots import make_subplots
from portfolio import Portfolio, logging
import pandas as pd
import functools
import os
import tempfile
import base64


class Figure():

    currency_symbols = {"USD":"$", "AUD":"$", "EUR":"€", "GBP" : "£"}

    indicators ={
        "price":{"secondary_y": False, "fill":"tonexty", "name":"PRICE", "line":{"color":"#ffe490"}, }, 
        "close":{"secondary_y": False, "fill":"tonexty", "name":"CLOSE", "line":{"color":"#a0ff90"}, },}
    
    symbol_tech_indicators ={
        "mfi":{"secondary_y": False, "name":"MFI" }, 
    }

    portfolio_tech_indicators ={
        "win":{"secondary_y": False, "name":"WIN"}, 
        "ema":{"secondary_y": False, "name":"EMA"}, 
        "sma":{"secondary_y": False, "name":"SMA"}, 
        "bb_lower":{"secondary_y": False, "name":"BB_LOW"}, 
        "bb_upper":{"secondary_y": False, "name":"BB_up"}, 
        "perf":{"secondary_y": True, "name":"% WIN"}, 
        "perf_ema":{"secondary_y": True, "name":"% EMA"}, 
        "perf_sma":{"secondary_y": True, "name":"% EMA"}, 
        "perf_bb_lower":{"secondary_y": True, "name":"% BB_LOW"}, 
        "perf_bb_upper":{"secondary_y": True, "name":"% BB_UP"},
        "rsi":{"secondary_y": True, "name":"RSI"}, 
        "mfi":{"secondary_y": True, "name":"MFI"}, 
        "macd":{"secondary_y": False, "name":"MACD"}, 
        "signal_line":{"secondary_y": False, "name":"SIGNAL"}, 
        "histogram":{"secondary_y": False, "name":"HISTO"}
        }

    def __init__(self,portfolio: Portfolio):
        self.portfolio = portfolio

    def fig(self, date_range:int = None, level="portfolio", primary_y_stretch:float=1.2, secondary_y_stretch:float=1.2, exclude:str = None, height:int = 500, sep="||"):

        self.y_axis={"primary_y":{"max":0, "min":0},"secondary_y":{"max":0, "min":0}}
        
        if level in ["portfolio","symbol"]: self.portfolio.aggregate_to(level=level, inplace=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])  
        fig.update_layout(legend=dict(x=0, y=1.15, orientation='h', font=dict(family="Arial", size=10, color="#404040"), bordercolor="Black", bgcolor="#ffffff", borderwidth=0),)

        indicators = Figure.indicators
        data_set = self.portfolio.history
        if date_range is not None:
            data_set = self.portfolio.history.tail(date_range)
        if exclude is not None:
            exclude = exclude.split(sep)
            indicators = {ind:indicators[ind] for ind in set(indicators.keys()) - set(exclude)} 
        for key, config in indicators.items():
            col = key
            #if col in self.portfolio.history.columns:
            if col in data_set.columns:
                fig.add_trace(go.Scatter(x=data_set.index, y=data_set[col], mode='lines', name=config["name"], line=config["line"], fill="tonexty",), secondary_y=config["secondary_y"],)
                which_y = "secondary_y" if config["secondary_y"]==True else "primary_y"
                self.y_axis[which_y]["min"] = min(self.y_axis[which_y]["min"], data_set[col].min())
                self.y_axis[which_y]["max"] = max(self.y_axis[which_y]["max"], data_set[col].max())


        portfolio_tech_indicators = Figure.portfolio_tech_indicators
        if exclude is not None:
            portfolio_tech_indicators = {ind:portfolio_tech_indicators[ind] for ind in set(portfolio_tech_indicators.keys()) - set(exclude)} 
        
        for key, config in portfolio_tech_indicators.items():
            col = f"{self.portfolio._prefix_portfolio_indicator}{key}"
            if col in self.portfolio.history.columns:
                fig.add_trace(go.Scatter(x=data_set.index, y=data_set[col], mode='lines', name=config["name"],), secondary_y=config["secondary_y"],)
                which_y = "secondary_y" if config["secondary_y"]==True else "primary_y"
                self.y_axis[which_y]["min"] = min(self.y_axis[which_y]["min"], data_set[col].min())
                self.y_axis[which_y]["max"] = max(self.y_axis[which_y]["max"], data_set[col].max())


        fig.update_xaxes(title_text="<b>History</b>")

        tickprefix = Figure.currency_symbols.get(self.portfolio.target_currency,"")
        _min = self.y_axis["primary_y"]["min"]* primary_y_stretch
        _max = self.y_axis["primary_y"]["max"]* primary_y_stretch
        fig.update_yaxes(title_text=f"<b>{self.portfolio.target_currency}</b>",  secondary_y=False,  tickprefix=tickprefix, range=[_min, _max])

        _min = self.y_axis["secondary_y"]["min"]* secondary_y_stretch
        _max = self.y_axis["secondary_y"]["max"]* secondary_y_stretch
        fig.update_yaxes(title_text="<b>Yield in %</b>", secondary_y=True, tickformat=".0%", range=[_min, _max])

        fig.update_layout(height=height)

        return fig
    
    @staticmethod
    def fig_to_base64(fig):
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmpfile:
                fig.write_image(tmpfile.name)
                with open(tmpfile.name, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
            return image_data
        except Exception as e:
            logging.error(f"Error saving chart as base64 string: {e}")
            return None