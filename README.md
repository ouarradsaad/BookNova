# BookNova - Système de Gestion de Bibliothèque

BookNova est une application complète de gestion de bibliothèque développée avec Django. Elle permet de gérer efficacement les livres, les emprunts, les retours et les utilisateurs d'une bibliothèque.

## Fonctionnalités

- **Gestion des livres** : ajouter, modifier, supprimer, visualiser les livres
- **Gestion des emprunts** : enregistrer les emprunts, gérer les retours
- **Gestion des utilisateurs** : différents types d'utilisateurs (bibliothécaires et lecteurs)
- **Tableau de bord** : statistiques sur les livres, emprunts, retards, et taux de rotation
- **Réservations** : permettre aux lecteurs de réserver des livres

## Technologies utilisées

- Backend : Django
- Frontend : HTML, CSS, JavaScript, Bootstrap
- Base de données : PostgreSQL (en production via Railway)

## Installation en local

1. Cloner le repository
```bash
git clone https://github.com/ouarradsaad/BookNova.git
cd BookNova
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Configurer la base de données

4. Exécuter les migrations
```bash
python manage.py migrate
```

5. Lancer le serveur
```bash
python manage.py runserver
```

## Déploiement sur Railway

Ce projet est configuré pour être déployé sur Railway avec une base de données PostgreSQL.
