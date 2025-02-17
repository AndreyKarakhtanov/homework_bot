import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from exceptions import (
    APIError, APIStatusError, EmptyEnvironmentError, FormatError
)
from telebot import TeleBot

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
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding="UTF-8"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


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
    for name, var in ENV_VARS.items():
        if not var:
            error = (
                f'Отсутствует обязательная переменная окружения: \'{name}\'.'
                '\nПрограмма принудительно остановлена.'
            )
            logging.critical(error)
            raise ValueError(error)
                

def send_message(bot, message):
    """Функция отправляет сообщение в Telegram-чат.

    Определяется переменной окружения TELEGRAM_CHAT_ID. Принимает на вход два
    параметра: экземпляркласса TeleBot и строку с текстом сообщения.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Бот отправил сообщение \'{message}\'')
    except Exception:
        logging.error('Ошибка отправки сообщения.')


def get_api_answer(timestamp):
    """Функция запроса к единственному эндпоинту API-сервиса.

    В качестве параметра в функцию передаётся временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    payload = {'from_date': f'{timestamp}'}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    try:
        response = requests.get(ENDPOINT, headers=headers, params=payload)
    except Exception as error:
        raise APIError(ENDPOINT, error)
    if response.status_code != HTTPStatus.OK:
        raise APIStatusError(ENDPOINT, response.status_code)
    try:
        return response.json()
    except Exception:
        raise FormatError


def check_response(response):
    """Функция проверки ответа API на соответствие документации из урока.

    В качестве параметра функция получает ответ API, приведённый к типам
    данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API не соответствует типу \'dict\'')
    try:
        homeworks = response.get('homeworks')
        if not isinstance(homeworks, list):
            raise TypeError('В ответе API домашки под ключом \'homeworks\''
                            ' данные приходят не в виде списка')
    except KeyError:
        raise KeyError('Ключ \'homework\' не найден')
    try:
        homework = homeworks[0]
    except IndexError:
        raise IndexError('Список домашних заданий пустой')
    return homework


def parse_status(homework):
    """Функция извлечения из информации статусе домашней работы.

    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха функция возвращает подготовленную для
    отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_VERDICTS.
    """
    if 'homework_name' not in homework.keys():
        raise KeyError('Ключ \'homework_name\' не найден')
    homework_name = homework['homework_name']
    if 'status' not in homework.keys():
        raise KeyError('Ключ \'status\' не найден')
    status = homework['status']
    if homework.get('status') not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Неожиданный статус домашней работы в ответе API: {status}'
        )
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()   
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    VERDICT = ''
    LAST_ERROR = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message != VERDICT:
                timestamp = response.get('current_date')
                send_message(bot, message)
                VERDICT = message
            else:
                logging.debug('Статус домашней работы не измененился')
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            if error_message != LAST_ERROR:
                send_message(bot, error_message)
                LAST_ERROR = error_message
            logging.error(error_message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
