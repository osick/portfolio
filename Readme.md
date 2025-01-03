# Stock Portfolio app

## Intro

Simple proof of concept of a Portfolio app to monitor and view the history of a portfilio.

## Usage
1. Install required Python Libs (or better first activate an environment)
```bash
foo@bar:~$ pip install .
```
2. Start the app

```bash
foo@bar:~$ streamlit run app.py
```

3. Open the streamlit address  
```
http://localhost:8501
```

<!--CUT-->

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
