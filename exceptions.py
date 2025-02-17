class EmptyEnvironmentError(Exception):
    """Исключение окружения."""

    def __init__(self, name):
        """Конструктор класса."""
        self.name = name

    def __str__(self):
        """Строковое представление исключения."""
        return (
            f'Отсутствует обязательная переменная окружения: \'{self.name}\'.'
            '\nПрограмма принудительно остановлена.'
        )


class APIError(Exception):
    """Исключение окружения."""

    def __init__(self, url, innerException):
        """Конструктор класса."""
        self.url = url
        self.innerException = innerException

    def __str__(self):
        """Строковое представление исключения."""
        return f'Ошибка доступа к Эндпоинту {self.url}: {self.innerException}'


class APIStatusError(Exception):
    """Исключение окружения."""

    def __init__(self, url, status_code):
        """Конструктор класса."""
        self.url = url
        self.status_code = status_code

    def __str__(self):
        """Строковое представление исключения."""
        return (f'Эндпоинт {self.url} недоступен. '
                f'Код ответа API:{self.status_code}')


class FormatError(Exception):
    """Исключение окружения."""

    def __str__(self):
        """Строковое представление исключения."""
        return 'Ошибка формата ответа API'
