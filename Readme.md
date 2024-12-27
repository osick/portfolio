# Stock Portfolio app

## Intro

Simple proof of concept of a Portfolio app to monitor and view the history of a portfilio.

## Usage
```bash
foo@bar:~$ pip install .
```
Then

```bash
foo@bar:~$ streamlit run app.py
```

## Input für Portfolio

### Structure of the CSV file  
    | NAME      | ISIN         | AMOUNT | BUY  | DATE       | SYMBOL | 
    |-----------|--------------|--------|------|------------|--------|  
    | ALLIANZ   | DE0008404005 | 11     | 2000 | 31.10.2021 | ALIZF  |
    | MICROSOFT | US5949181045 | 15     | 1000 | 31.10.2022 | MSFT   |
    | ...       | ...          | ...    | ...  | ...        | ...    |
    | ...       | ...          | ...    | ...  | ...        | ...    |
    
    Each line is a buy or sell transaction

### Columns
**NAME**: arbitrary Identifier  
**ISIN**: ISIN Number (optional)  
**AMOUNT**: Number of shares  
**BUY**: The total price (in EUR)  
**DATE**: Buying Day (no Time or timezone Info nescessary)  
**SYMBOL**: The symbol of the share 