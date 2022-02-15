FROM python:3.9.10-alpine3.15

WORKDIR /boost

RUN apk update && apk add --virtual build-dependencies build-base gcc wget git
RUN apk add python3-dev
RUN apk add linux-headers
RUN apk add expat>=2.4.4-r0
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .