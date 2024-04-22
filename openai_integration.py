from openai import OpenAI
from typing import List
client = None

def initialize_api(api_key: str):
    """Initialize the OpenAI API with the provided API key."""
    global client
    client = OpenAI(api_key=api_key)
    
def send_analysis_request(prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 1500):
    """Send a request to the OpenAI API to analyze the provided text using the specified model."""
    try:
        # Adjusting to use ChatCompletion for newer API version compatibility
        response = client.chat.completions.create(model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=max_tokens)
        # Assuming the API returns a single message in the response for simplicity
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred while querying the OpenAI API: {str(e)}")
        return ""

def parse_api_response(response: str):
    """Placeholder function for any additional processing of the OpenAI API's response."""
    # This can be expanded based on specific needs, such as formatting the response.
    return response

# Example usage
if __name__ == "__main__":
    # api_key = "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"
    api_key = '''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'''
    initialize_api(api_key)
    prompt = "what is the best way to write code?"
    model = "gpt-3.5-turbo"  # Ensure you use the appropriate model for your needs.
    response = send_analysis_request(prompt, model)
    print(response)
