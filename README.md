# WebScraping

Welcome to the WebScraping GitHub repository! This project is a Django-based web application that leverages Docker for easy deployment and management. The application includes several features such as asynchronous task processing with Celery, real-time updates using Redis, and a PostgreSQL database. Gunicorn is used to serve the application.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Telegram Bot](#telegram-bot)

## Getting Started

These instructions will help you set up and run the project on your local machine for development and testing purposes.

## Prerequisites

- Docker
- Docker Compose
- Telegram account (for using the bot)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/webscraping.git
    cd webscraping
    ```

2. **Build and run the Docker containers:**

    ```bash
    docker-compose up -d --build
    ```

## Configuration

Before running the project, you need to configure the Django settings to allow your IP address. Open the `settings.py` file and add your IP to the `ALLOWED_HOSTS` list.

```python
ALLOWED_HOSTS = ['your_ip_address', 'another_ip_address', 'localhost']
