from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta


# Set up the Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
driver = webdriver.Chrome(options=options)

# Base URL for FranceTravail job search
base_url = "https://candidat.pole-emploi.fr/offres/recherche?lieux=01P"

# Function to scrape job postings using Selenium
def scrape_francetravail_jobs_selenium(max_pages=2):
    """
    Scrapes job postings from FranceTravail using Selenium.

    Args:
        max_pages (int): Maximum number of "Afficher les 20 offres suivantes" clicks.

    Returns:
        list: A list of dictionaries containing job information.
    """
    job_list = []
    scraped_urls = set()  # Keep track of scraped job URLs to avoid duplicates

    try:
        # Load the page
        driver.get(base_url)
        wait = WebDriverWait(driver, 10)  # Wait for elements to load

        for page in range(max_pages):
            print(f"Scraping page {page + 1}...")
            # Wait for job cards to load
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "result")))

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_cards = soup.find_all('li', class_='result')

            for job in job_cards:
                try:
                    # Extract job URL (used as a unique identifier)
                    link = job.find('a', href=True)
                    job_url = f"https://candidat.pole-emploi.fr{link['href']}" if link else None

                    # Skip the job if it's already been scraped
                    if job_url in scraped_urls:
                        continue

                    # Add the job URL to the set of scraped URLs
                    scraped_urls.add(job_url)

                    # Extract job title
                    title = job.find('h2', class_='t4').get_text(strip=True) if job.find('h2', class_='t4') else None

                    # Extract company name (your logic retained)
                    subtext = job.find('p', class_='subtext')
                    company = subtext.contents[0].get_text(strip=True).split('\n')[0] if subtext else None

                    # Extract location
                    location_span = subtext.find('span') if subtext else None
                    location = location_span.get_text(strip=True).split(" - ")[-1] if location_span else None

                    # Extract job description
                    description = job.find('p', class_='description').get_text(strip=True) if job.find('p', class_='description') else None

                    # Extract employment type and contract type
                    type_info = job.find('p', class_='contrat').get_text(strip=True).split("-") if job.find('p', class_='contrat') else None
                    employment_type = type_info[0].strip() if type_info else None
                    contract_type = type_info[-1].strip() if len(type_info) > 1 else None

                    # Extract date posted
                    try:
                        raw_date = job.find('p', class_='date').get_text(strip=True) if job.find('p', class_='date') else None
                        if raw_date:
                            raw_date = raw_date.lower()
                            if "aujourd'hui" in raw_date:
                                date_posted = datetime.today().strftime('%Y-%m-%d')  # Today's date
                            elif "hier" in raw_date:
                                date_posted = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # Yesterday's date
                            elif "il y a" in raw_date:
                                # Handle "il y a x jours"
                                try:
                                    days_ago = int(''.join(filter(str.isdigit, raw_date)))  # Extract number of days
                                    date_posted = (datetime.today() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                                except ValueError:
                                        date_posted = None  # In case of unexpected format
                            elif  "plus de 30 jours" in raw_date:
                                    date_posted = "more than 30 days ago"
                                    
                            else:
                                date_posted = raw_date
                        else:
                            date_posted = None
                    except Exception as e:
                        date_posted = None
                        print(f"Error parsing date: {e}")

                    # Append the job details to the list
                    job_list.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        # 'description': description,
                        'employment_type': employment_type,
                        'contract_type': contract_type,
                        'date_posted': date_posted,
                        'job_url': job_url,
                    })
                except Exception as e:
                    print(f"Error parsing job: {e}")

            # Locate the "Afficher les 20 offres suivantes" button by its `class` or `href`
            try:
                next_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'btn-primary') and contains(@href, 'afficherplusderesultats')]"))
                )
                driver.execute_script("arguments[0].click();", next_button)  # Click the button
                time.sleep(3)  # Allow time for the next set of jobs to load
            except Exception as e:
                print("No more pages to load or an error occurred:", e)
                break

    finally:
        driver.quit()

    return job_list

# Main script
if __name__ == "__main__":
    max_pages_to_scrape = 5  # Number of "Afficher les 20 offres suivantes" clicks
    print("Scraping job postings from FranceTravail...")

    # Scrape job postings
    jobs = scrape_francetravail_jobs_selenium(max_pages=max_pages_to_scrape)

    # Convert the job list to a DataFrame
    df = pd.DataFrame(jobs)

    # Save to CSV
    df.to_csv('francetravail_job_listings.csv', index=False, encoding='utf-8')
    print(f"Saved {len(df)} job listings to 'francetravail_job_listings.csv'.")
