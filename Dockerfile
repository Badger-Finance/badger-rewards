FROM python:3.9.10-alpine3.15

WORKDIR /boost

RUN apk update && apk add --virtual build-dependencies build-base gcc wget git
RUN apk add python3-dev
RUN apk add linux-headers
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .