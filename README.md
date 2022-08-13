# WCA Competition Badge Generator

This tool generates competitor badges for WCA competitions by parsing the WCIF file of the competition.

The format of the badges is A6. The front and back are printed netx to each other on half of a A4 page, so you just need to fold it.
In case you need a different format, you can edit the CSS formatting of the [templates](https://github.com/Laura-O/wca-badges/tree/main/templates).

## Running locally

```
pip install -r requirements.txt
streamlit run app.py
```

In order to generate PDFs, you also need [wkhtmltopdf](https://wkhtmltopdf.org/) which is an open source command line tool to render HTML into PDF.
Instructions on how to install it on your OS can be found on [their website](https://wkhtmltopdf.org/downloads.html).
