#!/bin/bash

# Attendance System - Clean Reinstall Script
# Version: 1.0
# ATTENTION: Ce script efface tout sauf la base de données !

echo "=========================================="
echo "  Attendance System - Clean Reinstall"
echo "=========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Confirmation
echo -e "${RED}⚠️  ATTENTION ⚠️${NC}"
echo "Ce script va :"
echo "  - Sauvegarder la base de données"
echo "  - Supprimer TOUT le code"
echo "  - Réinstaller depuis GitHub"
echo "  - Restaurer la base de données"
echo ""
read -p "Êtes-vous sûr ? (tapez 'OUI' en majuscules) : " confirm

if [ "$confirm" != "OUI" ]; then
    error "Annulation de la réinstallation"
    exit 1
fi

echo ""
info "Début de la réinstallation..."
echo ""

# Étape 1 : Sauvegarder la base de données
info "Sauvegarde de la base de données..."
DB_BACKUP="/tmp/attendance.db.backup_$(date +%Y%m%d_%H%M%S)"

if [ -f "attendance.db" ]; then
    cp attendance.db "$DB_BACKUP"
    info "Base de données sauvegardée : $DB_BACKUP"
else
    warn "Aucune base de données trouvée"
    DB_BACKUP=""
fi

# Étape 2 : Arrêter le service
info "Arrêt du service backend..."
if command -v systemctl &> /dev/null; then
    sudo systemctl stop attendance-backend
    info "Service arrêté"
else
    pkill -f "python.*app.main"
    info "Processus Python arrêté"
fi

# Étape 3 : Supprimer tout le code
info "Suppression du code actuel..."
cd ..
PROJECT_DIR=$(basename "$(pwd)/Attendance")
rm -rf Attendance
info "Code supprimé"

# Étape 4 : Cloner depuis GitHub
info "Clonage depuis GitHub..."
git clone https://github.com/FingaDZ/Attendance.git
cd Attendance

if [ $? -ne 0 ]; then
    error "Échec du clonage depuis GitHub"
    exit 1
fi

info "Code récupéré depuis GitHub"

# Étape 5 : Restaurer la base de données
if [ -n "$DB_BACKUP" ]; then
    info "Restauration de la base de données..."
    cp "$DB_BACKUP" attendance.db
    info "Base de données restaurée"
fi

# Étape 6 : Installer les dépendances backend
info "Installation des dépendances backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    error "Échec de l'installation des dépendances"
    exit 1
fi

cd ..
info "Dépendances installées"

# Étape 7 : Redémarrer le service
info "Redémarrage du service backend..."

if command -v systemctl &> /dev/null; then
    sudo systemctl start attendance-backend
    sleep 3
    sudo systemctl status attendance-backend --no-pager -l
else
    cd backend
    nohup python -m app.main > ../backend.log 2>&1 &
    cd ..
    info "Backend démarré manuellement (PID: $!)"
fi

# Étape 8 : Vérification
info "Vérification du backend..."
sleep 5

if curl -s http://localhost:8000/api/employees/ > /dev/null; then
    info "✓ Backend fonctionne correctement"
else
    error "✗ Backend ne répond pas"
    warn "Vérifiez les logs : sudo journalctl -u attendance-backend -n 50"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Réinstallation terminée !${NC}"
echo "=========================================="
echo ""
info "Version actuelle : $(git log --oneline -1)"
info "Base de données : $([ -f attendance.db ] && echo 'Restaurée' || echo 'Nouvelle')"
echo ""
warn "N'oubliez pas de vider le cache de votre navigateur (Ctrl+Shift+R)"
echo ""
