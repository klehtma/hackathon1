import time
import json
import os
from urllib.parse import urlparse

def get_epic_page(competition_url, driver):
    match_id = competition_url.split("=")[-1]
    tries = 0
    max_tries = 3
    output_dir = "epicbet/get_page_data"
    os.makedirs(output_dir, exist_ok=True)
    while tries < max_tries:
        data = {"activeOdds": [], "match.Get": None}
        responses = {"activeOdds": [], "match.Get": None}
        def handle_response(response):
            try:
                path = urlparse(response.url).path
                if "/s/core-proxy/public/sport-odds/activeOdds" in path:
                    responses["activeOdds"].append(response)
                elif "/s/core-proxy/public/sport-base/match.getSidebets" in path:
                    responses["match.Get"] = response
            except Exception as e:
                print(f"Error handling response: {e}")
        try:
            print(f"\nLoading page... attempt {tries + 1}/{max_tries}")
            driver.on("response", handle_response)
            # Load the page
            driver.goto(competition_url, wait_until="domcontentloaded")
            time.sleep(1)
            timeout = 10
            start_time = time.time()
            # Wait out the full timeout so we catch every activeOdds call,
            # not just the first one.
            while time.time() - start_time < timeout:
                found_active = len(responses["activeOdds"])
                found_match = 1 if responses["match.Get"] is not None else 0
                print(
                    f"\rWaiting for API responses: "
                    f"activeOdds={found_active}, match.Get={found_match}/1",
                    end="",
                )
                time.sleep(0.2)
            print()

            # Remove response listener
            driver.remove_listener("response", handle_response)

            # Check which endpoints we received
            missing = []
            if not responses["activeOdds"]:
                missing.append("activeOdds")
            if responses["match.Get"] is None:
                missing.append("match.Get")

            if missing:
                raise Exception(f"Missing API responses: {', '.join(missing)}")

            parsed_active = []
            for response in responses["activeOdds"]:
                try:
                    parsed_active.append(response.json())
                except Exception as e:
                    print(f"Could not parse activeOdds response as JSON: {e}")
            data["activeOdds"] = parsed_active

            try:
                data["match.Get"] = responses["match.Get"].json()
            except Exception as e:
                print(f"Could not parse match.Get response as JSON: {e}")
                data["match.Get"] = None

            print("\n✅ ALL API RESPONSES RECEIVED\n")

            print(f"ACTIVE ODDS: {len(data['activeOdds'])} response(s) captured")
            print(f"MATCH.GET:   {'OK' if data['match.Get'] is not None else 'FAILED'}")
            print("\nResponse data:")
            print(json.dumps(data, ensure_ascii=False, indent=4))
            filepath = f"epicbet/get_page_data/epic_data_{match_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"\n💾 Data saved to: {filepath}")
            return match_id
        except Exception as e:
            print(f"\n❌ Unsuccessful, trying again..."f" ({e})")
            try:
                driver.remove_listener("response", handle_response)
            except Exception:
                pass
            tries += 1
            if tries < max_tries:
                time.sleep(2)
    print(
        f"\n❌ Failed after {max_tries} attempts."
    )
    return None