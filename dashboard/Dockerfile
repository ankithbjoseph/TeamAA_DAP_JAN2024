FROM python:3.11-slim

WORKDIR /dashboard

RUN python -m pip install --upgrade pip
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
CMD panel serve dashboard.py --autoreload