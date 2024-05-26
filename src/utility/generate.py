from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("API_KEY")


def generate(utterance: str, settings_text: str = '', dialogue_history: list = [], model='gpt-4-0613', temperature=0.0, next_response=False):

    print(model)
    print(temperature)
    # print('temperature:', temperature)
    # print(model)
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
            # defaults to os.environ.get("OPENAI_API_KEY")
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
    # print(response_text)
    return response_text, dialogue_history


if __name__ == '__main__':
    utt = "Say this is a test"
    model = "gpt-3.5-turbo"
    temperature = 0

    print(generate(utterance=utt, model=model, temperature=temperature))
