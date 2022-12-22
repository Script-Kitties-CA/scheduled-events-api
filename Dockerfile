FROM python:3.10-alpine

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

COPY . /app

WORKDIR /app/src

EXPOSE 5000

CMD ["gunicorn", "--access-logfile", "-", "--log-level", "INFO", "--bind", "0.0.0.0:5000", "api:app"]
