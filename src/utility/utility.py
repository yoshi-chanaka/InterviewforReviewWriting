import json
import re


def initialize():

    data = {
        'prompts': {},
        'product': {},
        'history': [],
        'saveable': 1,
    }
    with open('prompts/begin_interview.json', 'r') as f:
        data['prompts']['interview'] = json.load(f)
    with open('prompts/generate_review.json', 'r') as f:
        data['prompts']['review'] = json.load(f)
    with open('prompts/generate_rating.json', 'r') as f:
        data['prompts']['rating'] = json.load(f)

    output_file = 'data/empty_data.json'
    with open(output_file, 'w') as f:
        json.dump(data, f)

    return


def load_prefix(lang):
    if lang == 'en':
        prefixes = {'interviewer': 'Interviewer',
                    'interviewee': 'Interviewee', 'rating': 'Rating'}
    elif lang == 'ja':
        prefixes = {'interviewer': 'インタビュアー',
                    'interviewee': 'インタビュイー', 'rating': '評価'}
    return prefixes


def load_data(filepath='data/empty_data.json'):
    """
    - prompts: プロンプト
        - interview: インタビュー開始時
        - review: レビュー生成時
        - rating: 数値評価生成時
    - product: 商品情報
        - name: 商品名
        - url: 商品URL
    - history: 対話履歴
    - saveable: セーブできるか
        - セーブできる場合-> 1, できない-> 0
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def save_data(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f)


def extract_rating(input_text, lang='en'):
    if lang == 'en':
        pattern = "Rating: [1-5]"
    elif lang == 'ja':
        pattern = "評価: [1-5]"

    rating_scale = set([str(i) for i in range(1, 6)])
    candidates = re.findall(pattern, input_text)
    if len(candidates):
        rating = candidates[-1][-1]
        return rating
    else:
        rating = 0
        for char in input_text[::-1]:
            if char in rating_scale:
                return char
        return rating


if __name__ == '__main__':
    print()

    ######

    from generate import generate
    import re

    PH_NAME = "[PRODUCT_NAME]"
    PH_REVIEW = "[REVIEW]"
    MODEL = "gpt-4-0613"

    review = "Nutricity is the very worst ever place to order.  I ordered almond butter thinking it came in a glass bottle and when I received it it was packages in plastic.  I returned them and they send me an email saying they did not receive returns.  When I tried to get in touch with them with their 800 number a recording said they only handle returns via email.  I will never ever order from them.  I highly recommend that nobody ever orders from them.  When I ordered I never read that you couldn't return an item.  And then to top it off I could not talk to anyone in their company they handle all via email.  VERY DISSAPOINTING!  DO NOT ORDER ANYTHING FROM THEM."
    product = "Artisana Organics - Almond Butter, no added sugar or oil, Certified organic, RAW, and non-GMO, grown and made in California"

    with open('prompts/generate_rating.json', 'r') as f:
        prompt_rating = json.load(f)

    prompt_rating['system'] = prompt_rating['system'].replace(PH_NAME, product)
    prompt_rating['system'] = prompt_rating['system'].replace(
        PH_REVIEW, review)
    temperature = 0.
    rating_chain, _ = generate(prompt_rating['user'], prompt_rating['system'], [
    ], temperature=temperature, model=MODEL)
    rating = 0  # int(extract_rating(rating_chain, lang='en'))
    print(rating_chain, rating, temperature)
    print()
    print("=====")

    num_trial = 0
    temperature_list = [0.2, 0.4, 0.6]
    while rating == 0:
        temperature = temperature_list[num_trial]
        rating_chain, _ = generate(prompt_rating['user'], prompt_rating['system'], [
        ], temperature=temperature, model=MODEL)
        rating = int(extract_rating(rating_chain, lang='en'))
        print(rating_chain, rating, temperature)
        print(temperature)
        print()
        num_trial += 1
        if num_trial > 2:
            rating = 3

    print(rating)
