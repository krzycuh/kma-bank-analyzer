# Faza 4: Deployment na Raspberry Pi

**Czas trwania:** 2 dni  
**Cel:** Production deployment całego stacku na RPI

## Przegląd

W tej fazie wdrażamy cały system na Raspberry Pi z monitoringiem, backupem i zabezpieczeniami produkcyjnymi.

## Wymagania systemowe

### Raspberry Pi
- Model: RPi 4 (2GB+ RAM zalecane)
- OS: Raspberry Pi OS (64-bit) lub Ubuntu Server
- Storage: 32GB+ microSD (lub SSD przez USB)
- Network: Ethernet lub WiFi

### Software
- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl, wget

## Przygotowanie RPI

### Krok 1: Aktualizacja systemu

```bash
# Update i upgrade
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y \
    git \
    curl \
    wget \
    htop \
    vim \
    net-tools
```

### Krok 2: Instalacja Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Dodaj użytkownika do grupy docker
sudo usermod -aG docker $USER

# Relogin lub:
newgrp docker

# Sprawdź instalację
docker --version
docker ps
```

### Krok 3: Instalacja Docker Compose

```bash
# Docker Compose (już included w nowszych wersjach Docker)
docker compose version

# Jeśli nie ma, zainstaluj:
sudo apt install docker-compose-plugin
```

### Krok 4: Struktura katalogów

```bash
# Utwórz główny katalog projektu
mkdir -p ~/kma-bank-analyzer
cd ~/kma-bank-analyzer

# Utwórz strukturę
mkdir -p {data/{input,processed,output},logs,config,backups}

# Uprawnienia
chmod 755 data/{input,processed,output} logs config
```

## Clone projektu

```bash
cd ~/kma-bank-analyzer

# Clone repo
git clone https://github.com/[username]/kma-bank-analyzer.git repo

# Lub jeśli używasz SSH
git clone git@github.com:[username]/kma-bank-analyzer.git repo

cd repo
```

## Konfiguracja

### Krok 1: Pliki konfiguracyjne

```bash
# Skopiuj przykłady
cp config/categories.example.yaml ../config/categories.yaml
cp config/rules.example.yaml ../config/rules.yaml

# Edytuj według potrzeb
nano ../config/categories.yaml
nano ../config/rules.yaml
```

### Krok 2: Environment variables

```bash
# Utwórz .env w katalogu głównym (nie w repo!)
cd ~/kma-bank-analyzer
nano .env
```

**Zawartość .env:**
```bash
# n8n Credentials
N8N_USER=admin
N8N_PASSWORD=twoje_silne_haslo_tutaj_zmien

# Google Sheets (opcjonalnie)
GOOGLE_SHEETS_ID=

# Timezone
TZ=Europe/Warsaw

# Logging
LOG_LEVEL=INFO

# Paths (relative to project root)
DATA_DIR=./data
CONFIG_DIR=./config
LOGS_DIR=./logs
```

**Zabezpiecz .env:**
```bash
chmod 600 .env
```

### Krok 3: docker-compose.prod.yml

Utwórz w katalogu głównym:

```bash
nano docker-compose.prod.yml
```

```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/[username]/kma-bank-analyzer/api:latest
    container_name: bank-analyzer-api
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - TZ=${TZ:-Europe/Warsaw}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 1m
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - bank-analyzer
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  n8n:
    image: n8nio/n8n:latest
    container_name: bank-analyzer-n8n
    restart: unless-stopped
    ports:
      - "127.0.0.1:5678:5678"  # Tylko localhost
    volumes:
      - n8n_data:/home/node/.n8n
      - ./data:/data
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - GENERIC_TIMEZONE=${TZ:-Europe/Warsaw}
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_LOG_LEVEL=info
      - TZ=${TZ:-Europe/Warsaw}
    depends_on:
      api:
        condition: service_healthy
    networks:
      - bank-analyzer
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  bank-analyzer:
    driver: bridge

volumes:
  n8n_data:
    driver: local
```

## Deployment

### Krok 1: Pull obrazów

```bash
cd ~/kma-bank-analyzer

# Pull latest images
docker compose -f docker-compose.prod.yml pull
```

### Krok 2: Start services

```bash
# Start w tle
docker compose -f docker-compose.prod.yml up -d

# Sprawdź status
docker compose -f docker-compose.prod.yml ps

# Sprawdź logi
docker compose -f docker-compose.prod.yml logs -f
```

### Krok 3: Weryfikacja

```bash
# API health check
curl http://localhost:8000/health

# n8n (z przeglądarki)
# http://[RPI_IP]:5678
```

### Krok 4: Import n8n workflow

1. Otwórz n8n: `http://[RPI_IP]:5678`
2. Login: admin / hasło z .env
3. Workflows → Import from File
4. Wybierz: `repo/n8n/workflows/bank-statement-processor.json`
5. Configure Google Sheets credentials
6. Activate workflow

## Automatyzacja

### Update script

```bash
cd ~/kma-bank-analyzer
nano update.sh
```

```bash
#!/bin/bash
set -e

echo "🔄 Aktualizacja kma-bank-analyzer..."

cd ~/kma-bank-analyzer

# Backup config
echo "📦 Backup konfiguracji..."
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz config/

# Pull latest code
echo "📥 Pulling latest code..."
cd repo
git pull origin main
cd ..

# Pull latest images
echo "🐳 Pulling latest Docker images..."
docker compose -f docker-compose.prod.yml pull

# Restart services
echo "🔄 Restarting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for health
echo "⏳ Czekam na health check..."
sleep 10

# Verify
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed!"
    exit 1
fi

echo "✅ Update zakończony pomyślnie!"
```

```bash
chmod +x update.sh
```

## Monitoring

### Health check script

```bash
cd ~/kma-bank-analyzer
nano health_check.sh
```

```bash
#!/bin/bash

LOG_FILE="logs/health_check.log"
ALERT_EMAIL="your@email.com"  # Opcjonalnie

# API health check
if ! curl -f http://localhost:8000/health &> /dev/null; then
    echo "[$(date)] ❌ API is DOWN" >> $LOG_FILE
    
    # Restart API
    docker compose -f docker-compose.prod.yml restart api
    sleep 10
    
    # Sprawdź ponownie
    if ! curl -f http://localhost:8000/health &> /dev/null; then
        echo "[$(date)] ❌ API restart FAILED" >> $LOG_FILE
        # Opcjonalnie: wyślij email/SMS
    else
        echo "[$(date)] ✅ API restarted successfully" >> $LOG_FILE
    fi
else
    echo "[$(date)] ✅ API is healthy" >> $LOG_FILE
fi

# n8n health (sprawdź czy kontener działa)
if ! docker ps | grep -q bank-analyzer-n8n; then
    echo "[$(date)] ❌ n8n container is DOWN" >> $LOG_FILE
    docker compose -f docker-compose.prod.yml restart n8n
else
    echo "[$(date)] ✅ n8n is running" >> $LOG_FILE
fi
```

```bash
chmod +x health_check.sh
```

### Cron jobs

```bash
# Edytuj crontab
crontab -e
```

Dodaj:
```cron
# Health check co 15 minut
*/15 * * * * /home/pi/kma-bank-analyzer/health_check.sh

# Backup codziennie o 3:00
0 3 * * * /home/pi/kma-bank-analyzer/backup.sh

# Update co niedzielę o 4:00 (opcjonalnie)
0 4 * * 0 /home/pi/kma-bank-analyzer/update.sh

# Cleanup starych logów raz w miesiącu
0 2 1 * * find /home/pi/kma-bank-analyzer/logs -name "*.log" -mtime +90 -delete
```

## Backup

### Backup script

```bash
cd ~/kma-bank-analyzer
nano backup.sh
```

```bash
#!/bin/bash
set -e

BACKUP_DIR="/home/pi/kma-bank-analyzer/backups"
EXTERNAL_BACKUP="/mnt/external/backups"  # Opcjonalnie: external drive
DATE=$(date +%Y%m%d_%H%M%S)

echo "📦 Starting backup: $DATE"

# Backup config
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" config/

# Backup processed data
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" \
    data/processed/ \
    data/output/ \
    data/state.json 2>/dev/null || true

# Backup n8n data
docker run --rm \
    -v bank-analyzer_n8n_data:/source \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/n8n_$DATE.tar.gz" -C /source .

# Copy to external drive if mounted
if [ -d "$EXTERNAL_BACKUP" ]; then
    echo "📤 Copying to external drive..."
    cp "$BACKUP_DIR"/*.tar.gz "$EXTERNAL_BACKUP/" 2>/dev/null || true
fi

# Cleanup old backups (>30 dni)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "✅ Backup completed: $DATE"
```

```bash
chmod +x backup.sh
```

### Restore from backup

```bash
# Stop services
docker compose -f docker-compose.prod.yml down

# Restore config
tar -xzf backups/config_YYYYMMDD_HHMMSS.tar.gz

# Restore data
tar -xzf backups/data_YYYYMMDD_HHMMSS.tar.gz

# Restore n8n
docker run --rm \
    -v bank-analyzer_n8n_data:/target \
    -v ~/kma-bank-analyzer/backups:/backup \
    alpine sh -c "cd /target && tar xzf /backup/n8n_YYYYMMDD_HHMMSS.tar.gz"

# Start services
docker compose -f docker-compose.prod.yml up -d
```

## Security

### Firewall (ufw)

```bash
# Install if needed
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow n8n only from LAN
sudo ufw allow from 192.168.1.0/24 to any port 5678 proto tcp

# Enable firewall
sudo ufw enable

# Status
sudo ufw status
```

### Fail2ban (opcjonalnie)

```bash
# Install
sudo apt install fail2ban

# Configure
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### SSL/HTTPS z Caddy (opcjonalnie)

Jeśli chcesz wystawić n8n przez HTTPS:

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Caddyfile
sudo nano /etc/caddy/Caddyfile
```

```
n8n.yourdomain.com {
    reverse_proxy localhost:5678
}
```

```bash
sudo systemctl reload caddy
```

## Monitoring dashboard

### Portainer (opcjonalnie)

```bash
# Install Portainer
docker volume create portainer_data

docker run -d \
  -p 9000:9000 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

Dostęp: `http://[RPI_IP]:9000`

## Troubleshooting

### Logi

```bash
# API logs
docker logs -f bank-analyzer-api

# n8n logs
docker logs -f bank-analyzer-n8n

# Wszystkie logs
docker compose -f docker-compose.prod.yml logs -f

# System logs
journalctl -u docker -f
```

### Restart usług

```bash
# Restart pojedynczego serwisu
docker compose -f docker-compose.prod.yml restart api

# Restart wszystkich
docker compose -f docker-compose.prod.yml restart

# Full reset
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Sprawdzenie zasobów

```bash
# Ogólne
htop

# Docker stats
docker stats

# Disk usage
df -h
du -sh ~/kma-bank-analyzer/*

# Docker disk usage
docker system df
```

### Cleanup

```bash
# Usuń nieużywane obrazy
docker image prune -a

# Usuń nieużywane volumes
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

## Performance tuning (opcjonalnie)

### Docker memory limits

W docker-compose.prod.yml dodaj:

```yaml
services:
  api:
    # ...
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  
  n8n:
    # ...
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### Swap (jeśli RPI ma mało RAM)

```bash
# Zwiększ swap
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Maintenance checklist

### Codziennie (automatyczne)
- [ ] Health checks działają
- [ ] Backup wykonany

### Co tydzień (ręcznie)
- [ ] Sprawdź logi (błędy?)
- [ ] Sprawdź miejsce na dysku
- [ ] Sprawdź Google Sheets (dane zapisują się?)

### Co miesiąc
- [ ] Update obrazów Docker (`./update.sh`)
- [ ] Sprawdź backupy (czy da się restore?)
- [ ] Cleanup starych logów
- [ ] Review kategorii i reguł

## Deliverables Fazy 4

### Checklist

- [ ] RPI przygotowane (Docker, katalogi)
- [ ] Projekt sklonowany
- [ ] Konfiguracja (.env, config files)
- [ ] docker-compose.prod.yml
- [ ] Services uruchomione
- [ ] n8n workflow zaim portowany i aktywny
- [ ] Health checks skonfigurowane (cron)
- [ ] Backup automation (cron)
- [ ] Update script
- [ ] Firewall skonfigurowany
- [ ] Monitoring (logi, stats)
- [ ] Dokumentacja deployment

### Test produkcyjny

1. Wrzuć plik CSV do `data/input/`
2. Poczekaj na cron (lub trigger ręcznie w n8n)
3. Sprawdź:
   - [ ] Logi API (parsowanie)
   - [ ] n8n execution (success)
   - [ ] Google Sheets (nowe dane)
   - [ ] Plik w `data/processed/`
   - [ ] `state.json` zaktualizowany
4. Restart RPI
5. Sprawdź:
   - [ ] Services auto-start
   - [ ] Health checks działają

## Next Steps

System jest gotowy do użycia produkcyjnego! 

### Przyszłe rozszerzenia (opcjonalne):
- Web UI dla zarządzania
- ML dla kategoryzacji
- Więcej banków
- Mobile notifications
- Analytics dashboard
