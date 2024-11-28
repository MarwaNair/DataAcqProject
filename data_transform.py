import pandas as pd
from googletrans import Translator

# Initialize Google Translator
translator = Translator()
adzuna_df = pd.read_csv("adzuna_job_listings.csv")
francetravail_df = pd.read_csv("francetravail_job_listings.csv")

# Translation mapping for field names
field_translation = {
    "title": "intitulé",
    "company": "entreprise",
    "location": "localisation",
    "description": "description",
    "employment_type": "type_contrat",
    "contract_type": "temps_contrat",
    "date_posted": "date_publication",
    "job_url": "url_offre"
}

# Translation mapping for content fields (employment type, contract type)
value_translation = {
    "full-time": "temps plein",
    "part-time": "temps partiel",
    "permanent": "CDI",
    "contract": "CDD",
    "temporary": "temporaire"
}

adzuna_df.rename(columns=field_translation, inplace=True)
adzuna_df["type_contrat"] = adzuna_df["type_contrat"].map(value_translation).fillna(adzuna_df["type_contrat"])
adzuna_df["temps_contrat"] = adzuna_df["temps_contrat"].map(value_translation).fillna(adzuna_df["temps_contrat"])

def translate_descriptions(dataframe, column_name):
    """Translate descriptions in the specified column using Google Translate."""
    translated_values = []
    for value in dataframe[column_name]:
        if pd.notna(value):  
            try:
                translated_value = translator.translate(value, src="en", dest="fr").text
                translated_values.append(translated_value)
            except Exception as e:
                print(f"Translation error for '{value}': {e}")
                translated_values.append(value) 
        else:
            translated_values.append(value)
    return translated_values

adzuna_df["description"] = translate_descriptions(adzuna_df, "description")
francetravail_df.rename(columns=field_translation, inplace=True)
final_dataset = pd.concat([adzuna_df, francetravail_df], ignore_index=True)

# Save the combined dataset to a CSV file
final_dataset.to_csv("combined_job_listings.csv", index=False, encoding="utf-8")