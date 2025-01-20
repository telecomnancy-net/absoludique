FROM python:3.11
WORKDIR /src/
ADD ./src /src/
ADD requirements.txt /src
ADD .env /src
RUN ls -la
RUN pip install -r requirements.txt
EXPOSE 3306
RUN python3 init_db.py
#CMD ["flask", "run", "-h", "0.0.0.0", "-p", "8000"]
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w","4", "app:app", "--preload"]
