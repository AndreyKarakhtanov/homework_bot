import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from contextlib import suppress
from dotenv import load_dotenv
from telebot import TeleBot, apihelper

from exceptions import (
    APIStatusError, EmptyEnvironmentError
)


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Функция проверки доступности необходимых переменных окруженияю.

    Если отсутствует хотя бы одна переменная окружения — продолжать работу
    бота нет смысла.
    """
    ENV_VARS = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    empty_env_vars = []
    for name, var in ENV_VARS.items():
        if not var:
            empty_env_vars.append(name)
    if empty_env_vars:
        for var in empty_env_vars:
            error = (
                f'Отсутствует обязательная переменная окружения: "{var}".'
            )
            logging.critical(error)
        raise EmptyEnvironmentError('Программа принудительно остановлена.')


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram-чат.

    Определяется переменной окружения TELEGRAM_CHAT_ID. Принимает на вход два
    параметра: экземпляркласса TeleBot и строку с текстом сообщения.
    """
    logging.debug('Подготовка отправки сообщения...')
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logging.debug(f'Бот отправил сообщение: "{message}"')


def get_api_answer(timestamp):
    """Функция запроса к единственному эндпоинту API-сервиса.

    В качестве параметра в функцию передаётся временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    logging.debug(f'Подготовка запроса к эндпоинту: {ENDPOINT} ...')
    payload = {'from_date': f'{timestamp}'}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise ConnectionError(
            f'Ошибка доступа к Эндпоинту {ENDPOINT}: {error}'
        )
    if response.status_code != HTTPStatus.OK:
        raise APIStatusError(
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}.'
        )
    logging.debug(f'Получен ответ от эндпоинта: {ENDPOINT}')
    return response.json()


def check_response(response):
    """Функция проверки ответа API на соответствие документации из урока.

    В качестве параметра функция получает ответ API, приведённый к типам
    данных Python.
    """
    logging.debug('Проверки ответа API на соответствие документации...')
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ API не соответствует типу "dict". '
            f'Полученный тип: {type(response)}'
        )
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(
            'В ответе API домашки под ключом "homeworks" '
            'данные не соответствует типу "list". '
            f'Полученный тип: {type(response)}'
        )
    logging.debug('Проверки ответа API заверешена...')
    return homeworks


def parse_status(homework):
    """Функция извлечения статуса из информации о домашней работе.

    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха функция возвращает подготовленную для
    отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_VERDICTS.
    """
    logging.debug('Извлечение статуса из информации о домашней работе...')
    necessary_keys = ['homework_name', 'status']
    missing_keys = []
    for key in necessary_keys:
        if key not in homework.keys():
            missing_keys.append(key)
    if missing_keys:
        keys = '", "'.join(missing_keys)
        raise KeyError(f'Не найдены ключи: "{keys}".')
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Неожиданный статус домашней работы в ответе API: {status}.'
        )
    verdict = HOMEWORK_VERDICTS.get(status)
    logging.debug('Статус домашней работы получен.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_verdict = ''
    last_error = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug('Статус домашней работы не измененился.')
                continue
            message = parse_status(homeworks[0])
            if message != last_verdict:
                send_message(bot, message)
                last_verdict = message
                timestamp = response.get('current_date', timestamp)
        except (apihelper.ApiException, requests.exceptions.RequestException):
            logging.error('Ошибка отправки сообщения.')
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            if error_message != last_error:
                with suppress(
                    apihelper.ApiException,
                    requests.exceptions.RequestException
                ):
                    send_message(bot, error_message)
                    last_error = error_message
            logging.exception(error_message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        handlers=[logging.StreamHandler(sys.stdout)],
        level=logging.DEBUG,
        format=(
            '%(asctime)s [%(levelname)s] '
            '(%(filename)s::%(funcName)s[%(lineno)d]) %(message)s'
        ),
        encoding="UTF-8"
    )
    main()
