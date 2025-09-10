FROM python:3.11

WORKDIR /src/

COPY src /src/
COPY requirements.txt /src/

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w","4", "app:app", "--preload"]