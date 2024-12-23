# Описание проекта:
![main workflow](https://github.com/EkaterinaRez/foodgram/actions/workflows/main.yml/badge.svg)

Проект включает в себя автоматическое развертывание на удаленном сервере с помощью docker compose.
В проекте используется github actions для автоматических тестов, билда контейнеров и их деплоя. После успешного деплоя отправляется сообщение в телеграм.

Foodgram создан для публикации различных рецептов. 
Сервис предоставляет возможность публиковать рецепты, подписываться на рецепты других пользователей, добавить рецепты в список избранного, скачивать в формате .txt список продуктов, необходимых для приготовления выбранных рецептов.

## Как запустить проект локально:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/EkaterinaRez/foodgtam.git
```

```
cd foodram
```

Cоздать и активировать виртуальное окружение:

```
python -m .venv venv
```

```
source .venv/scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```

Запустить проект:

```
python manage.py runserver
```

## Разворачивание проекта с помощью Docker
Проект поддерживает развертывание с использованием Docker для облегчения процесса управления зависимостями и изолирования среды выполнения. Следуйте приведенным ниже инструкциям для развертывания проекта с использованием Docker Compose.

### Предварительные требования
Убедитесь, что у вас установлены Docker и Docker Compose.


1. Клонируйте репозиторий и перейдите в его директорию:

```
git clone https://github.com/EkaterinaRez/foodgram.git
cd foodgram
```

2. Создайте файл .env в корне проекта с необходимыми переменными окружения.

3. Cоздайте образы приложения и необходимые volumes:
Используемые образы:
- foodgram_backend
- foodgram_frontend
- foodgram_gateway

Необходимые volumes:
- pg_data — для хранения данных PostgreSQL.
- static — для статических файлов.
- media — для медиа файлов пользователей.

4. Скопируйте на сервер docker-compose.production.yml

5. В директории с docker-compose.production.yml выполните команду
```
docker-compose -f docker-compose.production.yml up --build
```
6. Настройте общий nginx для работы с приложением по ssl.
Выполните команду:
```
 sudo nano /etc/nginx/sites-enabled/default 
```
и пропишите адресацию для своегj приложения:
```
# Пример

server {
    server_name 89.169.173.181 foodgram.ddns.net;
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8000;
    }
}
```
7. Настройте шифрование с помощью certbot, последовательно выполняя команды:
```
sudo apt install snapd
sudo certbot --nginx 
sudo systemctl reload nginx

```

### Интеграция с GitHub Actions
Проект настроен для использования GitHub Actions для автоматизированного тестирования, сборки и деплоя. Интеграция позволяет автоматически деплоить изменения на сервер после успешного прохождения всех тестов в CI/CD пайплайне. При успешном деплое отправляется уведомление в Telegram.


## Заполнение .env
В секретах используются следующие атрибуты (значения указаны для примера):
- POSTGRES_DB=django
- POSTGRES_USER=user
- POSTGRES_PASSWORD=password
- DB_NAME=food
- DB_HOST=db
- DB_PORT=5432
- SECRET_KEY='django-insecure-n&$zd1t1dd6y'
- DEBUG='True'
- ALLOWED_HOSTS="foodkatya.ddns.net,localhost,127.0.0.1"


## Адрес: 
- https://foodkatya.zapto.org
- 89.169.173.181:8000


## Стек технологий:
- Python
- Docker
- Nginx
- Gunicorn
- Django
- Django REST Framework
- Postgres
- Github


## Авторство:
[EkaterinaRez](https://github.com/ekaterinarez)