FROM python:3.11

WORKDIR /code

COPY /app/requirements.txt /code/
COPY /app/ /code/
RUN pip install -U pip
RUN pip install -r requirements.txt

CMD python3 manage.py makemigrations --noinput && \
    python3 manage.py migrate --noinput && \
    python3 manage.py collectstatic --noinput && \
    gunicorn -b 0.0.0.0:8000 tracker.wsgi --reload;

    
