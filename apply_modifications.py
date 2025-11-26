#!/usr/bin/env python3
"""
Script pour appliquer les modifications v1.7.1 à api.py
"""
import re

def apply_modifications():
    # Lire le fichier
    with open('backend/app/routers/api.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Fichier lu avec succès")
    
    # 1. Ajouter imports CSV et pandas
    content = content.replace(
        'import datetime\r\n',
        'import datetime\r\nimport csv\r\nimport pandas as pd\r\n'
    )
    print("✓ Imports ajoutés")
    
    # 2. Ajouter check_time_constraints avant check_attendance_status
    time_constraints_func = '''def check_time_constraints(log_type: str) -> tuple[bool, str]:
    """
    Vérifie si l'heure actuelle respecte les contraintes horaires.
    
    Args:
        log_type: 'ENTRY' ou 'EXIT'
    
    Returns:
        (is_valid, error_message)
    """
    now = datetime.datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_time_minutes = current_hour * 60 + current_minute
    
    if log_type == 'ENTRY':
        # ENTRY: 03h00 à 13h30
        start_time = 3 * 60  # 03:00 = 180 minutes
        end_time = 13 * 60 + 30  # 13:30 = 810 minutes
        
        if not (start_time <= current_time_minutes <= end_time):
            return False, "Les entrées sont autorisées uniquement entre 03h00 et 13h30"
    
    elif log_type == 'EXIT':
        # EXIT: 12h00 à 23h59 (pas après minuit)
        start_time = 12 * 60  # 12:00 = 720 minutes
        end_time = 23 * 60 + 59  # 23:59 = 1439 minutes
        
        if not (start_time <= current_time_minutes <= end_time):
            return False, "Les sorties sont autorisées uniquement entre 12h00 et 23h59"
    
    return True, ""

'''
    
    content = content.replace(
        'def check_attendance_status(employee_id: int, db: Session):',
        time_constraints_func + 'def check_attendance_status(employee_id: int, db: Session) -> tuple[str | None, str | None]:'
    )
    print("✓ Fonction check_time_constraints ajoutée")
    
    # 3. Modifier le corps de check_attendance_status
    old_body = '''def check_attendance_status(employee_id: int, db: Session) -> tuple[str | None, str | None]:
    """Determine if next log should be ENTRY or EXIT"""
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logs = db.query(AttendanceLog).filter(
        AttendanceLog.employee_id == employee_id,
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.asc()).all()
    
    # Strict Logic: 1 Entry / 1 Exit per day
    has_entry = any(log.type == 'ENTRY' for log in logs)
    has_exit = any(log.type == 'EXIT' for log in logs)
    
    if has_exit:
        print(f"Blocked: Already has EXIT for today.")
        return None # Day complete
        
    if not has_entry:
        return 'ENTRY'
        
    # If has_entry and not has_exit:
    # Check cooldown (4 hours = 14400 seconds)
    last_log = logs[-1]
    time_diff = (datetime.datetime.now() - last_log.timestamp.replace(tzinfo=None)).total_seconds()
    if time_diff < 14400:
        print(f"Blocked: Cooldown active. {14400 - time_diff}s remaining.")
        return None

    return 'EXIT\''''

    new_body = '''def check_attendance_status(employee_id: int, db: Session) -> tuple[str | None, str | None]:
    """Determine if next log should be ENTRY or EXIT
    
    Returns:
        (log_type, error_message)
    """
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logs = db.query(AttendanceLog).filter(
        AttendanceLog.employee_id == employee_id,
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.asc()).all()
    
    # Nouvelle logique stricte : 1 seule entrée et 1 seule sortie par jour
    entry_logs = [log for log in logs if log.type == 'ENTRY']
    exit_logs = [log for log in logs if log.type == 'EXIT']

    if len(entry_logs) >= 1 and len(exit_logs) >= 1:
        print(f"Blocked: Already has ENTRY and EXIT for today.")
        return None, "Vous avez déjà enregistré une entrée et une sortie aujourd'hui."

    if len(entry_logs) == 0:
        # Vérifier contrainte horaire pour ENTRY
        is_valid, error_msg = check_time_constraints('ENTRY')
        if not is_valid:
            return None, error_msg
        return 'ENTRY', None

    if len(entry_logs) == 1 and len(exit_logs) == 0:
        # Check cooldown (4 hours = 14400 seconds)
        last_log = logs[-1]
        time_diff = (datetime.datetime.now() - last_log.timestamp.replace(tzinfo=None)).total_seconds()
        if time_diff < 14400:
            remaining_minutes = int((14400 - time_diff) / 60)
            print(f"Blocked: Cooldown active. {remaining_minutes} minutes remaining.")
            return None, f"Vous devez attendre {remaining_minutes} minutes avant de pouvoir sortir."
        
        # Vérifier contrainte horaire pour EXIT
        is_valid, error_msg = check_time_constraints('EXIT')
        if not is_valid:
            return None, error_msg
        return 'EXIT', None

    # Toute autre situation : blocage
    print(f"Blocked: Invalid state for entry/exit logs.")
    return None, "État invalide des logs d'assiduité."'''

    content = content.replace(old_body, new_body)
    print("✓ Corps de check_attendance_status modifié")
    
    # 4. Modifier /verify-pin/
    content = content.replace(
        '''        log_type = check_attendance_status(emp.id, db)
        if not log_type:
            return {"status": "already_logged", "name": emp.name, "message": "Already logged Entry and Exit for today."}''',
        '''        log_type, error_msg = check_attendance_status(emp.id, db)
        if not log_type:
            return {"status": "blocked", "name": emp.name, "message": error_msg}'''
    )
    print("✓ Route /verify-pin/ modifiée")
    
    # 5. Modifier /log_attendance/
    content = content.replace(
        '''        log_type = check_attendance_status(employee_id, db)
        print(f"Log Request: Emp {employee_id}, Conf {confidence}. Status: {log_type}")
        if not log_type:
            return {"status": "already_logged_or_blocked"}''',
        '''        log_type, error_msg = check_attendance_status(employee_id, db)
        print(f"Log Request: Emp {employee_id}, Conf {confidence}. Status: {log_type}")
        if not log_type:
            return {"status": "blocked", "message": error_msg}'''
    )
    print("✓ Route /log_attendance/ modifiée")
    
    # Sauvegarder
    with open('backend/app/routers/api.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Toutes les modifications ont été appliquées avec succès!")
    print("Fichier sauvegardé: backend/app/routers/api.py")

if __name__ == "__main__":
    apply_modifications()
