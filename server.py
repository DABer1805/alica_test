from flask import Flask, request, jsonify
import logging
import json
from translate import Translator

app = Flask(__name__)

translator = Translator(from_lang="russian", to_lang="English")

# https://disk.yandex.ru/i/E6wKTr_xVLRGdA - демонстрация в Яндекс диалогах

# Добавляем логирование в файл.
# Чтобы найти файл, перейдите на pythonwhere в раздел files,
# он лежит в корневой папке
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        res['response']['buttons'] = [
            {
                'title': 'Помощь',
                'hide': True
            }
        ]

        sessionStorage[user_id] = {
            'first_name': None,  # здесь будет храниться имя
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response'][
                'text'] = 'Не расслышала имя. Повтори, пожалуйста!'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, ' \
                                      f'{first_name.title()}. Я Алиса. ' \
                                      f'Я могу показать город или ' \
                                      f'сказать расстояние между городами!'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
    else:
        first_name = sessionStorage[user_id]['first_name']
        word = get_word(req)
        if word == '/help' or word == '/error':
            text = f'{first_name.title()}, тебе нужно назвать фразу вида:  ' \
                   f'переведи *слово* и я тебе напишу его перевод на ' \
                   f'английском'
            res['response']['text'] = text
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
        elif word == '/too_few_words':
            res['response']['text'] = f'{first_name.title()}, тебе надо ' \
                                      f'еще назвать какое слово ' \
                                      f'нужно перевести'
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]
        else:
            res['response']['text'] = word
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то
            # возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


def get_word(req):
    tokens = req['request']['nlu']['tokens']
    if 'помощь' in tokens:
        return '/help'
    elif 'переведи' in tokens or 'переведите' in tokens:
        if len(tokens) > 1:
            text_rus = req['request']['nlu']['tokens'][-1]
            text_eng = translator.translate(text_rus)
            return text_eng
        return '/too_few_words'
    return '/error'


if __name__ == '__main__':
    app.run()
