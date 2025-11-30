#!/bin/bash

# Attendance System - Auto Update Script
# Version: 1.0

echo "=========================================="
echo "  Attendance System - Auto Update"
echo "=========================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Étape 1 : Vérifier qu'on est dans le bon répertoire
if [ ! -f "README.md" ]; then
    error "Ce script doit être exécuté depuis le répertoire racine du projet"
    exit 1
fi

info "Répertoire de travail : $(pwd)"
echo ""

# Étape 2 : Sauvegarder la base de données
info "Sauvegarde de la base de données..."
if [ -f "attendance.db" ]; then
    BACKUP_FILE="attendance.db.backup_$(date +%Y%m%d_%H%M%S)"
    cp attendance.db "$BACKUP_FILE"
    info "Base de données sauvegardée : $BACKUP_FILE"
else
    warn "Aucune base de données trouvée (première installation ?)"
fi
echo ""

# Étape 3 : Récupérer les modifications depuis GitHub
info "Récupération des modifications depuis GitHub..."
git fetch origin

if [ $? -ne 0 ]; then
    error "Échec de la récupération depuis GitHub"
    exit 1
fi

info "Mise à jour du code..."
git reset --hard origin/master

if [ $? -ne 0 ]; then
    error "Échec de la mise à jour du code"
    exit 1
fi

# Étape 3.5 : Mettre à jour le Frontend
info "Mise à jour du Frontend..."
cd frontend
# Installation des dépendances si package.json a changé
if [ -f "package.json" ]; then
    info "Installation des dépendances frontend..."
    npm install
fi

# Build du frontend
info "Compilation du Frontend (Build)..."
npm run build

if [ $? -ne 0 ]; then
    error "Échec de la compilation du Frontend"
    exit 1
fi
cd ..

# Afficher la version actuelle
CURRENT_VERSION=$(git log --oneline -1)
info "Version actuelle : $CURRENT_VERSION"
echo ""

# Étape 4 : Redémarrer le service backend
info "Redémarrage du service backend..."

# Détecter le système de gestion de services
if command -v systemctl &> /dev/null; then
    # systemd
    sudo systemctl restart attendance-backend
    if [ $? -eq 0 ]; then
        info "Service redémarré avec systemd"
        sudo systemctl status attendance-backend --no-pager -l
    else
        error "Échec du redémarrage avec systemd"
        exit 1
    fi
elif command -v pm2 &> /dev/null; then
    # PM2
    pm2 restart attendance-backend
    if [ $? -eq 0 ]; then
        info "Service redémarré avec PM2"
        pm2 status
    else
        error "Échec du redémarrage avec PM2"
        exit 1
    fi
else
    # Méthode manuelle
    warn "systemd et PM2 non détectés, redémarrage manuel..."
    pkill -f "python.*app.main"
    sleep 2
    cd backend
    nohup python -m app.main > ../backend.log 2>&1 &
    cd ..
    info "Backend redémarré manuellement (PID: $!)"
fi

echo ""

# Étape 5 : Vérification
info "Vérification du backend..."
sleep 3

if curl -s http://localhost:8000/api/employees/ > /dev/null; then
    info "✓ Backend fonctionne correctement"
else
    error "✗ Backend ne répond pas"
    warn "Vérifiez les logs : sudo journalctl -u attendance-backend -n 50"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Mise à jour terminée avec succès !${NC}"
echo "=========================================="
echo ""
info "Videz le cache de votre navigateur (Ctrl+Shift+R) pour voir les changements"
echo ""
