FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install flask
RUN apt-get update
RUN pip install -r requirements.txt

EXPOSE 80


CMD ["python3", "run.py"]