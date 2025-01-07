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

    @functools.cache
    def fig(self, level="portfolio", primary_y_stretch:float=1.0, secondary_y_stretch:float=1.0, exclude:str = None, height:int = 600, sep="||"):
        exclude = exclude.split(sep)

        self.y_axis={"primary_y":{"max":0, "min":0},"secondary_y":{"max":0, "min":0}}
        
        if level in ["portfolio","symbol"]: self.portfolio.aggregate_to(level=level, inplace=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])  
        fig.update_layout(legend=dict(x=0, y=1.0, orientation='h', font=dict(family="Arial", size=10, color="#404040"), bordercolor="Black", bgcolor="#ffffff", borderwidth=0),)

        indicators = Figure.indicators
        if exclude is not None:
            indicators = {ind:indicators[ind] for ind in set(indicators.keys()) - set(exclude)} 
        for key, config in indicators.items():
            col = key
            if col in self.portfolio.history.columns:
                fig.add_trace(go.Scatter(x=self.portfolio.history.index, y=self.portfolio.history[col], mode='lines', name=config["name"], line=config["line"], fill="tonexty",), secondary_y=config["secondary_y"],)
                which_y = "secondary_y" if config["secondary_y"]==True else "primary_y"
                self.y_axis[which_y]["min"] = min(self.y_axis[which_y]["min"], self.portfolio.history[col].min())
                self.y_axis[which_y]["max"] = max(self.y_axis[which_y]["max"], self.portfolio.history[col].max())


        portfolio_tech_indicators = Figure.portfolio_tech_indicators
        if exclude is not None:
            portfolio_tech_indicators = {ind:portfolio_tech_indicators[ind] for ind in set(portfolio_tech_indicators.keys()) - set(exclude)} 
        for key, config in portfolio_tech_indicators.items():
            col = f"{self.portfolio._prefix_portfolio_indicator}{key}"
            if col in self.portfolio.history.columns:
                fig.add_trace(go.Scatter(x=self.portfolio.history.index, y=self.portfolio.history[col], mode='lines', name=config["name"],), secondary_y=config["secondary_y"],)
                which_y = "secondary_y" if config["secondary_y"]==True else "primary_y"
                self.y_axis[which_y]["min"] = min(self.y_axis[which_y]["min"], self.portfolio.history[col].min())
                self.y_axis[which_y]["max"] = max(self.y_axis[which_y]["max"], self.portfolio.history[col].max())


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
    def chart_to_image(fig):
        try:
            if not os.path.exists("data"):
                os.mkdir("data")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                tmpfile_path = os.path.join("data", tmpfile.name)
                fig.write_image(tmpfile_path)
            with open(tmpfile_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            os.remove(tmpfile_path)
            return image_data
        except Exception as e:
            logging.error(f"Error saving chart to image: {e}")
            return None