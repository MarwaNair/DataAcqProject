import pandas as pd
from googletrans import Translator
import subprocess
import json
import re
from transformers import pipeline


# France Travail ########

francetravail_df = pd.read_csv("test_francetravail_job_listings.csv")

# Category mapping
frt_category_mapping = {
    "Achats / Comptabilité / Gestion": "Accounting & Finance Jobs",
    "Arts / Artisanat d'art": "Creative & Design Jobs",
    "Banque / Assurance": "Accounting & Finance Jobs",
    "Bâtiment / Travaux Publics": "Trade & Construction Jobs",
    "Commerce / Vente": "Sales Jobs",
    "Communication / Multimédia": "PR, Advertising & Marketing Jobs",
    "Conseil / Etudes": "Consultancy Jobs",
    "Direction d'entreprise": "Other/General Jobs",
    "Espaces verts et naturels / Agriculture / Pêche / Soins aux animaux": "Other/General Jobs",
    "Hôtellerie - Restauration / Tourisme / Animation": "Hospitality & Catering Jobs",
    "Immobilier": "Property Jobs",
    "Industrie": "Manufacturing Jobs",
    "Informatique / Télécommunication": "IT Jobs",
    "Installation / Maintenance": "Maintenance Jobs",
    "Marketing / Stratégie commerciale": "PR, Advertising & Marketing Jobs",
    "Ressources Humaines": "HR & Recruitment Jobs",
    "Santé": "Healthcare & Nursing Jobs",
    "Secrétariat / Assistanat": "Admin Jobs",
    "Services à la personne / à la collectivité": "Social work Jobs",
    "Spectacle": "Other/General Jobs",
    "Sport": "Other/General Jobs",
    "Transport / Logistique": "Logistics & Warehouse Jobs"
}

francetravail_df['catégorie'] = francetravail_df['catégorie'].map(frt_category_mapping)

print("--------------------")
# Salary extraction
def extract_salary(desc):
    qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2",)

    answer = qa_pipeline(question="What is the salary per month here?", context=desc)["answer"]

    try:
        numbers = re.findall(r"\d+\.?\d*", answer)
        monthly_salary = float(numbers[0])
    except:
        monthly_salary = float('nan')
    
    return monthly_salary


francetravail_df['salaire'] = francetravail_df['salaire'].apply(extract_salary)


# Adzuna #######
adzuna_df = pd.read_csv("test_adzuna_job_listings.csv")

# value translation
value_translation = {
    "full-time": "temps plein",
    "part-time": "temps partiel",
    "permanent": "CDI",
    "contract": "CDD",
    "temporary": "temporaire"
}
adzuna_df["type_contrat"] = adzuna_df["type_contrat"].map(value_translation).fillna(adzuna_df["type_contrat"])
adzuna_df["temps_contrat"] = adzuna_df["temps_contrat"].map(value_translation).fillna(adzuna_df["temps_contrat"])



# decription translation
translator = Translator()

def translate_descriptions(dataframe, column_name):
    """Translate descriptions in the specified column using Google Translate."""
    translated_values = []
    for value in dataframe[column_name]:
        if pd.notna(value):  
            try:
                translated_value = translator.translate(value, src="en", dest="fr").text
                translated_values.append(translated_value)
            except Exception as e:
                translated_values.append(value) 
        else:
            translated_values.append(value)
    return translated_values

adzuna_df["description"] = translate_descriptions(adzuna_df, "description")


# Localization Extraction
def get_region(longitude, latitude):
    # Format the URL with the given latitude and longitude
    url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"
    

    # Call curl and capture the response without the User-Agent header
    response = subprocess.check_output(['curl', url])
    
    # Convert the response from bytes to JSON
    localization_data = json.loads(response)
    return localization_data['address']['state']
    
adzuna_df['localisation'] = adzuna_df.apply(lambda row: get_region(row['longitude'], row['latitude']), axis=1)
adzuna_df = adzuna_df.drop('longitude', axis=1)
adzuna_df = adzuna_df.drop('latitude', axis=1)

columns = adzuna_df.columns.tolist()
columns.insert(3, columns.pop(columns.index('localisation')))
df = adzuna_df[columns]



# Categorie mapping
adzuna_category_mapping = {
    "accounting-finance-jobs": "Accounting & Finance Jobs",
    "it-jobs": "IT Jobs",
    "sales-jobs": "Sales Jobs",
    "customer-services-jobs": "Customer Services Jobs",
    "engineering-jobs": "Engineering Jobs",
    "hr-jobs": "HR & Recruitment Jobs",
    "healthcare-nursing-jobs": "Healthcare & Nursing Jobs",
    "hospitality-catering-jobs": "Hospitality & Catering Jobs",
    "pr-advertising-marketing-jobs": "PR, Advertising & Marketing Jobs",
    "logistics-warehouse-jobs": "Logistics & Warehouse Jobs",
    "teaching-jobs": "Teaching Jobs",
    "trade-construction-jobs": "Trade & Construction Jobs",
    "admin-jobs": "Admin Jobs",
    "legal-jobs": "Legal Jobs",
    "creative-design-jobs": "Creative & Design Jobs",
    "graduate-jobs": "Graduate Jobs",
    "retail-jobs": "Retail Jobs",
    "consultancy-jobs": "Consultancy Jobs",
    "manufacturing-jobs": "Manufacturing Jobs",
    "scientific-qa-jobs": "Scientific & QA Jobs",
    "social-work-jobs": "Social work Jobs",
    "travel-jobs": "Travel Jobs",
    "energy-oil-gas-jobs": "Energy, Oil & Gas Jobs",
    "property-jobs": "Property Jobs",
    "charity-voluntary-jobs": "Charity & Voluntary Jobs",
    "domestic-help-cleaning-jobs": "Domestic help & Cleaning Jobs",
    "maintenance-jobs": "Maintenance Jobs",
    "part-time-jobs": "Part time Jobs",
    "other-general-jobs": "Other/General Jobs",
    "unknown": "Unknown"
}

adzuna_df['catégorie'] = adzuna_df['catégorie'].map(adzuna_category_mapping)

# Salary normalization
def salary_norm(salary):
    if salary is not None:
        return float(salary)/12.0
    else:
        return salary 
    
adzuna_df['salaire_min'] = adzuna_df['salaire_min'].apply(salary_norm)
adzuna_df['salaire_max'] = adzuna_df['salaire_max'].apply(salary_norm)


#  Merging   #####
final_dataset = pd.concat([adzuna_df, francetravail_df], ignore_index=True)
order = ['intitulé', 'catégorie', 'entreprise', 'localisation', 'type_contrat', 'temps_contrat',
       'date_publication', 'url', 'salaire_min', 'salaire_max', 'salaire', 'description']

final_dataset = final_dataset[order]

final_dataset.to_csv("combined_job_listings.csv", index=False, encoding="utf-8")