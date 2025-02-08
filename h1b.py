from fuzzywuzzy import process
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd


def process_and_match_companies(input_company):
    fp = "data/h1binfo.xlsx"

    df = pd.read_excel(fp)
    unique_names = df['Employer (Petitioner) Name'].dropna().unique()
    matches = process.extract(input_company, unique_names)
    
    # Filter out matches that meet the threshold
    matched_names = [match[0] for match in matches if match[1] >= 50]
    
    if not matched_names:
        print("No similar company names found above the threshold.")
        return
    
    print("Matched Company Names:", matched_names)
    
    # Step 2: Filter the DataFrame for rows where the company name is one of the matched names
    filtered_df = df[df['Employer (Petitioner) Name'].isin(matched_names)]
    return filtered_df
    

if __name__ == "__main__":
    input_company = "nvidia"
    process_and_match_companies(input_company)