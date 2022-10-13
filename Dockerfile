FROM python:3.10.3-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD python app.py