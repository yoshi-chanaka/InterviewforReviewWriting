# if MODEL = "rule-based", then use rule-based generation 
MODEL = "gpt-4.1"
MAX_QUESTIONS = 5
MIN_QUESTIONS = 3

TEMPERATURE_INTERVIEW = 0.5
TEMPERATURE_RATING = 0.0
TEMPERATURE_REVIEW = 0.0
LANG = 'ja'

if MODEL == "rule-based":
    BOT_TYPE = "rule-based"
else:
    BOT_TYPE = "gpt"

# special tokens for interview
CONTINUE_TOKEN = "[Wait_for_Response]"
END_TOKEN = "[End_of_Interview]"

# placeholders for prompts
PH_DIALOGUE = "[DIALOGUE]"
PH_NAME = "[PRODUCT_NAME]"
PH_REVIEW = "[REVIEW]"

SAVE_COMPLETED = False  # whether to save the completed interview or not

# clean up log files
TIMEOUT_SECONDS = 60 # 5 * 60 * 60
MAX_LOG_FILES = 2
LOG_DIR = "./data/logs/"

