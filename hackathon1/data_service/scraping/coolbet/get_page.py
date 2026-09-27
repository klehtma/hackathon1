import time
import json
import os
from urllib.parse import urlparse

def get_cool_page(competition_url, driver):
    tries = 0
    max_tries = 3
    data = {"fo": None, "fo-line": None, "sidebets": None}
    output_dir = "coolbet/get_page_data"
    os.makedirs(output_dir, exist_ok=True)
    while tries < max_tries:
        data = {"fo": None, "fo-line": None, "sidebets": None}
        responses = {}
        def handle_response(response):
            try:
                path = urlparse(response.url).path
                if path == "/s/sb-odds/odds/current/fo":
                    responses["fo"] = response
                elif path == "/s/sb-odds/odds/current/fo-line/":
                    responses["fo-line"] = response
                elif path == "/s/sbgate/sports/fo-market/sidebets":
                    responses["sidebets"] = response
            except Exception as e:
                print(f"Error handling response: {e}")
        try:
            print(f"\nLoading page... attempt {tries + 1}/{max_tries}")
            driver.on("response", handle_response)
            # Load the page
            driver.goto(competition_url, wait_until="domcontentloaded")
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                found = len(responses)
                print(f"\rWaiting for API responses: " f"{found}/3",end="")
                if found == 3:
                    break
                time.sleep(0.2)
            print()

            # Remove response listener
            driver.remove_listener("response", handle_response)

            # Check which endpoints we received
            missing = [name for name in data if name not in responses]

            if missing:
                raise Exception(f"Missing API responses: {', '.join(missing)}")
            for name, response in responses.items():
                try:
                    data[name] = response.json()
                except Exception as e:
                    print(
                        f"Could not parse {name} response as JSON: {e}"
                    )
                    data[name] = None
            print("\n✅ ALL API RESPONSES RECEIVED\n")

            print(f"FO:       {'OK' if data['fo'] is not None else 'FAILED'}")
            print(f"FO-LINE:  {'OK' if data['fo-line'] is not None else 'FAILED'}")
            print(f"SIDEBETS: {'OK' if data['sidebets'] is not None else 'FAILED'}")
            print("\nResponse data:")
            print(json.dumps(data,ensure_ascii=False,indent=4))
            with open(f"coolbet/get_page_data/cool_data_{int(time.time())}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"\n💾 Data saved to: {f"coolbet/get_page_data/cool_data_{int(time.time())}.json"}")
            return
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
    