# pull official base image
FROM python:3.8.2-buster

# set work directory
WORKDIR /usr/src/mars

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apt update \
    && apt install -y gcc python3-dev musl-dev

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/mars/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/mars/
