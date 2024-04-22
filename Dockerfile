FROM python:3.11-slim

WORKDIR /main
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD dagit -h 0.0.0.0 -f extract_transform_load.py