"""
Text normalization for Russian search queries.
Handles lemmatization, stopwords, synonyms, and characteristic extraction.
"""

import re
from typing import List, Dict


class TextNormalizer:
    PRIORITY_CHARS = {
        'вид товаров', 'вид продукции', 'цвет', 'материал',
        'длина', 'вес', 'ширина', 'назначение', 'высота',
        'тип', 'размер', 'диаметр', 'объем', 'количество в упаковке'
    }

    DEFAULT_STOPWORDS = {
        'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со',
        'как', 'а', 'то', 'все', 'она', 'так', 'его', 'но', 'да',
        'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только',
        'ее', 'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет',
        'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг',
        'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него',
        'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там',
        'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут',
        'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их',
        'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'человек',
        'чего', 'раз', 'тоже', 'себе', 'под', 'жизнь', 'будет',
        'тогда', 'кто', 'этот', 'говорил', 'того', 'потому', 'этого',
        'какой', 'совсем', 'ним', 'здесь', 'этом', 'один', 'почти',
        'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда',
        'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец',
        'два', 'об', 'другой', 'хоть', 'после', 'над', 'больше',
        'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них',
        'какая', 'много', 'разве', 'три', 'эту', 'моя', 'впрочем',
        'хорошо', 'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть',
        'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'конечно',
        'всю', 'между'
    }

    DEFAULT_SYNONYMS = {
        'пластик': ['пластмасса', 'полимер', 'пластиковый', 'пластмассовый'],
        'сталь': ['металл', 'металлический', 'стальной'],
        'белый': ['бел', 'белого', 'белые', 'белое'],
        'черный': ['чёрный', 'чер', 'чёрного', 'черные', 'чёрное'],
        'товар': ['продукция', 'изделие', 'предмет'],
        'медицинский': ['мед', 'медизделие', 'медикаменты'],
        'строительный': ['строй', 'ремонт', 'строительство'],
        'упаковка': ['короб', 'пакет', 'контейнер', 'тара'],
        'мешок': ['пакет', 'сумка'],
        'пакет': ['мешок', 'упаковка'],
        'набор': ['комплект', 'коллекция'],
        'раствор': ['жидкость', 'суспензия', 'эмульсия'],
        'таблетки': ['таб', 'таблеточный'],
        'инструмент': ['инструментальный', 'орудие'],
        'оборудование': ['аппарат', 'устройство', 'машина'],
        'устройство': ['прибор', 'аппарат', 'оборудование'],
        'материал': ['сырье', 'вещество', 'ткань'],
        'ткань': ['материал', 'текстиль', 'полотно'],
        'бумага': ['бумажный', 'лист'],
        'стекло': ['стеклянный', 'стек'],
        'резина': ['резиновый', 'каучук'],
        'дерево': ['деревянный', 'древесина'],
        'кожа': ['кожаный', 'кож'],
        'металл': ['металлический', 'железный', 'стальной', 'алюминиевый'],
        'цвет': ['окраска', 'оттенок', 'тон'],
        'размер': ['габарит', 'величина', 'параметр'],
        'вес': ['масса', 'тяжелый', 'легкий'],
        'длина': ['протяженность', 'размер'],
        'ширина': ['размер'],
        'высота': ['размер', 'высотный'],
        'объем': ['вместимость', 'литраж'],
        'количество': ['число', 'штук', 'единиц'],
    }

    def __init__(self):
        self.stopwords = self.DEFAULT_STOPWORDS.copy()
        self.synonyms = self.DEFAULT_SYNONYMS.copy()
        self._morph = None

    @property
    def morph(self):
        if self._morph is None:
            try:
                import pymorphy3
                self._morph = pymorphy3.MorphAnalyzer()
            except ImportError:
                self._morph = None
        return self._morph

    def normalize(self, text: str) -> str:
        if not text:
            return ''
        text = text.lower()
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\s\-\.\,]', ' ', text)
        tokens = text.split()
        lemmatized = []
        if self.morph:
            for token in tokens:
                if token and token not in self.stopwords:
                    parsed = self.morph.parse(token)[0]
                    lemmatized.append(parsed.normal_form)
        else:
            lemmatized = [t for t in tokens if t and t not in self.stopwords]
        return ' '.join(lemmatized)

    def expand_synonyms(self, text: str) -> List[str]:
        terms = text.lower().split()
        expanded = [text]
        for term in terms:
            if term in self.synonyms:
                for synonym in self.synonyms[term]:
                    new_query = text.lower().replace(term, synonym)
                    if new_query not in expanded:
                        expanded.append(new_query)
        return expanded

    def extract_characteristics(self, text: str) -> Dict:
        result = {'category': None, 'material': None, 'color': None, 'dimensions': {}, 'priority_terms': []}
        text_lower = text.lower()
        for mat in ['пластик', 'сталь', 'металл', 'дерево', 'резина', 'стекло', 'полимер', 'пластмасса', 'бумага', 'ткань', 'кожа']:
            if mat in text_lower:
                result['material'] = mat
                break
        for color in ['белый', 'черный', 'красный', 'синий', 'зеленый', 'желтый', 'серый', 'коричневый', 'прозрачный']:
            if color in text_lower:
                result['color'] = color
                break
        result['dimensions'] = re.findall(r'(\d+(?:\.\d+)?)\s*(мм|см|м|кг|г|л|мл)?', text_lower)
        result['priority_terms'] = [t for t in self.PRIORITY_CHARS if t in text_lower]
        return result

    def normalize_for_fts(self, text: str) -> str:
        if not text:
            return ''
        text = text.lower()
        text = re.sub(r'[^\w\s\-\.\,\/]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
