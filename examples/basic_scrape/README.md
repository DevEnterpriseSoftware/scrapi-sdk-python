# Basic Scrape Example

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install scrapi-sdk
$env:SCRAPI_API_KEY="your_api_key_here_or_blank"
python main.py
```

This sample performs a scrape against `https://deventerprise.com` and prints status, credits used, and a short content preview.
