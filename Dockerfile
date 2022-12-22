FROM python:3.10-alpine

COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt
RUN pip3 install hypercorn

EXPOSE 5000

CMD ["hypercorn", "--bind", "0.0.0.0:5000", "src/api:app"]
