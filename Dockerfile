FROM python:3.12-slim-bookworm

WORKDIR /app

# redunandant, but helps with docker caching
COPY src/requirements.txt . 
RUN pip install -r requirements.txt

COPY src .
