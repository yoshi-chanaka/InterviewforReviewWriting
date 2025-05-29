from flask import Flask, render_template, request, jsonify
from modules.generate import generate
from modules import utils, html_builder
from settings.config import *

import json
import time
from datetime import datetime
import os
import sys

prefixes = utils.load_prefix(lang=LANG)
app = Flask(__name__)

if not(os.path.isdir('data')):
    os.mkdir('data')
    os.mkdir('data/logs')
utils.initialize()

with open('resources/questionnaire/questions.txt', 'r', encoding='utf-8') as f:
    QUESTIONS = f.readlines()
    QUESTIONS = [q.strip() + CONTINUE_TOKEN for q in QUESTIONS[:-1]] + [QUESTIONS[-1].strip() + END_TOKEN]
    QUESTIONS = [prefixes['interviewer'] + ': ' + q for q in QUESTIONS]

with open('resources/guidance/guidance_{}.txt'.format(LANG), 'r', encoding='utf-8') as f:
    GUIDANCE = f.readlines()



@app.route("/", methods=["GET"])
def get():
    return render_template("index.html", time=datetime.now().strftime('%H:%M'))


@app.route("/add_user_utterance", methods=["POST"])
def add_user_utterance():
    """
    worker(interviewee)の発話を反映
    """
    text = request.form.get('text')
    text = text.strip().replace('\n', '<br>')
    if len(text):
        response = html_builder.worker_bubble(text)
        return jsonify(element=response)



@app.route("/post_guidance", methods=["POST"])
def post_guidance():
    """
    インタビューの準備: 商品情報の入力
    """
    gdn_number = int(request.form.get('q_number'))
    response = ''

    memory = utils.load_data()
    memory['first_post_time'] = str(datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f'))
    memory['id'] = "this_is_demo"
    memory['prompts']['interview']['system'] = memory['prompts']['interview']['system'].replace('[MIN_QUESTION]', str(MIN_QUESTIONS))
    memory['prompts']['interview']['system'] = memory['prompts']['interview']['system'].replace('[MAX_QUESTION]', str(MAX_QUESTIONS))

    memory['product']['url'] = ""
    product_name = request.form.get('text').strip()
    memory['product']['name'] = product_name
    memory['prompts']['interview']['user'] = memory['prompts']['interview']['user'].replace(PH_NAME, product_name)
    memory['prompts']['review']['system'] = memory['prompts']['review']['system'].replace(PH_NAME, product_name)
    memory['prompts']['rating']['system'] = memory['prompts']['rating']['system'].replace(PH_NAME, product_name)
    worker_id = '{}_{}'.format(memory['first_post_time'], memory['id'])

    time.sleep(1)
    text = GUIDANCE[gdn_number].strip().replace('[NL]', '</p><p>')
    if '[IMAGE]' in text:
        img_filename, text = text.split('[IMAGE]', 1)
        component = html_builder.guide_bubble(input_text=text, step=False, sended_time=False) + '\n' + \
                    html_builder.guide_bubble(image_path=img_filename, sended_time=True)
    elif gdn_number >= int(request.form.get('num_guidance')) - 1:
        component = html_builder.guide_bubble(input_text=text, sended_time=True)
    else:
        component = html_builder.guide_bubble(input_text=text, step=False, sended_time=False)
    response += component
    utils.cleanup_logs()
    utils.save_data('data/logs/{}.json'.format(worker_id), memory)

    return jsonify(element=response, worker_id=worker_id)


@app.route("/post_question", methods=["POST"])
def post_question():
    """
    interviewerの発話生成・反映
    """
    ques_number = int(request.form.get('q_number'))
    worker_id = request.form.get('worker_id')
    memory_file_path = 'data/logs/{}.json'.format(worker_id)
    if not os.path.isfile(memory_file_path):
        # Send TIMEOUT message
        response = html_builder.guide_bubble("タイムアウトしました．もう一度最初からやり直してください．")
        return jsonify(element=response, end_sign=False)
    memory = utils.load_data(memory_file_path)

    history = memory['history']

    if BOT_TYPE == 'rule-based':
        time.sleep(1)
        next_response = QUESTIONS[ques_number].strip()
    else:
        next_response = False


    if ques_number:
        utterance = request.form.get('text').strip()
        utterance = '{}: '.format(prefixes['interviewee']) + utterance

        response, history = generate(
            utterance = utterance,
            settings_text = memory['prompts']['interview']['system'],
            dialogue_history = history,
            temperature=TEMPERATURE_INTERVIEW,
            next_response=next_response,
            model=MODEL)
    else: # 最初の発話
        utterance = memory['prompts']['interview']['user']

        response, history = generate(
            utterance = memory['prompts']['interview']['user'],
            settings_text = memory['prompts']['interview']['system'],
            dialogue_history = [],
            temperature=TEMPERATURE_INTERVIEW,
            next_response=next_response,
            model=MODEL
        )

    if int(ques_number) >= MAX_QUESTIONS or END_TOKEN in response:
        end_sign = True
        history = history[:-1]
        response = "対話はこれで終了です！AIがあなたのお話をもとにレビューを書いています．少々お待ちください..."
        response  = html_builder.guide_bubble(response)
    else:
        end_sign = False
        response = response.split(CONTINUE_TOKEN)[0].strip()
        try:
            response = response.replace('\n', '<br>').split("{}: ".format(prefixes['interviewer']))[1].strip()
        except:
            pass
        response = html_builder.system_bubble(response)
    memory['history'] = history

    utils.save_data('data/logs/{}.json'.format(worker_id), memory)
    return jsonify(element=response, end_sign=end_sign)


@app.route("/terminate_interview", methods=["POST"])
def terminate_interview():

    worker_id = request.form.get('worker_id')
    memory_file_path = 'data/logs/{}.json'.format(worker_id)
    memory = utils.load_data(memory_file_path)

    # プロンプトへの対話履歴の埋め込み
    dialogue_history = []
    len_prefix_er, len_prefix_ee = len(prefixes['interviewer']) + 2, len(prefixes['interviewee']) + 2
    for msg in memory['history']:
        if (msg['role'] in ['user', 'assistant']) and (msg['content'][:len_prefix_er] == '{}: '.format(prefixes['interviewer']) or msg['content'][:len_prefix_ee] == '{}: '.format(prefixes['interviewee'])):
            utt = msg['content'].replace(CONTINUE_TOKEN, '')
            utt = utt.replace(END_TOKEN, '')
            dialogue_history.append(utt.strip())
    prompt_review, prompt_rating = memory['prompts']['review'], memory['prompts']['rating']
    prompt_review['system'] = prompt_review['system'].replace(PH_DIALOGUE, '\n'.join(dialogue_history))
    memory['prompts']['review'], memory['prompts']['rating'] = prompt_review, prompt_rating

    review, _ = generate(prompt_review['user'], prompt_review['system'], [], temperature=TEMPERATURE_REVIEW, model=MODEL)
    review = review.strip()
    prompt_rating['system'] = prompt_rating['system'].replace(PH_REVIEW, review)

    rating_chain, _ = generate(prompt_rating['user'], prompt_rating['system'], [], temperature=TEMPERATURE_RATING, model=MODEL)
    rating = int(utils.extract_rating(rating_chain, lang=LANG))
    
    # rating == 0の場合何度か試す
    num_trial = 0
    temperature_list = [0.2, 0.4, 0.6]
    while rating == 0:
        current_temperature = temperature_list[num_trial]
        rating_chain, _ = generate(prompt_rating['user'], prompt_rating['system'], [], temperature=current_temperature, model=MODEL)
        rating = int(utils.extract_rating(rating_chain, lang=LANG))
        num_trial += 1
        if num_trial > 2:
            rating = 3


    finish_text = "レビューができました！以下は，あなたのお話をもとにAIが書いた商品レビューです．"
    rating_text = "★" * rating + "☆" * (5 - rating)
    review_text = "<br>{}".format(review.replace('\n', '<br>'))
    final_response = html_builder.guide_bubble(finish_text) + '\n' + \
                    html_builder.review_bubble(review=review_text, rating=rating_text)

    memory['review'] = review
    memory['rating_chain'] = rating_chain
    memory['rating'] = rating

    memory['settings'] = {
        'max_questions': MAX_QUESTIONS,
        'min_questions': MIN_QUESTIONS,
        'temperature_interview': TEMPERATURE_INTERVIEW,
        'temperature_result': TEMPERATURE_REVIEW
    }
    # remove the memory file
    if os.path.isfile(memory_file_path):
        os.remove(memory_file_path)

    """
    保存
    - log, prompt -> txt
    - result -> csv
    """
    saveable_flg = memory['saveable']
    if saveable_flg and SAVE_COMPLETED:
        finish_time = str(datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f'))

        savefile_name = 'data/completed/output-{}-{}.json'.format(finish_time, str(worker_id))
        settings_data = {
            'prompts': memory['prompts'],
            'product': {'title': str(memory['product']['name']), 'url': str(memory['product']['url'])},
            'max_questions': MAX_QUESTIONS,
            'min_questions': MIN_QUESTIONS,
            'temperature_interview': TEMPERATURE_INTERVIEW,
            'temperature_review': TEMPERATURE_REVIEW,
            'temperature_rating': TEMPERATURE_RATING,
            'language': LANG,
            'bot': BOT_TYPE,
            'model': MODEL,
            'worker_id': memory['id'],
            'time_start': memory['first_post_time'],
            'time_finish': finish_time,
            'review': review,
            'rating-cot': rating_chain,
            'rating': rating,
            'history': dialogue_history
        }
        with open(savefile_name, 'w') as f:
            json.dump(settings_data, f)

        saveable_flg = 0
        memory['saveable'] = saveable_flg
    
    return jsonify(element=final_response, review=review)


