# Homework bot

## Описание проекта

Homework bot - обращается к API сервиса Практикум Домашка и узнаёт статус вашей работы: взята ли она в ревью, проверена ли, а если проверена — принял её ревьюер или вернул на доработку.
- раз в 10 минут опрашивает API сервиса Практикум Домашка и проверяет статус отправленной на ревью домашней работы;
- при обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram;
- логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

## Как запустить "Homework bot":

Клонировать репозиторий и перейти в него в командной строке:

```
git clone 
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать в директории проекта файл .env с переменными окружения в соответствии с .env.example.

Запустить бота:

```
python homework.py
```

# Контакты 

Email: [Андрей Карахтанов](super.andrew100@yandex.com) 

GitHub: [AndreyKarakhtanov](https://github.com/AndreyKarakhtanov)