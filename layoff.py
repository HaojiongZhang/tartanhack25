import pandas as pd
from fuzzywuzzy import process
import matplotlib.pyplot as plt

def layoffs(company_name):
    df = pd.read_excel("data/filtered_WARN_data.xlsx")
    
    # Step 1: Fuzzy matching the company names
    unique_names = df['Company'].dropna().unique()
    matches = process.extract(company_name, unique_names)
    
    # Filter out matches that meet the threshold
    if matches:
        matched_names = [match[0] for match in matches if match[1] >= 80]
    else:
        return None
    
    target = matched_names[0]
    # Step 2: Filter the DataFrame for rows where the company name is one of the matched names
    filtered_df = df[df['Company'] == target]
    
    
    print(filtered_df)
    
    return filtered_df

if __name__ == "__main__":
    layoffs("amazon")