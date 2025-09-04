import json
import requests
import pandas as pd
import time
from typing import List, Dict, Any

API_URL = "http://localhost:5000/orbit/sniffer_ai"         # change path if needed
NO_OF_URLS_TO_CRAWL = 1              # set to len(urls) to crawl all URLs per entity
DEFAULT_KEYWORDS = ["string"]        # override if needed
TIMEOUT_SECONDS = 120

def build_payload(entity: str, urls: List[str], prompt: str, source: str, googleSearch: bool, snifferTool: bool, enableSearch: bool, enableRefinement: bool) -> Dict[str, Any]:
    return {
        "urls": urls,
        "entity": entity,
        "prompt": prompt,
        "source": source,
        "googleSearch": googleSearch,
        "snifferTool": snifferTool,
        "enableSearch": enableSearch,
        "enableRefinement": enableRefinement,
        "keywordsToSearch": [],
    }

headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
}


# with open(r"C:\Users\Asheem Siwach\Downloads\bank_data_scraper\lender_urls - Copy.json", "r") as file:
#     data = json.load(file)

# Extract the data from the AdvisersKhoj using the csv file
advisers_data = pd.read_csv(r"D:\Orbit\SniffrAI\app\testing\advisers_new_data.csv")

left_items = []
total = advisers_data.shape[0]
for index, row in advisers_data.iterrows():
    if index >= 57:
        urls = [f"https://www.advisorkhoj.com/{row['location']}/{row['profession']}?distance=5&experience=1&sortby=Recommended"]
        prompt = f"""Scroll the page till the last of the page and extract all the necessary details of the entities 
        present on the page related to the {row['profession']} for location {row['location']}. 
        You can find the data in the class 'relative' or 'row'.
        """
        entity = row['profession']
        source = "advisorkhoj"
        payload = build_payload(entity, urls, prompt, source, googleSearch=False, snifferTool=True, enableSearch=False, enableRefinement=False)
        # payload = build_payload(entity, [])

        print("---------------------------------PAYLOAD---------------------------------")
        print(payload)
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
            print(f"HTTP {resp.status_code}")
            time.sleep(5)
            if resp.status_code != 200:
                left_items.append([entity, row['location']])
        except Exception as e:
            print(f"Error: {e}")
            continue
    else:
        pass

    print(f"---------------------------------{index+1}/{total} ENDS---------------------------------")

df = pd.DataFrame(left_items, columns=['profession', 'location'])
df.to_csv(r"D:\Orbit\SniffrAI\app\testing\left_items2.csv", index=False)