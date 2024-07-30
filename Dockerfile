FROM python:3.11

# Install PostgreSQL development packages and client tools
RUN apt-get update && apt-get install -y libpq-dev postgresql-client

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the Docker image
COPY . /app/

# Accept build arguments
ARG DATABASE_URL

# Set environment variables
ENV DATABASE_URL=$DATABASE_URL
ENV PYTHONUNBUFFERED=1

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application with gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "webscraper.wsgi:application"]