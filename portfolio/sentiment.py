
import pandas as pd
from finvizfinance.quote import finvizfinance
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, BertTokenizer, BertForSequenceClassification
from transformers import pipeline
import logging
import yfinance as yf
import json
import plotly.express as px
import nltk
nltk.downloader.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import crawl4ai


class Sentiment():

    sentiment_models ={
        "nltk":{}, 
        "distilBERT":{"tokenizer":"distilbert/distilbert-base-uncased-finetuned-sst-2-english", "model":"distilbert/distilbert-base-uncased-finetuned-sst-2-english"}, 
        "finBERT":{"tokenizer":"ProsusAI/finbert", "model":"ProsusAI/finbert"}, 
        }


    def __init__(self, ticker):
        self.ticker = {t:1 for t in ticker} if isinstance(ticker, list) else ticker
        self.news_df = pd.DataFrame()
        self.ticker_info = pd.DataFrame()
        self._init = False


    def init_data(self):
        if self._init: return
        data={'Industry': [], 'Price': [], 'Shares': []}
        tickers =[]
        for ticker,shares in self.ticker.items():
            tickerdata = yf.Ticker(ticker)
            data["Price"].append(tickerdata.info.get("regularMarketPreviousClose",0))
            data["Industry"].append(tickerdata.info.get("industry",""))        
            data["Shares"].append(shares)
            tickers.append(ticker)
        self.ticker_info = pd.DataFrame(data=data, index = tickers)
        self.ticker_info['Stockvalue'] = self.ticker_info['Price']*self.ticker_info['Shares']
        self.load_news()
        self._init = True


    def load_news(self, source="finviz"):
        """
        Get news data in the form ["Date", "Title", "Link", "Source"] and load it into self.news_df

        Parameter:
        ----------

        Return:
        -------

        """
        # self.news_df-columns =["Date", "Title", "Link", "Source"]
        self.news_df=pd.DataFrame({"Date":[], "Title":[], "Link":[], "Source":[], "Ticker":[]})
        if self.ticker == {}: print("load_news(): no ticker found!"); return
        if source =="finviz":
            try:
                for ticker in self.ticker.keys():
                    stock = finvizfinance(ticker)
                    news = stock.ticker_news()
                    news["Ticker"]=ticker
                    self.news_df = pd.concat([self.news_df, news], axis=0, ignore_index=True,)
                self.news_df['Date'] = pd.to_datetime(self.news_df['Date'])
            except Exception as e:
                print(f"Error loading finviz news from {source} for {self.ticker=} Error: {e}")
        else:
            try:
                pass
            except Exception as e:
                print(f"Error loading news from {source} for {self.ticker=} Error: {e}")


    def score_data(self, model="nltk",threshold=0.8) -> None:
        if model not in Sentiment.sentiment_models.keys(): return    
        try:
            if model == "nltk":
                scores_df = self._score_data_by_nlp(model=model)
            else:                
                scores_df = self._score_data_by_ai(model=model)
            scores_df = self.news_df.join(scores_df, rsuffix=f'_{model}')
            mean_scores = scores_df.groupby(['Ticker']).mean(numeric_only=True)
            self.ticker_info = self.ticker_info.drop([f"neu_{model}",f"pos_{model}",f"neg_{model}","Ticker"], errors="ignore", axis=1)
            self.ticker_info = pd.concat([self.ticker_info, mean_scores], axis =1)
        except Exception as e:
            logging.error(f"Error in score_data() with {model = }: {e}")


    def _score_data_by_nlp(self, model="nltk", threshold=0.8) -> pd.DataFrame:
        """
        Get sentiment score for each text using NLP methods WITHOUT AI
        
        Parameter:
        ----------
        model: str, Default "nltk"
        name of the model

        Return:
        -------
        pandas dataframe like [...{"compound_nltk":0.9227, "neg_nltk": 0.0, "neu_nltk": 0.246, "pos_nltk": 0.754,}...]
        """
        vader = SentimentIntensityAnalyzer()
        scores = self.news_df["Title"].apply(vader.polarity_scores).tolist()
        score_data = pd.DataFrame(scores)
        score_data.rename(columns={"neg":f"neg_{model}","pos":f"pos_{model}","neu":f"neu_{model}","compound":f"compound_{model}",}, inplace=True,)
        return score_data
  
    def _score_data_by_ai(self, model="finBERT") -> pd.DataFrame:
        """        
        Get sentiment score for each text using NLP methods WITH AI

        Parameter:
        ----------
        model: str, Default "finBERT"
        name of the model

        Return:
        -------
        pandas dataframe like [...{"Score":0.9227, "neg": 0.0, "neu": 0.246, "pos": 0.754,}...]
        """
        if model not in Sentiment.sentiment_models.keys(): return
        try:
            if model == "finBERT":
                tokenizer = BertTokenizer.from_pretrained(Sentiment.sentiment_models["finBERT"]["tokenizer"])
                _model = BertForSequenceClassification.from_pretrained(Sentiment.sentiment_models["finBERT"]["model"], num_labels=3)
            elif model == "distilBERT":
                tokenizer = DistilBertTokenizer.from_pretrained(Sentiment.sentiment_models[model]["tokenizer"])
                _model = DistilBertForSequenceClassification.from_pretrained(Sentiment.sentiment_models[model]["model"])
            nlp = pipeline("sentiment-analysis", tokenizer=tokenizer, model=_model)
            results = nlp(self.news_df["Title"].tolist())

            sentiment_by_AI_results =[]
            for result in results:
                sent={f"neg_{model}":0,f"neu_{model}":0,f"pos_{model}":0,f"compound_{model}":0}
                sent[f"compound_{model}"] = - result["score"] if result["label"].upper()=="NEGATIVE" else (result["score"] if result["label"].upper()=="POSITIVE" else 0)
                sent[result["label"][:3].lower()+f"_{model}"]=1
                sentiment_by_AI_results.append(sent)

            return pd.DataFrame(sentiment_by_AI_results)
        except Exception as e:
            logging.error(f"Error in _score_data_by_ai: {e}")
            return pd.DataFrame([{f"neg_{model}":0,f"neu_{model}":0,f"pos_{model}":0,f"compound_{model}":0}]*len(results))
    
    def get_treemap(self) -> px.treemap:
        fig = px.treemap(
            self.ticker_info, 
            path=[px.Constant("Industries"), "Industry", "ticker"], 
            values='Stockvalue', 
            color='Score', 
            hover_data=['Price', 'neg', 'neu', 'neg', 'Score'], 
            color_continuous_scale=['#FF0000', "#000000", '#00FF00'], 
            color_continuous_midpoint=0)
        fig.data[0].customdata = self.ticker_info[['Price', 'neg', 'neu', 'neg', 'Score']].round(3)
        fig.data[0].texttemplate = "%{label}<br>%{customdata[4]}"
        fig.update_traces(textposition="middle center")
        fig.update_layout(margin = dict(t=30, l=10, r=10, b=10), font_size=20)
        return fig


if __name__=="__main__":

    print("------------------------------------------------------------------")
    tickers ={"AAPL":10, "MSFT":20, "GOOG":100, "TSLA":12}
    sentiment = Sentiment(tickers)
    sentiment.init_data()
    
    for model in sentiment.sentiment_models:
        sentiment.score_data(model=model)
    print(sentiment.ticker_info)