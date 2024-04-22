FROM jupyter/minimal-notebook

WORKDIR /main

USER root
RUN apt-get update && apt-get install -y libpq-dev gcc
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


