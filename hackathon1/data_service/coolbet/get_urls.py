import time
import json
import os

def get_cool_urls(competition_url, driver):
    result = []
    clubs = []
    data = []
    tries = 0
    while not data and tries < 3:
        try:
            with driver.expect_response(
                lambda r: "country=EE" in r.url and "limit=6" in r.url,
                timeout=10000
            ) as response_info:
                driver.goto(competition_url)
            data = response_info.value.json()

            
            print("\n✅ RESPONSE JSON RECEIVED\n")
        except Exception as e:
            print(f"Unsuccessful, trying again... ({e})")
            tries += 1

        print(data)

        #write this to json file for later use, to make name unique use competition name and timestamp
        with open(f"coolbet/get_urls_data/cool_data_{int(time.time())}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        #pass it to ligthweight llm to get strcuted

    return result, clubs