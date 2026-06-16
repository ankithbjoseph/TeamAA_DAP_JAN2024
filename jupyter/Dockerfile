FROM jupyter/minimal-notebook

WORKDIR /main

USER root
RUN apt-get update && apt-get install -y libpq-dev gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
