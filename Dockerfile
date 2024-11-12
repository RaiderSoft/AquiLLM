FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=${DJANGO_DEBUG:-}
ENV GOOGLE_OAUTH2_CLIENT_ID=${GOOGLE_OAUTH2_CLIENT_ID:-}
ENV GOOGLE_OAUTH2_CLIENT_SECRET=${GOOGLE_OAUTH2_CLIENT_SECRET:-}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}
ENV COHERE_KEY=${COHERE_KEY:-}
ENV OPENAI_API_KEY=${OPENAI_API_KEY:-}
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Set working directory for Django app
WORKDIR /app/aquillm

# Collect static files
RUN yes yes | ./manage.py collectstatic

# Command to run the application
CMD ["python", "-m", "uvicorn", "aquillm.asgi:application", "--host", "0.0.0.0", "--port", "8080"]

