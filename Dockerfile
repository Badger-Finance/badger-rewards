FROM python:3.9

WORKDIR /boost

RUN chmod 755 start.sh
COPY requirements.txt .
RUN apt-get update
RUN apt-get install -y jq && apt-get install -y awscli
RUN pip install -r requirements.txt

COPY . .