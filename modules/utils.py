import json
import re
import os
from glob import glob
import fcntl
from settings.config import TIMEOUT_SECONDS, MAX_LOG_FILES, LOG_DIR
from datetime import datetime

def make_prompts():
    """
    指定したpathのプロンプトをjsonファイルに保存 -> それらをloadしてきちんとプロンプトが出来ているか確認
    """
    input_dir = 'text_ja'
    input_path_dict = {
        'interview':    "resources/prompts/{}/interview_orig.txt".format(input_dir),
        'review':       "resources/prompts/{}/review_orig.txt".format(input_dir),
        'rating':       "resources/prompts/{}/rating_fewshot_cot.txt".format(input_dir)
    }

    output_path_dict = {
        'interview':    './resources/prompts/begin_interview.json',
        'review':       './resources/prompts/generate_review.json',
        'rating':       './resources/prompts/generate_rating.json'
    }

    for task, input_path in input_path_dict.items():
        with open(input_path, 'r') as f:
            text = ''.join(f.readlines())
        prompts = {
            'system': re.findall(r'<system>(.*)</system>', text, flags=re.MULTILINE | re.DOTALL)[0],
            'user': re.findall(r'<user>(.*)</user>', text, flags=re.MULTILINE | re.DOTALL)[0]
        }

        output_path = output_path_dict[task]
        with open(output_path, 'w') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=4)

        # print(f'{task}: {input_path} -> {output_path}')
        # with open(output_path, 'r') as f:
        #     decode_data = json.load(f)
        #     for k, v in decode_data.items():
        #         print(k)
        #         print(v)
        # print('-' * 10)
    return


def initialize():
    make_prompts()
    data = {
        'prompts': {},
        'product': {},
        'history': [],
        'saveable': 1,
    }
    with open('resources/prompts/begin_interview.json', 'r') as f:
        data['prompts']['interview'] = json.load(f)
    with open('resources/prompts/generate_review.json', 'r') as f:
        data['prompts']['review'] = json.load(f)
    with open('resources/prompts/generate_rating.json', 'r') as f:
        data['prompts']['rating'] = json.load(f)

    output_file = 'resources/empty_data.json'
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


def load_data(filepath='resources/empty_data.json'):
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
        json.dump(data, f, ensure_ascii=False, indent=4)
    return


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


LOCK_FILE = os.path.join(LOG_DIR, ".cleanup_lock")
CLEANUP_LOG_FILE = "./data/cleanup_log.txt"

def cleanup_logs():
    current_time = datetime.now().timestamp()
    stored_file_list = glob(LOG_DIR + "*.json")
    if len(stored_file_list) > MAX_LOG_FILES:
        # Sort files by modification time
        stored_file_list.sort(key=lambda x: os.path.getmtime(x))
        
        # global lock
        with open(LOCK_FILE, "a+") as global_lock_fp:
            try:
                fcntl.flock(global_lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return

            try:
                with open(CLEANUP_LOG_FILE, "a",  encoding="utf-8") as cleanup_fp:
                    # 各ファイルを個別にロック＆削除
                    for file_path in stored_file_list:
                        file_mtime = os.path.getmtime(file_path)

                        if current_time - file_mtime < TIMEOUT_SECONDS:
                            break
                        try:
                            with open(file_path, "r+") as fp:
                                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                                os.remove(file_path)
                                cleanup_fp.write(f"Deleted: {file_path} at {datetime.now().isoformat()}\n")
                        except BlockingIOError:
                            continue
                        except FileNotFoundError:
                            continue
            finally:
                # グローバルロック解除
                fcntl.flock(global_lock_fp, fcntl.LOCK_UN)
    return


