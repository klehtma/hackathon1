import time
import json

def get_epic_urls(competition_url, driver):
    data = []
    
    tries = 0
    while not data and tries < 3:
        try:
            print("Starting epic_get_urls")
            with driver.expect_response(
                    lambda r: "public/sport-base/match.getFoByLeague?input=%" in r.url,
                    timeout=20000
            ) as response_info:
                print("Got response! epic")
                driver.goto(competition_url)
            data = response_info.value.json()

        except Exception as e:
            print("get_epic_urls_error1")
            print(f"Unsuccessful, trying again... ({e})")
            tries += 1

        print(data)
        #write this to json file for later use, to make name unique use competition name and timestamp
        with open(f"epicbet/get_urls_data/epic_data_{int(time.time())}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        #pass to lightweight llm to get structured data
        
        
