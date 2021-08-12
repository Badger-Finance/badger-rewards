FROM python:3.9

WORKDIR /boost

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod 775 start.sh
ENTRYPOINT ./start.sh