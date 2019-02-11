FROM python:3.6-slim

WORKDIR /code 
COPY . ./
RUN pip install -e .
RUN pip install --no-cache-dir -r requirements-dev.txt
