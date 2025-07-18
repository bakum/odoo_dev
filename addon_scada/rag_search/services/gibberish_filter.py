import re
from langdetect import detect, LangDetectException


class GibberishFilter:
    @staticmethod
    def is_gibberish(text):
        if not text or len(text.strip()) < 10:
            return True  # слишком короткий текст

        # Удалим все небуквенные символы и приведём к нижнему регистру
        clean = re.sub(r'[^а-яА-Яa-zA-Z ]+', '', text).lower()

        # Проверка на длинные цепочки согласных (русский/английский)
        if re.search(r'[бвгджзйклмнпрстфхцчшщ]{4,}', clean):
            return True
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', clean):
            return True

        # Проверка уникальности символов
        if len(set(clean)) < 5:
            return True

        try:
            lang = detect(text)
            if lang not in ['ru', 'en', 'uk', 'be', 'pl', 'de']:
                return True
        except LangDetectException:
            return True

        return False
