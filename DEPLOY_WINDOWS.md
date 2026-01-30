# Deployment Guide - Windows

## Système de Pointage par Reconnaissance Faciale

---

## 🚀 Déploiement Rapide (5 minutes)

### Prérequis
- Windows 10/11 (64-bit)
- Connexion Internet
- Droits Administrateur

### Étape 1: Installer Python 3.11

```powershell
# Ouvrir PowerShell en tant qu'Administrateur
winget install Python.Python.3.11
```

> ⚠️ **Important**: Python 3.11 est obligatoire. Les versions 3.12+ ne sont pas compatibles avec InsightFace.

### Étape 2: Télécharger et Installer

```powershell
# Cloner le repository
git clone https://github.com/FingaDZ/Attendance.git C:\Attendance
cd C:\Attendance

# Lancer l'installation (en Admin)
install_windows.bat
```

### Étape 3: Installer comme Service Windows

```powershell
# Installer le service (en Admin)
install_service.bat
```

---

## 📋 Déploiement Détaillé

### 1. Vérifier les Prérequis

| Composant | Version | Vérification |
|-----------|---------|--------------|
| Python | 3.11.x | `py -3.11 --version` |
| Node.js | 20+ LTS | `node --version` |
| Git | 2.x+ | `git --version` |

Si un composant manque, le script `install_windows.bat` l'installera automatiquement via `winget`.

### 2. Installation

```powershell
# En tant qu'Administrateur
cd C:\
git clone https://github.com/FingaDZ/Attendance.git C:\Attendance
cd C:\Attendance
install_windows.bat
```

Le script effectue:
1. ✅ Vérifie/installe les prérequis (Python 3.11, Node.js, Git)
2. ✅ Clone le code source
3. ✅ Crée l'environnement Python virtuel
4. ✅ Installe les dépendances backend (FastAPI, InsightFace, etc.)
5. ✅ Installe les dépendances frontend (React, Vite)
6. ✅ Build le frontend pour production
7. ✅ Crée un raccourci de démarrage automatique

### 3. Installation du Service

```powershell
# En tant qu'Administrateur
cd C:\Attendance
install_service.bat
```

Le service:
- Démarre automatiquement au boot Windows
- Redémarre automatiquement en cas de crash
- Tourne en arrière-plan (pas de fenêtre)
- Logs dans `C:\Attendance\logs\`

---

## 🌐 Configuration Réseau

### Accès Local
```
http://localhost:8000
http://localhost:8000/kiosk
```

### Accès LAN (autres PC du réseau)

1. **Trouver l'IP du serveur:**
```powershell
ipconfig | findstr "IPv4"
```

2. **Ouvrir le pare-feu:**
```powershell
netsh advfirewall firewall add rule name="Attendance System" dir=in action=allow protocol=TCP localport=8000
```

3. **Accéder depuis un autre PC:**
```
http://192.168.1.X:8000
http://192.168.1.X:8000/kiosk
```

### Accès Caméra sur LAN (HTTP)

Pour que la caméra fonctionne sur HTTP depuis un autre PC:

1. Ouvrir Chrome/Edge sur le **PC client**
2. Aller à `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. Ajouter: `http://192.168.1.X:8000`
4. Redémarrer le navigateur

---

## 🔧 Commandes de Gestion

### Service Windows

```powershell
# Statut
sc query AttendanceSystem

# Démarrer
net start AttendanceSystem

# Arrêter
net stop AttendanceSystem

# Redémarrer
net stop AttendanceSystem & net start AttendanceSystem

# Supprimer le service
C:\Attendance\tools\nssm.exe remove AttendanceSystem
```

### Mode Script (sans service)

```powershell
# Démarrer manuellement
C:\Attendance\start_system.bat

# Arrêter
Ctrl+C ou taskkill /F /IM python.exe
```

---

## 📁 Structure des Fichiers

```
C:\Attendance\
├── backend\
│   ├── venv\              # Environnement Python
│   ├── app\               # Code backend
│   └── requirements.txt
├── frontend\
│   ├── dist\              # Build production
│   └── src\               # Code source React
├── logs\                  # Logs du service
├── tools\
│   └── nssm.exe           # Gestionnaire de service
├── attendance.db          # Base de données SQLite
├── install_windows.bat    # Script d'installation
├── install_service.bat    # Installation service
├── start_system.bat       # Démarrage manuel
└── update_windows.bat     # Mise à jour
```

---

## 🔄 Mise à Jour

```powershell
# Arrêter le service
net stop AttendanceSystem

# Mettre à jour
cd C:\Attendance
update_windows.bat

# Redémarrer
net start AttendanceSystem
```

---

## ❓ Dépannage

### Le service ne démarre pas
```powershell
# Vérifier les logs
type C:\Attendance\logs\service-error.log
```

### Erreur InsightFace / NumPy
```powershell
cd C:\Attendance\backend
venv\Scripts\pip install "numpy<2"
```

### Caméra non accessible
1. Vérifier qu'aucune autre app n'utilise la caméra
2. Supprimer les caméras backend: `curl -X DELETE http://localhost:8000/api/cameras/1`
3. Utiliser HTTPS ou le flag Chrome pour HTTP

### Port 8000 déjà utilisé
```powershell
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

---

## 📞 Support

- **Repository**: https://github.com/FingaDZ/Attendance
- **Version**: 2.12.0
