import os

from scrapi_sdk import ScrapeRequest, ScrapiClient

URL = "https://deventerprise.com"
api_key = os.getenv("SCRAPI_API_KEY", "")

request = ScrapeRequest(URL)
request.use_browser = True
request.include_screenshot = True
request.include_video = True
request.include_pdf = True

with ScrapiClient(api_key) as client:
    print(f"Scraping {URL}")
    print()
    response = client.scrape(request)

if response is None:
    print("No response was returned by ScrAPI.")
else:
    preview = (response.content or "").strip().replace("\n", " ")
    if len(preview) > 200:
        preview = preview[:200] + "..."

    print(f"Request URL    : {response.request_url}")
    print(f"Response URL   : {response.response_url}")
    print(f"Status Code    : {response.status_code}")
    print(f"Duration       : {response.duration}")
    print(f"Credits Used   : {response.credits_used}")
    print(f"Screenshot URL : {response.screenshot_url}")
    print(f"Video URL      : {response.video_url}")
    print(f"PDF URL        : {response.pdf_url}")
    print(f"Content Hash   : {response.content_hash}")
    print(f"Preview        : {preview}")
    print()
