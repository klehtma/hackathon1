from driver import Driver
import time
from pathlib import Path
from scraping.coolbet.get_urls import get_cool_urls
from scraping.epicbet.get_urls import get_epic_urls
from scraping.optibet.get_urls import get_opti_urls
from scraping.coolbet.get_page import get_cool_page
from scraping.epicbet.get_page import get_epic_page
from scraping.optibet.get_page import get_opti_page
from scraping.optibet.proc_get_page import process_optibet_data
from scraping.coolbet.proc_get_page import process_coolbet_data
from scraping.epicbet.proc_get_page import process_epicbet_data


cool_comp = "https://www.coolbet.com/en/sports/basketball/germany/basketball-bundesliga"
opti_comp = "https://www.optibet.ee/en/sport/prematch/Euroleague-494"
epic_comp = "https://epicbet.com/en/sports/basketball/germany/germany-basketball-bundesliga"

cool_comp1 = "https://www.coolbet.com/en/sports/match/6155250"
epic_comp1 = "https://epicbet.com/en/sports/football/england?matchId=2070636"
opti_comp1 = "https://www.optibet.ee/en/sport/prematch/event/Arsenal-Leeds-United-11231549"

with Driver() as page:

    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)

    successes = []
    """
    match_id_cool = get_cool_page(cool_comp1, page)
    match_id_epic = get_epic_page(epic_comp1, page)
    match_id_opti = get_opti_page(opti_comp1, page)
    """

    match_id_cool, match_id_epic, match_id_opti = 6155250, 2070636, 11231549
   

    if match_id_cool is not None and match_id_epic is not None and match_id_opti is not None:
        print("\nSuccess\n")
        process_coolbet_data(match_id_cool)
        process_epicbet_data(match_id_epic)
        process_optibet_data(match_id_opti)



    exit()

    get_epic_urls(epic_comp, page)
    get_opti_urls(opti_comp, page)
    get_cool_urls(cool_comp, page)

    exit()
    time.sleep(10)
    print(page.title())

    #setup llama chatbot to process the data and get structured data
    print(cool_urls)
    print(opti_urls)
    print(epic_urls)

    
