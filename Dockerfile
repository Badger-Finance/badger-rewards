FROM python:3.9.10-bullseye

WORKDIR /boost

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .