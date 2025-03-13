MTG Project Documentation

Версия: 1.1
Автор: MrVladikk
Дата: Март 2025

1. Обзор проекта

MTG Project – это веб-приложение, разработанное на основе Django для управления коллекцией карт Magic: The Gathering. Приложение предоставляет следующие возможности:

Импорт данных о карточках из CSV/Excel-файлов.
Скачивание изображений карт с API Scryfall.
Обновление ссылок на изображения в базе данных.
Управление колодами (добавление, редактирование, удаление) через административную панель.
Управление проектом посредством Django management commands, что позволяет запускать задачи (импорт, обновление, добавление колод) через manage.py. 2. Стек технологий

Python 3.12
Django 4.2 – основной веб-фреймворк
SQLite – база данных (по умолчанию; для продакшена рекомендуется PostgreSQL)
Requests – для выполнения HTTP-запросов
Pandas – для обработки CSV/Excel файлов
tqdm – для отображения прогресс-бара при загрузке изображений
Gunicorn – для запуска в продакшене
psycopg2-binary – для работы с PostgreSQL (если потребуется)
django-environ – для управления переменными окружения (рекомендуется) 3. Структура проекта

mtg_project/ # Корневая директория проекта
├── db.sqlite3 # Файл базы данных (SQLite)
├── manage.py # Основная точка входа Django
├── requirements.txt # Файл зависимостей проекта
├── mtg_app/ # Приложение Django для работы с MTG
│ ├── admin.py # Настройка административной панели
│ ├── apps.py # Конфигурация приложения
│ ├── models.py # Определение моделей (Card, Set, Deck)
│ ├── management/ # Django management commands
│ │ ├── **init**.py
│ │ └── commands/
│ │ ├── **init**.py
│ │ ├── download_images.py # Команда для скачивания изображений
│ │ ├── update_image_urls.py # Команда для обновления ссылок на изображения
│ │ └── add_deck.py # Команда для импорта колод из текстового файла
│ ├── parser_mtg/ # Папка с парсерами (если используются отдельно)
│ │ └── my_cards.csv # CSV-файл с данными карточек
│ └── static/
│ └── mtg_app/
│ └── images/
│ └── cards # Папка для хранения скачанных изображений
└── mtg_project/ # Директория с настройками проекта
├── **init**.py
├── asgi.py
├── settings.py # Основные настройки Django
├── urls.py # URL-конфигурация проекта
└── wsgi.py 4. Установка и настройка

Клонирование репозитория:

git clone https://github.com/MrVladikk/mtg_project.git
cd mtg_project
Создание виртуального окружения и установка зависимостей:
python -m venv venv

# Linux/macOS:

source venv/bin/activate

# Windows:

venv\Scripts\activate
pip install -r requirements.txt
Применение миграций и запуск сервера:

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
Откройте браузер по адресу: http://127.0.0.1:8000.

5. Модели и администрирование

Основные модели (определены в mtg_app/models.py):

Set – хранит информацию о наборах карт.
Card – содержит данные о каждой карте (название, сет, номер, редкость, цена, ссылка на изображение и т.д.).
Deck – позволяет создавать колоды, объединяющие множество карт (связь ManyToMany).
Административная панель:

Модели зарегистрированы в mtg_app/admin.py.
Создайте суперпользователя:
python manage.py createsuperuser
Перейдите по адресу: http://127.0.0.1:8000/admin. 6. Management Commands

В проекте реализованы пользовательские команды для автоматизации задач:

download_images:
Запускается командой:
python manage.py download_images
Считывает данные из CSV-файла (my_cards.csv), получает изображения по Scryfall ID и сохраняет их в папку mtg_app/static/mtg_app/images/cards.

update_image_urls:
Запускается командой:
python manage.py update_image_urls
Команда проходит по всем объектам Card, формирует имя файла на основе названия карты и номера коллекции, проверяет наличие файла и обновляет поле image_url в базе данных.

add_deck:
Запускается командой:
python manage.py add_deck --deck_file "path/to/deck_file.txt" --deck_name "Название колоды" --deck_description "Описание колоды"
Команда читает текстовый файл с описанием колоды, ищет соответствующие объекты Card в базе данных и добавляет их в созданную колоду Deck.

7. Фронтенд и стили

Проект использует кастомные CSS-стили, определённые в mtg_app/static/mtg_app/styles.css, для оформления:

Общего оформления (фон, шрифты, цвета).
Заголовка, навигации и геро-секции.
Карточек карт и страниц с деталями.
Футера, который прижат к низу экрана с помощью Flexbox.
Пример обновлённого CSS для фиксации футера:

html, body {
margin: 0;
padding: 0;
height: 100%;
}

.wrapper {
display: flex;
flex-direction: column;
min-height: 100vh;
}

.content {
flex: 1;
}

footer {
background: #2e2b25;
padding: 20px;
text-align: center;
color: #d4c8a2;
font-size: 1rem;
border-top: 3px solid #c8a24a;
}
Важно: Убедитесь, что базовый HTML-шаблон содержит контейнер <div class="wrapper"> с элементами header, main (с классом .content) и footer.

8. Развертывание

Настройки для продакшена:

Перейдите на PostgreSQL вместо SQLite.
В файле mtg*project/settings.py установите:
DEBUG = False
ALLOWED_HOSTS = ['ваш*домен', 'IP*адрес*сервера']
Выполните сбор статических файлов:
python manage.py collectstatic
Используйте Gunicorn и Nginx для продакшена.

9. Заключение

MTG Project – это мощное Django-приложение для коллекционеров карт Magic: The Gathering. Проект включает:

Импорт данных и загрузку изображений через management commands.
Удобное управление коллекцией через административную панель.
Современный фронтенд с кастомными CSS-стилями, включая прижатый к низу футер.
Рекомендации по улучшению кода, тестированию и развертыванию.
