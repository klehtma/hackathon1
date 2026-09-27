import time
import json

def get_opti_page(competition_url, driver):

    match_id = competition_url.split("-")[-1]

    data = []
    tries = 0
    while not data and tries < 3:
        try:
            with driver.expect_response(
                lambda r: f"https://ensb-trading.optibet.ee/en/events/{match_id}?" in r.url,
                timeout=10000
            ) as response_info:
                driver.goto(competition_url)
            data = response_info.value.json()
            print("\n✅ RESPONSE JSON RECEIVED\n")
        except Exception as e:
            print(f"Unsuccessful, trying again... ({e})")
            tries += 1
        print(data)

        with open(f"optibet/get_page_data/opti_data_{int(time.time())}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

