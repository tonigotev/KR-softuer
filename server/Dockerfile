FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /home/app

# Install postgresql-client for wait script
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /home/app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /home/app

# Make wait script executable
RUN chmod +x wait-for-db.sh

EXPOSE 8000

CMD ["sh", "-c", "until PGPASSWORD=\"$DB_PASSWORD\" psql -h \"$DB_HOST\" -U \"$DB_USER\" -d \"$DB_NAME\" -c '\\q' 2>/dev/null; do echo 'PostgreSQL is unavailable - sleeping'; sleep 1; done; echo 'PostgreSQL is up - executing command'; python manage.py migrate && gunicorn server.wsgi:application --bind 0.0.0.0:8000"]
