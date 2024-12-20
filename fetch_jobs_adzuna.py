import requests
import json
import pandas as pd
from datetime import datetime
import argparse

APP_ID = "e74b959f"  
APP_KEY = "d0b8e5220b2e75aff9a3809295100015" 
BASE_URL = "https://api.adzuna.com/v1/api/jobs/fr/search"  # Base URL without page number

# Function to fetch job listings
def fetch_job_listings(query, results_per_page=20, page=1):
    """
    Fetches job listings from Adzuna API.

    Args:
        query (str): Job title or keyword to search for.
        results_per_page (int): Number of results per page.
        page (int): The page number to fetch.

    Returns:
        list: A list of job listings.
    """
    url = f"{BASE_URL}/{page}"  # Include page number in the URL path
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        # "what": query,
        "results_per_page": results_per_page,
        "content-type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])  # Adzuna returns job listings in "results"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching job listings: {e}")
        return []

# Function to parse Adzuna results into desired format
def parse_job_listings(jobs):
    """
    Parses Adzuna job listings into a structured format.

    Args:
        jobs (list): List of raw job data from Adzuna.

    Returns:
        list: Parsed job data with required fields.
    """
    parsed_jobs = []
    for job in jobs:
        try:
            parsed_jobs.append({
                "intitulé": job.get("title"),
                "catégorie": job.get("category", {}).get("tag"),
                "entreprise": job.get("company", {}).get("display_name"),
                "longitude": job.get("longitude"),
                "latitude" : job.get("latitude"),
                "type_contrat": job.get("contract_type"),
                "temps_contrat": job.get("contract_time"),  
                "date_publication": datetime.strptime(job["created"], "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d') if "created" in job else None,
                "url": job.get("redirect_url"),
                "salaire_min": job.get("salary_min"),
                "salaire_max": job.get("salary_max"),
                "description": job.get("description"),
            })
        except Exception as e:
            print(f"Error parsing job: {e}")
    return parsed_jobs

# Main script
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Fetch job listings from Adzuna API.")
    parser.add_argument("--pages", type=int, help="Total number of pages to fetch.")
    args = parser.parse_args()

    # Define search parameters
    query = "AI"  # Modify to your desired job title
    results_per_page = 20  # Adjust the number of jobs per page
    total_pages = args.pages  # Get total pages from arguments
    
    # Fetch job listings
    print("Fetching job listings...")
    all_jobs = []
    for page in range(1, total_pages + 1):
        print(f"Fetching page {page}...")
        jobs = fetch_job_listings(query, results_per_page, page)
        if not jobs:
            print(f"No more jobs found on page {page}.")
            break
        parsed_jobs = parse_job_listings(jobs)
        all_jobs.extend(parsed_jobs)

    # Save job listings to a CSV file
    df = pd.DataFrame(all_jobs)
    df.to_csv("adzuna_job_listings.csv", index=False, encoding="utf-8")
    
    print(f"Saved {len(all_jobs)} job listings to 'adzuna_job_listings.csv'.")
