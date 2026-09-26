from scraping.driver import Driver
import time
from pathlib import Path
from scraping.coolbet.get_urls import get_cool_urls
from scraping.epicbet.get_urls import get_epic_urls
from scraping.optibet.get_urls import get_opti_urls
import ollama

if __name__ == "__main__":
    # Example usage of the Driver context manager


    cool_comp = "https://www.coolbet.com/en/sports/basketball/germany/basketball-bundesliga"
    opti_comp = "https://www.optibet.ee/en/sport/prematch/Euroleague-494"
    epic_comp = "https://epicbet.com/en/sports/basketball/germany/germany-basketball-bundesliga"

    with Driver() as page:

        output_dir = Path(__file__).parent / "data"
        output_dir.mkdir(exist_ok=True)

        epic_urls, epic_clubs = get_epic_urls(epic_comp, page)
        
        opti_urls, opti_clubs = get_opti_urls(opti_comp, page)
        cool_urls, cool_clubs = get_cool_urls(cool_comp, page)
        exit()
        time.sleep(10)
        print(page.title())

        #setup llama chatbot to process the data and get structured data
        

        
        print(data)
        print(f"User's name is: {data['name']}")

        
        print(cool_urls)
        print(opti_urls)
        print(epic_urls)

    
