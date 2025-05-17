FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers du projet
COPY . .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

# Exécuter collectstatic
RUN cd Book && python manage.py collectstatic --noinput

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD cd Book && gunicorn BookNova.wsgi:application --bind 0.0.0.0:8000
