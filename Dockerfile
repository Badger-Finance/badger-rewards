FROM python:3.9

WORKDIR /boost

COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y jq && apt-get install -y awscli
RUN pip install -r requirements.txt

COPY . .
RUN [ "chmod", "+x", "start.sh" ]