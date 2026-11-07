# Conso Maison

Application web de suivi de consommation domestique (eau, gaz, electricite
jour/nuit), auto-hebergee sur NAS via Docker, derriere un reverse proxy
Nginx Proxy Manager.

## Stack

- **Backend** : Flask + Flask-Login + Flask-SQLAlchemy
- **Base de donnees** : SQLite (un seul fichier, dans `data/`)
- **Serveur** : Gunicorn (2 workers)
- **Conteneur** : image `python:3.12-slim`, utilisateur non-root (`appuser`)
- **Frontend** : Bootstrap 5 (theme sombre) + Chart.js

## Fonctionnalites

- Saisie manuelle des releves cumulatifs par compteur et par mois
- Calcul automatique des consommations mensuelles (releve M - releve M-1)
- Moyennes mensuelles dynamiques (total / nombre de mois reels encodes)
- Suivi des couts (prix unitaire par compteur)
- Graphiques mensuels et comparatifs multi-annees, filtrables par annee
- Import historique depuis un fichier Excel (un onglet par annee)
- Authentification par login/mot de passe (hash scrypt)
- Sauvegarde automatique quotidienne de la base (cron + rotation)

## Structure du projet

    conso-maison/
    ├── docker-compose.yml      # Services app + backup
    ├── Dockerfile              # Image de l'application
    ├── Dockerfile.backup       # Image du conteneur de sauvegarde
    ├── .env                    # Secrets (NON versionne)
    ├── requirements.txt        # Dependances Python
    ├── import_xlsx.py          # Import des donnees historiques
    ├── backup.sh               # Script de sauvegarde SQLite
    ├── data/                   # Base SQLite + .xlsx (NON versionne)
    └── app/
        ├── __init__.py         # Fabrique d'app + config securite
        ├── models.py           # Modeles (User, MeterReading, CostConfig)
        ├── auth.py             # Login / logout / profil
        ├── routes.py           # Dashboard, saisie, couts, import, API
        ├── templates/          # Templates Jinja (Bootstrap)
        └── static/css/         # Feuille de style

## Prerequis

- NAS (ou serveur) avec **Docker** et **Docker Compose** (architecture x86)
- Un reverse proxy type **Nginx Proxy Manager** pour l'acces HTTPS

## Installation

1. Cloner le depot et creer les dossiers :

        git clone https://github.com/made2001/conso-maison.git
        cd conso-maison
        mkdir -p data
        chmod 777 data

2. Creer le fichier `.env` :

        SECRET_KEY=<une-chaine-aleatoire-64-caracteres>
        ADMIN_EMAIL=votre@email.com
        ADMIN_PASSWORD=votre-mot-de-passe

    Generer une clee secrete :

        python3 -c "import secrets; print(secrets.token_hex(32))"

3. Construire et lancer :

        docker compose up -d --build

    L'app demarre sur le port interne 5000, joignable via le reseau Docker
    partage avec NPM (nom d'hote `conso-maison`, port `5000`). Aucun port
    n'est publie sur l'hote.

    Le compte admin est cree automatiquement au premier demarrage a partir
    de `ADMIN_EMAIL` / `ADMIN_PASSWORD`, **uniquement si la base est vide**.

## Import des donnees historiques

Deposer un fichier `.xlsx` dans `data/` (un onglet par annee, nomme `2023`,
`2024`, etc. ; l'onglet sans titre est rattache a l'annee en cours), puis :

    docker compose exec conso python import_xlsx.py

Format attendu par onglet : ligne d'en-tete de mois, puis une ligne par
compteur (`Eau`, `Gaz`, `Elec jour`, `Elec nuit`) avec les valeurs cumulees.

## Securite

- Conteneur applicatif en **non-root**
- Mots de passe hashees (scrypt)
- Cookie de session `Secure` / `HttpOnly` / `SameSite=Lax`
- Port applicatif **non expose** sur l'hote (reseau Docker interne)
- `.env` et donnees hors du depot via `.gitignore`

## Sauvegarde automatique

Le service `backup` sauvegarde la base chaque jour a 3h via `sqlite3 .backup`
(copie coherent meme a chaud), compresse en gzip et conserve les 30 derniers
fichiers dans `/volume1/Datas/backup-conso`.

Test manuel :

    docker compose exec backup sh /backup.sh

## Commandes utiles

- Appliquer une modif de code : `docker compose up -d --build`
- Voir les logs : `docker compose logs -f conso`

### Reinitialiser le mot de passe admin

    docker compose exec conso python -c "from app import create_app, db; from app.models import User; app=create_app(); app.app_context().push(); u=User.query.first(); u.set_password('nouveau-mdp'); db.session.commit(); print('OK', u.email)"

## Restauration

Tout tient dans deux elements :

- `data/conso.db` : la base (donnees)
- `.env` : les secrets

Avec ces deux fichiers + le depot, on reconstruit l'app complete :

    docker compose up -d --build

## Licence

Usage prive.

### Reinitialiser le mot de passe admin

    docker compose exec conso python -c "from app import create_app, db; from app.models import User; app=create_app(); app.app_context().push(); u=User.query.first(); u.set_password('nouveau-mdp'); db.session.commit(); print('OK', u.email)"

## Restauration

Tout tient dans deux elements :

- `data/conso.db` : la base (donnees)
- `.env` : les secrets

Avec ces deux fichiers + le depot, on reconstruit l'app complete :

    docker compose up -d --build

## Licence

Usage prive.
