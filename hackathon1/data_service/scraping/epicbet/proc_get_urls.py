import json
from pathlib import Path

# Get the directory where this Python file is located
BASE_DIR = Path(__file__).resolve().parent

NAME = "EPICBET"

# data_service/scraping/epicbet/get_urls_data
folder = BASE_DIR / "get_urls_data"

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
ids = []
teams = []
result_dic = {}

for data in data_list:
    try:
        matches = data["result"]["data"]["matches"]

        for match in matches:
            try:
                match_id = match["id"]
                home_team = match["homeTeamName"].strip()
                away_team = match["awayTeamName"].strip()

                ids.append(match_id)
                teams.append((home_team, away_team))

                result_dic[match_id] = {
                    "home_team": home_team,
                    "away_team": away_team
                }

                print(
                    f"Match ID: {match_id}, "
                    f"Home Team: {home_team}, "
                    f"Away Team: {away_team}"
                )

            except (KeyError, TypeError) as e:
                print(
                    f"Skipping match because of "
                    f"{type(e).__name__}: {e}"
                )
                continue

    except (KeyError, TypeError) as e:
        print(
            f"Skipping data entry because of "
            f"{type(e).__name__}: {e}"
        )
        continue


# --------------------------------------------------
# Save result_dic
# --------------------------------------------------

# data_service/scraping/epicbet/matching_logic/EPICBET
output_folder = BASE_DIR.parent / "matching_logic" / NAME.lower()

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