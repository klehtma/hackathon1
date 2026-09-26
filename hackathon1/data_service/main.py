from driver import Driver
import time
from pathlib import Path
from coolbet.get_urls import get_cool_urls
from epicbet.get_urls import get_epic_urls
from optibet.get_urls import get_opti_urls
import ollama


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
    

    prompt_content = """
    Your job is to tell if the 
    {
        "name": "string",
        "age": "integer",
        "city": "string"
    }
    """

    response = ollama.chat(
        model='qwen3:0.6b',
        messages=[
            {
                'role': 'system',
                'content': 'You are a data extraction assistant. Always respond with pure JSON.'
            },
            {
                'role': 'user',
                'content': prompt_content
            }
        ],
        format='json'  # <-- Enforces JSON mode at the Ollama engine level
    )

    # The response content is guaranteed to be a stringified JSON
    json_string = response.message.content

    # Parse it into a native Python dictionary
    data = json.loads(json_string)
    print(data)
    print(f"User's name is: {data['name']}")

    
    print(cool_urls)
    print(opti_urls)
    print(epic_urls)

    
