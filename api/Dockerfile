FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user instead of root
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# One worker process so seeding runs once; threads handle concurrent requests.
# Hosts like Render choose the port through $PORT; locally it defaults to 5000.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --access-logfile - wsgi:app"]
