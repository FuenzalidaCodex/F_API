# F_API

Esta api usa API_KEYS que estaran en un archivo aparte en la entrega
Las API_KEY se dejan al final de C:F_API\ferremas_api\ferremas_api\settings.py

carga esta F_API primero y luego la F_WEB:

inicias con:

cd ferremas_api

y:

python -m venv env

luego:

env\Scripts\activate

y luego con:

pip install -r requirements.txt

puedes cargar migraciones por si acaso:

python manage.py makemigrations
python manage.py migrate


con el siguiente comando inicias el server:

python manage.py runserver 0.0.0.0:8000