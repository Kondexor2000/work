import re
from langdetect import detect
import logging

logger = logging.getLogger(__name__)


def is_valid_text(text: str) -> bool:
    try:
        if not text:
            return False

        text = text.strip()

        if not text or not text[0].isalpha():
            return False

        lang = detect(text)

        if lang != "pl":
            return False

        latin_like = len(re.findall(r'\b\w+(us|um|ae|is)\b', text.lower()))

        return latin_like < 3

    except Exception:
        logger.exception("Language detection failed")
        return False