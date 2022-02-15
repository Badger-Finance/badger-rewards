FROM python:3.9.10-alpine3.15

WORKDIR /boost

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .