# Deployment Anleitung - Grocery Shopping List

Dieses Dokument beschreibt, wie Sie die Grocery Shopping List Anwendung auf Ihrem Server deployen.

## Voraussetzungen

- Docker (Version 20.10 oder höher)
- Docker Compose (Version 1.29 oder höher)
- Git (optional, für das Klonen des Repositories)

## Schnellstart mit Docker Compose

### 1. Repository klonen oder Dateien kopieren

```bash
git clone <repository-url> grocery-shopping-list
cd grocery-shopping-list
```

Oder kopieren Sie alle Dateien auf Ihren Server.

### 2. Umgebungsvariablen konfigurieren

Erstellen Sie eine `.env` Datei basierend auf `.env.example`:

```bash
cp .env.example .env
```

**WICHTIG:** Ändern Sie den `SECRET_KEY` in der `.env` Datei:

```bash
# Generieren Sie einen sicheren Secret Key:
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Fügen Sie den generierten Key in die .env Datei ein:
# SECRET_KEY=<generierter-key>
```

### 3. Anwendung starten

```bash
docker-compose up -d
```

Die Anwendung ist nun unter http://localhost:5000 erreichbar.

### 4. Standard-Admin-Login

Nach dem ersten Start können Sie sich mit folgenden Zugangsdaten anmelden:

- **Benutzername:** admin
- **Passwort:** admin123

**WICHTIG:** Ändern Sie das Admin-Passwort sofort nach dem ersten Login!

## Manuelles Deployment mit Docker

### 1. Docker Image bauen

```bash
docker build -t grocery-shopping-list:latest .
```

### 2. Container starten

```bash
docker run -d \
  --name grocery-shopping-list \
  -p 5000:5000 \
  -e SECRET_KEY="<ihr-geheimer-schlüssel>" \
  -e FLASK_CONFIG=config.ProductionConfig \
  -v $(pwd)/instance:/app/instance \
  grocery-shopping-list:latest
```

## Reverse Proxy Setup (Nginx)

Für Production-Deployments empfiehlt sich die Verwendung eines Reverse Proxys wie Nginx.

### Nginx Konfiguration

Erstellen Sie eine neue Nginx-Konfiguration:

```nginx
# /etc/nginx/sites-available/grocery-shopping-list

server {
    listen 80;
    server_name ihre-domain.de;

    # Optional: Redirect to HTTPS
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (falls später benötigt)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (optional - für bessere Performance)
    location /static {
        alias /pfad/zu/grocery-shopping-list/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Aktivieren Sie die Konfiguration:

```bash
sudo ln -s /etc/nginx/sites-available/grocery-shopping-list /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS mit Let's Encrypt (optional)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ihre-domain.de
```

## Datenpersistenz

Die SQLite-Datenbank wird im `instance/` Verzeichnis gespeichert. Dieses Verzeichnis wird als Volume gemountet, sodass die Daten auch nach Container-Neustarts erhalten bleiben.

### Backup erstellen

```bash
# Datenbank sichern
docker-compose exec web flask db upgrade
cp instance/app.db instance/app.db.backup-$(date +%Y%m%d-%H%M%S)
```

### Backup wiederherstellen

```bash
# Container stoppen
docker-compose down

# Backup wiederherstellen
cp instance/app.db.backup-YYYYMMDD-HHMMSS instance/app.db

# Container neu starten
docker-compose up -d
```

## Wartung

### Logs anzeigen

```bash
# Docker Compose
docker-compose logs -f

# Nur Web-Service
docker-compose logs -f web

# Nur die letzten 100 Zeilen
docker-compose logs --tail=100 web
```

### Container neu starten

```bash
docker-compose restart
```

### Anwendung aktualisieren

```bash
# Neueste Version pullen (falls Git verwendet wird)
git pull

# Container neu bauen und starten
docker-compose down
docker-compose up -d --build
```

### Container stoppen

```bash
docker-compose down
```

### Container und Volumes löschen (VORSICHT: Daten gehen verloren!)

```bash
docker-compose down -v
```

## Datenbank-Migrationen

Falls Sie Änderungen am Datenbankschema vornehmen:

```bash
# In den Container einloggen
docker-compose exec web bash

# Migration erstellen
flask db migrate -m "Beschreibung der Änderung"

# Migration anwenden
flask db upgrade
```

## CLI-Befehle im Container ausführen

```bash
# Benutzer auflisten
docker-compose exec web flask list-users

# Statistiken anzeigen
docker-compose exec web flask stats

# Neuen Admin erstellen
docker-compose exec web flask create-admin

# Neuen Benutzer erstellen
docker-compose exec web flask create-user --username test --email test@example.com --password test123
```

## Sicherheitshinweise

1. **SECRET_KEY ändern:** Verwenden Sie in Production IMMER einen zufällig generierten Secret Key!
2. **Admin-Passwort ändern:** Ändern Sie das Standard-Admin-Passwort sofort nach dem ersten Login!
3. **HTTPS verwenden:** In Production sollten Sie immer HTTPS verwenden (siehe Nginx + Let's Encrypt)
4. **Firewall konfigurieren:** Öffnen Sie nur die notwendigen Ports (80, 443)
5. **Regelmäßige Backups:** Erstellen Sie regelmäßig Backups Ihrer Datenbank
6. **Updates:** Halten Sie Docker und die Anwendung aktuell

## Fehlerbehebung

### Container startet nicht

```bash
# Logs überprüfen
docker-compose logs web

# Container-Status überprüfen
docker-compose ps
```

### Datenbank-Fehler

```bash
# Migrations-Status überprüfen
docker-compose exec web flask db current

# Migrationen neu anwenden
docker-compose exec web flask db upgrade
```

### Permission-Fehler

```bash
# Berechtigungen für instance-Verzeichnis setzen
sudo chown -R 1000:1000 instance/
```

## Performance-Optimierung

### Gunicorn-Worker anpassen

Bearbeiten Sie die `CMD` im Dockerfile:

```dockerfile
# Anzahl der Worker: (2 × CPU Cores) + 1
CMD ["sh", "-c", "flask db upgrade && flask init-db && gunicorn --bind 0.0.0.0:5000 --workers 8 --threads 4 --timeout 60 --access-logfile - --error-logfile - 'app:create_app()'"]
```

### PostgreSQL verwenden (statt SQLite)

Für größere Deployments empfiehlt sich PostgreSQL:

```yaml
# docker-compose.yml erweitern:
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: grocery_db
      POSTGRES_USER: grocery_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://grocery_user:secure_password@db:5432/grocery_db

volumes:
  postgres_data:
```

Dann `psycopg2` zu `requirements.txt` hinzufügen.

## Support

Bei Problemen oder Fragen:
- Überprüfen Sie die Logs: `docker-compose logs -f`
- Prüfen Sie die Systemressourcen: `docker stats`
- Konsultieren Sie die README.md und weitere Dokumentation

## Systemanforderungen

### Minimum

- 1 CPU Core
- 512 MB RAM
- 1 GB Festplattenspeicher

### Empfohlen

- 2+ CPU Cores
- 2 GB RAM
- 5 GB Festplattenspeicher (für Logs und Backups)
