# app/utils/review_utils.py

import re

# 🔒 BASIC ABUSIVE WORD LIST (can expand later / replace with AI)
ABUSIVE_WORDS = [
    "fuck",
    "shit",
    "asshole",
    "bitch",
    "scam"
]


def should_auto_flag(review_text: str) -> bool:
    """
    Returns True if review should be auto-flagged.
    Conditions:
    - abusive words
    - URLs
    - phone numbers
    """

    if not review_text:
        return False

    text = review_text.lower()

    # 🚫 Abuse check
    if any(word in text for word in ABUSIVE_WORDS):
        return True

    # 🔗 URL check
    if re.search(r"http[s]?://|www\.", text):
        return True

    # 📞 Phone number check (India basic)
    if re.search(r"\b\d{10}\b", text):
        return True

    return False
