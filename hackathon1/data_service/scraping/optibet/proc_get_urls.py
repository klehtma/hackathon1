import json
from pathlib import Path

# Get the directory where this Python file is located
BASE_DIR = Path(__file__).resolve().parent

NAME = "OPTIBET"

# Input:
# data_service/scraping/optibet/get_urls_data
folder = BASE_DIR / "get_urls_data"

print("Folder:", folder)
print("Folder exists:", folder.exists())

data_list = []

for file_path in folder.glob("opti_data*.json"):
    print(f"Processing file: {file_path.name}")

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data_list.append(data)

print(f"Loaded {len(data_list)} files")


# Process Optibet data
ids = []
teams = []

result_dic = {}

for data in data_list:
    try:
        # data is a list of matches
        for match in data:
            match_id = match["id"]
            home_team = match["player1"]["name"].strip()
            away_team = match["player2"]["name"].strip()

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
            f"Skipping data entry because of "
            f"{type(e).__name__}: {e}"
        )
        continue


# --------------------------------------------------
# Save result_dic
# --------------------------------------------------

# data_service/scraping/optibet/matching_logic/OPTIBET
output_folder = BASE_DIR.parent / "matching_logic" / NAME.lower()

# Create folder if it doesn't exist
output_folder.mkdir(parents=True, exist_ok=True)

# Output filename
output_file = output_folder / f"result_{NAME.lower()}.json"

# Save JSON
with output_file.open("w", encoding="utf-8") as f:
    json.dump(result_dic, f, indent=4, ensure_ascii=False)

print(f"\nSaved {len(result_dic)} matches")
print(f"Output file: {output_file}")