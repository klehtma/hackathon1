import ollama 
import json

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

    