FROM python:3.12-slim-bookworm

WORKDIR /app

# redundant, but helps with docker caching
COPY src/requirements.txt .
RUN pip install -r requirements.txt

COPY src .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "eureka.wsgi:application"]
