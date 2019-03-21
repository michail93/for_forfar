#### Пояснения 
1) Все необходимые зависимости перечисленны в ```requirements.txt```
2) Необходимая инфраструктура указана в ```docker-compose.yml```
3) В директории ```api/fixtures``` находятся fixtures для модели ```Printer```
4) В директорию ```media/pdf``` сохраняются отрисованные pdf файлы


#### Запуск приложения
1) Установите зависимости из ```requirements.txt```:
    - ```pip install -r requirements.txt```

2) Создайте и запустите docker-контейнеры из ```docker-compose.yml```:
    - ```docker-compose up```

3) После того как все контейнеры запустятся и завершат свою инициализацию, примените все необходимые миграции:
    
    - ```python manage.py makemigrations```
    - ```python manage.py migrate```
    
4) Примените fixtures:
   - ```python manage.py loaddata api/fixtures/initial_data.json```     

5) Запустите воркеров django-rq:
    - ```python manage.py rqworker default```
    
6) Запустите приложение:
    - ```python manage.py runserver```

#### Тесты
1) Сначала запустите воркеров django-rq:
    - ```python manage.py rqworker default```

2) Зпустите сами тесты:
    - ```python manage.py test```