# Proof of Concept for Portfolio analysis using technical indicators and AI Chat models

## Introduction
This is a simple simple proof of concept of a Portfolio app to view and analyse a portfilio of stocks. 
- In the definition used here a  portfolio is a sequence of buy and sell trades of stock shares, always executed at specific dates.
- A portfolio has a history, i.e. a representation of the mix of shares and the total value of it.  
The history and the score sheet of the companies underlying the shares are the basis of a technical analysis, i.e. a numerical exploration of these KPI and data.
Examples of technical indicators are the gliding mean of the total value of the portfolio or the standard deviation. But of course there are many other and some of them are impelmented in this Web App. 

The financial data are based on **Yahoo finance** by using the **yfinance** library for Python and so we are limited to the shares and date renge provided by Yahoo (in fact, this is a lot ...)


## Setup
### Installation
Install required Python Libs (or better first activate an environment)
```bash
foo@bar:~$ pip install .
```
### AI capabilities
If you want to use AI capabilites then you have two chocies
1. Set up an Ollama Server on yourlocal machine 
2. Sponsor the OpenAI API and write the OpenAI key into an .env file in the base directory ( a sample file is given: [.env sample file ](.env.sample))

### Start the server
```bash
foo@bar:~$ streamlit run dashbaord.py
```

### Start the client
```
http://localhost:8501
```

<!--CUT-->
# <span style="color: red">Important </span>
### Read the [<span style="color: red">Disclaimer</span>](Disclaimer.md) before using this app. Act responsible!

## How to use the App

* Choose a CSV file containg all the transactions and upload it via the *Browse files* button   
(Don't be afraid, no data will be stored)
* The description of the structure of the CSV is given in the **Help** section
* The **Data Tab** shows the historical data as table
* The **Analysis Tab** shows history and forecast data
* The **AI Tab** shows an AI based interpretation of the data 
* Make your analysis, play with the technical indicators and discuss the results with the AI
* Finally yo may *Download* or *Print* the the results if you want (see Summary)

## Input für Portfolio

### Structure of the CSV file  
    | NAME      | AMOUNT  | PRICE  | DATE       | SYMBOL | 
    |-----------|---------|--------|------------|--------|  
    | ALLIANZ   |  11     |  2000  | 31.10.2021 | ALIZF  |
    | MICROSOFT |  15     |  1000  | 31.10.2022 | MSFT   |
    | MICROSOFT | -10     | -1000  | 31.08.2023 | MSFT   |
    | ...       | ...     | ...    | ...        | ...    |
    | ...       | ...     | ...    | ...        | ...    |
    
    Each line is a buy or sell transaction

### Columns
    |-------|-------------------------------------------------------------------------------------------------------------------------------|
    |NAME   | Arbitrary Identifier                                                                                                          |
    |AMOUNT | Number of shares. If it's a *Sell*, then price is a *negative* number. If it's a *Buy* the it is a *positive* number          | 
    |PRICE  | The total price (in EUR). If it's a *Sell*, then price is a *negative* number. If it's a *Buy* the it is a *positive* number  |
    |DATE   | Day of transaction (no Time or timezone Info nescessary)                                                                      |
    |SYMBOL | The symbol of the share                                                                                                       |
    |-------|-------------------------------------------------------------------------------------------------------------------------------|
