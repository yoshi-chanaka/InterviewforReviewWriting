from datetime import datetime

def worker_bubble(input_text):
    code = '<div class="msg msg-right">\n \
                <div class="msg-contents contents-right">\n \
                    <div class="msg-text">{}</div>\n \
                </div>\n \
                <div class="sended-time">{}</div>\n \
            </div>\n'.format(input_text, datetime.now().strftime('%H:%M'))
    return code

def system_bubble(input_text):
    code = '<div class="msg msg-left">\n \
                <div class="msg-contents contents-left">\n \
                    <div class="msg-text">{}</div>\n \
                </div>\n \
                <div class="sended-time">{}</div>\n \
            </div>\n'.format(input_text, datetime.now().strftime('%H:%M'))
    return code

def guide_bubble(input_text=False, step=False, image_path=False, sended_time=True):
    code = '<div class="msg msg-guide">\n [PH]</div>'
    if image_path:
        code = code.replace('[PH]', '<img class="guide_image" src="{}" width="300"/>\n [PH]'.format(image_path))
    if input_text:
        code = code.replace('[PH]', '<div class="msg-contents contents-guide">\n <div class="msg-text">[PH_TXT]</div>\n </div>\n [PH]')
        if step:
            code = code.replace('[PH_TXT]', '<p><strong>Step {}: </strong></p> [PH_TXT]'.format(step))
        code = code.replace('[PH_TXT]', '<p>{}</p> [PH_TXT]'.format(input_text))
    code = code.replace('[PH_TXT]', '')
    if sended_time:
        code = code.replace('[PH]', '<div class="sended-time">{}</div>\n [PH]'.format(datetime.now().strftime('%H:%M')))
    return code.replace('[PH]', '')

def review_bubble(review, rating):
    code = '<div class="msg msg-center">\n \
                <div class="rev-contents contents-center">\n \
                    <div class="review-text", style="font-size: 30px; color:#ff8c00">{}</div>\n \
                    <div class="review-text">{}</div>\n \
                </div>\n \
            </div>'.format(rating, review)
    return code

def concluding_bubble(messages, url=False):
    code = guide_bubble(input_text='[TMP]', sended_time=True)
    code = code.replace('<p>[TMP]</p>', '[PH]')
    for msg in messages:
        code = code.replace('[PH]', '<p>{}</p> [PH]'.format(msg))
    if url:
        code = code.replace('[PH]', '<p><a href="{}" target="_blank">{}</a></p> '.format(url, url))
    return code.replace('[PH]', '')
