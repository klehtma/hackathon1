import json
from pathlib import Path

# Get the directory where this Python file is located
BASE_DIR = Path(__file__).resolve().parent

NAME = "EPICBET"

# data_service/scraping/coolbet/get_urls_data
folder = BASE_DIR / "get_page_data"

print("Folder:", folder)
print("Folder exists:", folder.exists())

data_list = []

for file_path in folder.glob("epic_data*.json"):
    print(f"Processing file: {file_path.name}")

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data_list.append(data)

print(f"Loaded {len(data_list)} files")


# Process Epicbet data


#generate outcome_id mapping

outcome_id = {}

for data in data_list:
    try:
        for i in range(len(data["activeOdds"])):
            for a in range(len(data["activeOdds"][i]["result"]["data"])):
                outcome_id[data["activeOdds"][i]["result"]["data"][a]["outcomeId"]] = data["activeOdds"][i]["result"]["data"][a]["value"]

    except (KeyError, TypeError, IndexError) as e:
        print(
            f"Skipping data entry because of "
            f"{type(e).__name__}: {e}"
        )
        continue

ids = []
teams = []
result_dic = {}

for data in data_list:
    try:
        matches = data["match.Get"]["result"]["data"]["marketGroups"]
        
        for index in range(len(matches)):
            try:
                for outcome in matches[index]["markets"]:
                    
                    print("ASDF")
                    print(outcome)
                    market_name = outcome["name"]
                    
                    line = outcome.get("line", "")
                    if line is None:
                        line = ""
                    for outcome_values in outcome["outcomes"]:
                        total_name = market_name + " " + outcome_values.get("name", "") + " " + str(line)
                        total_name = total_name.strip()  
                        outcome_value = outcome_id[outcome_values["id"]]

                        result_dic[total_name] = outcome_value

            except (KeyError, TypeError) as e:
                print(
                    f"Skipping match because of "
                    f"{type(e).__name__}: {e}"
                )
                continue

    except (KeyError, TypeError, IndexError) as e:
        print(
            f"Skipping data entry because of "
            f"{type(e).__name__}: {e}"
        )
        continue
# --------------------------------------------------
# Save result_dic
# --------------------------------------------------

# data_service/scraping/coolbet/matching_logic/COOLBET
output_folder = BASE_DIR / "processed_data" / NAME.lower()

# Create folder if it doesn't exist
output_folder.mkdir(parents=True, exist_ok=True)

# Output file
output_file = output_folder / f"result_{NAME.lower()}.json"

# Save result_dic as JSON
with output_file.open("w", encoding="utf-8") as f:
    json.dump(
        result_dic,
        f,
        indent=4,
        ensure_ascii=False
    )

print(f"\nSaved {len(result_dic)} matches")
print(f"Output file: {output_file}")