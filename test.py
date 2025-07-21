import requests
import time
# Endpoint URL
apikey = "0UGhhKVqW1ofy0osb1dOcvabBS1vQZQHi4hKATs73an5pZY2xvv50xtnk0U"
url = f'http://127.0.0.1:8000/Stock/peerstocks/?apikey={apikey}'


tickers = [ "DATAMATICS", "HPL", "DALMIASUG",
  "ALEMBICLTD", "HATHWAY", "CARERATING", "SHK", "SBCL", "MTNL",
  "SEAMECLTD", "INDOSTAR", "SERVOTECH"
]

# Loop through and post each ticker
for ticker in tickers:
    payload = {
        "tickers": [ticker]
    }
    response = requests.post(url, json=payload)

    # Logging the result
    print(f"Sent ticker: {ticker}, Status: {response.status_code}")
    time.sleep(30)