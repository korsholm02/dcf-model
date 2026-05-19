# DCF Analyzer

Professionel DCF-værdiansættelse til investorer - minimalt arbejde, maksimal indsigt.

## Kom hurtigt i gang

### Installation

```bash
cd dcf-model
pip install -r requirements.txt
```

### Start Dashboard

```bash
streamlit run main.py
```

Dashboardet åbner i din browser på `http://localhost:8501`

## Funktioner

### 📊 DCF Værdiansættelse
- Automatisk datahentning fra Yahoo Finance (ingen API-nøgle nødvendig)
- 5-års FCF prognose baseret på historiske nøgletal
- WACC beregning med CAPM
- Terminal værdi (perpetuity growth)
- Implied share price vs. nuværende kurs

### 📈 Historisk Analyse
- 5 års historiske regnskaber
- Revenue, EBIT, FCF udvikling
- Margin trends

### ⚙️ Hybrid Budgettering
- **Default**: Systemet viser historiske gennemsnit som udgangspunkt
- **Juster**: Du kan override alle antagelser
- **Gem**: Dine antagelser kan tilpasses din vurdering

### 📉 Sensitivitetsanalyse
- WACC vs. Terminal Growth heatmap
- Base/Bull/Bear scenarier
- Se hvordan værdien ændrer sig med forskellige antagelser

## Support

### Børsnoterede virksomheder
Indtast blot tickeren:
- Danske: `NOVO-B.CO`, `MAERSK-B.CO`, `DSV.CO`
- Amerikanske: `AAPL`, `MSFT`, `ITRI`
- Internationale: `NESN.SW`, `TSLA`

### Ikke-børsnoterede
Kommer snart: Manuel input af regnskabsdata

## Eksempel: Itron Inc (ITRI)

```
Ticker: ITRI
Current Price: $79.05
Implied Price: $108.11
Upside: 36.8%
```

## Projektstruktur

```
dcf-model/
├── data/
│   ├── fetcher.py      # Yahoo Finance integration
│   └── parser.py       # Normalisering af regnskabsdata
├── models/
│   ├── cashflow.py     # FCF projektion
│   ├── wacc.py         # WACC beregning
│   └── valuation.py    # DCF → Equity Value
├── budget/
│   └── defaults.py     # Historiske gennemsnit
├── ui/
│   └── dashboard.py    # Streamlit dashboard
├── main.py             # Entry point
└── requirements.txt
```

## Næste skrid

- [ ] Manuel input for ikke-børsnoterede virksomheder
- [ ] Gem/eksportér analyser
- [ ] Peer comparison (multiples)
- [ ] Kvartalsvis data
