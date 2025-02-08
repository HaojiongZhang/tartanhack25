import csv
import pandas as pd
from jobspy import scrape_jobs
from fuzzywuzzy import process
from tenacity import retry, stop_after_attempt, wait_exponential

def get_filtered_company_jobs(company_name, position, results_wanted=20, hours_old=72, match_threshold=80):
    """
    Scrapes job postings for a specific company using JobSpy and filters results accurately.
    
    :param company_name: The company name to search for.
    :param results_wanted: Number of job results to retrieve.
    :param hours_old: Filters jobs posted within the last X hours.
    :param match_threshold: Minimum similarity score for fuzzy matching (default = 80).
    :return: Filtered DataFrame of jobs at the target company.
    """
    
    # Step 1: Scrape job listings
    jobs = scrape_jobs(
        site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"],
        search_term=f'"{position} at {company_name}"',  # Ensures a close match
        results_wanted=results_wanted,
        hours_old=hours_old
    )
    
    # If no jobs found, return early
    if jobs.empty:
        print(f"No jobs found for {company_name}")
        return None

    print(f"Found {len(jobs)} jobs related to {company_name}")

    # Step 2: Fuzzy match company names
    unique_companies = jobs['company'].dropna().unique().tolist()
    matches = process.extract(company_name, unique_companies)

    # Step 3: Determine the best-matching company name
    if not matches:
        print(f"No similar company names found for {company_name}.")
        return None

    best_match, score = matches[0]

    if score < match_threshold:
        print(f"Warning: Low match score ({score}) for {company_name}. Best match found: {best_match}")
        return None

    # Step 4: Filter jobs based on the best-matching company name
    filtered_df = jobs[jobs['company'].str.contains(best_match, case=False, na=False)]

    if filtered_df.empty:
        print(f"No exact job listings found for {best_match}")
        return None
    relevant_columns = ["company", "title", "location", "job_url"]
    print(f"Filtered {len(filtered_df)} jobs for {best_match}")

    return filtered_df[relevant_columns]


def get_company_jobs(self, company_name, position="Engineer"):
    """get_company_jobs"""
    @retry(stop=stop_after_attempt(3), 
          wait=wait_exponential(multiplier=1, min=4, max=10))
    def _retryable_job_search():
        return get_filtered_company_jobs(
            company_name=company_name,
            position=position,
            results_wanted=20,
            hours_old=72,
            match_threshold=80
        )
    
    try:
        return _retryable_job_search()
    except Exception as e:
        print(f"职位搜索失败: {str(e)}")
        return pd.DataFrame()

# Example Usage
if __name__ == "__main__":
    company_name = "nvidia"  
    position = "Software Engineer"
    filtered_jobs = get_filtered_company_jobs(company_name, position)