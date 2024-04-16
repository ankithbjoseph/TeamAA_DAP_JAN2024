FROM python:3.11-alpine
WORKDIR /main
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD dagit -h 0.0.0.0 -f flights_etl.py