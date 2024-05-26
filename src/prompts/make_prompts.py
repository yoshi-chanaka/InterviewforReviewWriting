import json
import re

if __name__ == '__main__':
    """
    指定したpathのプロンプトをjsonファイルに保存 -> それらをloadしてきちんとプロンプトが出来ているか確認
    """
    input_dir = 'text_ja'
    input_path_dict = {
        'interview':    '{}/interview_orig.txt'.format(input_dir),
        'review':       '{}/review_orig.txt'.format(input_dir),
        'rating':       '{}/rating_fewshot_cot.txt'.format(input_dir)
        # 'rating':       '{}/rating_orig.txt'.format(input_dir)
    }

    output_path_dict = {
        'interview':    './begin_interview.json',
        'review':       './generate_review.json',
        'rating':       './generate_rating.json'
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
            json.dump(prompts, f)

        print(f'{task}: {input_path} -> {output_path}')
        with open(output_path, 'r') as f:
            decode_data = json.load(f)
            for k, v in decode_data.items():
                print(k)
                print(v)
        print('-' * 10)
