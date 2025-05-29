from openai import OpenAI
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()
API_KEY = os.environ.get("API_KEY")

def generate(utterance: str, settings_text: str = '', dialogue_history: list = [], model='gpt-4.1', temperature=0.0, next_response=False):

    if len(dialogue_history) == 0 and len(settings_text) != 0:
        system = {"role": "system", "content": settings_text}
        dialogue_history.append(system)
    if len(utterance):
        new_message = {"role": "user", "content": utterance}
        dialogue_history.append(new_message)

    if next_response:
        response_text = next_response
    else:
        client = OpenAI(
            api_key=API_KEY,
        )
        response = client.chat.completions.create(
            model=model,
            messages=dialogue_history,
            temperature=temperature
        )
        response_text = response.choices[0].message.content
    response_message = {"role": "assistant", "content": response_text}
    dialogue_history.append(response_message)

    return response_text, dialogue_history

def warm_up():
    # Warm up the OpenAI API client to avoid cold start issues, max_tokens=1
    client = OpenAI(
        api_key=API_KEY,
    )
    response = client.chat.completions.create(
        model='gpt-4.1',
        messages=[{"role": "user", "content": "Hi"}],
        temperature=0.0,
        max_tokens=1
    )
    print("Warm-up completed: {}".format(response))
    return

if __name__ == '__main__':
    from settings.config import MODEL
    utt = "Say this is a test"
    model = MODEL
    temperature = 0.0

    print(generate(utterance=utt, model=model, temperature=temperature))
