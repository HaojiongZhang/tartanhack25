import requests
import os
import json
from datetime import datetime, timedelta
from fuzzywuzzy import process
from config import SEC_API_KEY, SEC_EXTRACT_API_URL
from llm import summarize_text
CACHE_FILE = "company_tickers_cache.json"
CACHE_DURATION = timedelta(days=7)  # Refresh cache every 7 days

def load_cache():
    """Load cached data if it exists and is still valid."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            data = json.load(file)
            cache_time = datetime.fromisoformat(data.get("timestamp"))
            if datetime.now() - cache_time < CACHE_DURATION:
                return data.get("companies")
    return None

def save_cache(companies):
    """Save company data to cache with a timestamp."""
    with open(CACHE_FILE, "w") as file:
        data = {
            "timestamp": datetime.now().isoformat(),
            "companies": companies
        }
        json.dump(data, file)

def get_company_data():
    """Fetch company data, using cache if available."""
    # Try to load cache
    cached_data = load_cache()
    if cached_data:
        print("Using cached data.")
        return cached_data

    # If no valid cache, fetch from SEC
    headers = {
        "User-Agent": "YourName YourEmail@example.com"  # Replace with actual details
    }
    response = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
    if response.status_code == 200:
        companies = response.json()
        save_cache(companies)  # Save the response to cache
        print("Fetched data from SEC and cached it.")
        return companies
    else:
        print(f"Error: {response.status_code}")
        return None

def get_ticker_or_cik(company_name):
    """
    Retrieve the ticker and CIK of a company based on its name.
    Uses cached or fetched data from SEC.
    """
    company_data = get_company_data()
    if not company_data:
        print("Unable to fetch company data.")
        return None, None

    # Flatten data for easy searching
    companies = {data['title']: data['cik_str'] for data in company_data.values()}

    # Use fuzzy matching for imprecise names
    match, score = process.extractOne(company_name, companies.keys())
    if score > 70:  # Ensure a reasonable match score
        print(f"Matched '{company_name}' to '{match}' with score {score}.")
        return match, companies[match]
    else:
        print(f"No close match found for '{company_name}'.")
        return None, None


def get_filing_urls(cik, filing_type="10-K"):
    """
    Fetch valid SEC filing URLs for a given company CIK and filing type.
    """
    headers = {"User-Agent": "YourName YourEmail@example.com"}
    cik_padded = str(cik).zfill(10)  # Pad CIK to 10 digits as required by SEC
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

    # Fetch filing data from SEC
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching data for CIK {cik}: {response.status_code}")
        return []

    data = response.json()
    filings = data.get("filings", {}).get("recent", {})
    
    # Extract URLs for the specific filing type
    filing_urls = []
    for acc_number, form_type in zip(filings.get("accessionNumber", []), filings.get("form", [])):
        if form_type == filing_type:
            # Construct valid SEC URL
            acc_number_cleaned = acc_number.replace("-", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_number_cleaned}/index.html"
            filing_urls.append(filing_url)

    return filing_urls




def extract_section(filing_url, item, return_type="text"):
    """
    Extract a specific section from an SEC filing using the SEC-API Extractor.
    
    Parameters:
        filing_url (str): URL of the SEC filing (.txt or .htm version).
        item (str): Item to extract (e.g., "1A" for 10-K Risk Factors).
        return_type (str): "text" or "html". Default is "text".
        
    Returns:
        str: Extracted section content.
    """
    # Build the request
    params = {
        "url": filing_url,
        "item": item,
        "type": return_type,
        "token": SEC_API_KEY,
    }
    response = requests.get(SEC_EXTRACT_API_URL, params=params)
    
    # Check for success
    if response.status_code == 200:
        return response.text  # Return extracted content
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


import re
def clean_text_regex(text):
    # Remove the specific patterns
    cleaned = re.sub(r'.*\|.*Form 10-K \|.*\n?', '', text)
    cleaned = re.sub(r'\n\n', '\n', text)
    return cleaned.strip()


def get_10k_section_text(
        company_name, store_dir="sec-edgar-filings",
        section_ids = ["1", "1A", "2", "7", "7A", "8"]):
    matched_name, cik = get_ticker_or_cik(company_name)
    filing_urls = get_filing_urls(cik, "10-K")
    text = ""
    file_name = os.path.join(
        store_dir, matched_name.replace(' ', '_'), "10K.txt")
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, "w") as file:
        for section_id in  section_ids:
            relevant_section = extract_section(filing_urls[0], section_id)
            if relevant_section is not None:
                cleaned_section_text = clean_text_regex(relevant_section)
                text += cleaned_section_text
                file.write(cleaned_section_text)
    return text

def get_summary(company_name):
    text = get_10k_section_text(company_name)
    sum = summarize_text(text)
    return sum

if __name__ == "__main__":
    print(get_summary('Nvidia'))