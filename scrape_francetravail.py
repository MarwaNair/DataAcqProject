import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta

# Function to scrape job postings using Selenium
def scrape_francetravail_jobs_selenium(max_pages, base_url, domaine):
    """
    Scrapes job postings from FranceTravail using Selenium.

    Args:
        max_pages (int): Maximum number of "Afficher les 20 offres suivantes" clicks.
        base_url (str): Base URL for job search.
        domaine (str): Job category name.

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
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "result")))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            job_cards = soup.find_all('li', class_='result')

            for job in job_cards:
                try:
                    link = job.find('a', href=True)
                    job_url = f"https://candidat.pole-emploi.fr{link['href']}" if link else None
                    if job_url in scraped_urls:
                        continue

                    scraped_urls.add(job_url)
                    driver.get(job_url)

                    region = driver.find_element(By.CSS_SELECTOR, 'span[itemprop="addressRegion"]').get_attribute("content")
                    salary = driver.find_element(By.CSS_SELECTOR, 'dd[itemprop="workHours"]').text
                    salary += " " + driver.find_element(By.CSS_SELECTOR, 'dd span[itemprop="baseSalary"] + ul li:first-child').text

                    title = job.find('h2', class_='t4').get_text(strip=True) if job.find('h2', class_='t4') else None
                    subtext = job.find('p', class_='subtext')
                    company = subtext.contents[0].get_text(strip=True).split('\n')[0] if subtext else None
                    description = job.find('p', class_='description').get_text(strip=True) if job.find('p', class_='description') else None
                    type_info = job.find('p', class_='contrat').get_text(strip=True).split("-") if job.find('p', class_='contrat') else None
                    employment_type = type_info[0].strip() if type_info else None
                    contract_type = type_info[-1].strip() if len(type_info) > 1 else None

                    raw_date = job.find('p', class_='date').get_text(strip=True) if job.find('p', class_='date') else None
                    if raw_date:
                        if "aujourd'hui" in raw_date:
                            date_posted = datetime.today().strftime('%Y-%m-%d')
                        elif "hier" in raw_date:
                            date_posted = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
                        elif "il y a" in raw_date:
                            days_ago = int(''.join(filter(str.isdigit, raw_date)))
                            date_posted = (datetime.today() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                        elif "plus de 30 jours" in raw_date:
                            date_posted = "more than 30 days ago"
                        else:
                            date_posted = raw_date
                    else:
                        date_posted = None

                    job_list.append({
                        'intitulé': title,
                        'catégorie': domaine,
                        'entreprise': company,
                        'localisation': region,
                        'type_contrat': employment_type,
                        'temps_contrat': contract_type,
                        'date_publication': date_posted,
                        'url': job_url,
                        'salaire': salary,
                        'description': description,
                    })
                except Exception as e:
                    print(f"Error parsing job: {e}")

            try:
                next_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'btn-primary') and contains(@href, 'afficherplusderesultats')]"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
            except Exception as e:
                print("No more pages to load or an error occurred:", e)
                break

    finally:
        driver.quit()

    return job_list

# Main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape job postings from FranceTravail.")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to scrape for each job category.")
    args = parser.parse_args()

    domaines = {
        "F": "Bâtiment / Travaux Publics",
        "D": "Commerce / Vente",
        "E": "Communication / Multimédia",
        "M14": "Conseil / Etudes",
        "M13": "Direction d'entreprise",
        "A": "Espaces verts et naturels / Agriculture / Pêche / Soins aux animaux",
        "G": "Hôtellerie - Restauration / Tourisme / Animation",
        "C15": "Immobilier",
        "H": "Industrie",
        "M18": "Informatique / Télécommunication",
        "I": "Installation / Maintenance",
        "M17": "Marketing / Stratégie commerciale",
        "M15": "Ressources Humaines",
        "J": "Santé",
        "M16": "Secrétariat / Assistanat",
        "K": "Services à la personne / à la collectivité",
        "L": "Spectacle",
        "L14": "Sport",
        "N": "Transport / Logistique",
    }

    jobs = []

    print("Scraping job postings from FranceTravail...")
    for code, domaine in domaines.items():
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        base_url = f"https://candidat.pole-emploi.fr/offres/recherche?domaine={code}&lieux=01P"
        jobs.extend(scrape_francetravail_jobs_selenium(max_pages=args.pages, base_url=base_url, domaine=domaine))

    df = pd.DataFrame(jobs)
    df.to_csv('francetravail_job_listings.csv', index=False, encoding='utf-8')
    print(f"Saved {len(df)} job listings to 'francetravail_job_listings.csv'.")
