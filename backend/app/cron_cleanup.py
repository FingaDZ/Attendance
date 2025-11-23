"""
Automatic log cleanup service
Deletes attendance logs older than 6 months
"""
from datetime import datetime, timedelta
from sqlalchemy import text
from .database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def cleanup_old_logs():
    """Delete attendance logs older than 6 months"""
    try:
        db = SessionLocal()
        
        # Calculate cutoff date (6 months ago)
        cutoff_date = datetime.now() - timedelta(days=180)
        
        # Delete old logs using raw SQL for efficiency
        result = db.execute(
            text("DELETE FROM logs WHERE timestamp < :cutoff_date"),
            {"cutoff_date": cutoff_date}
        )
        
        deleted_count = result.rowcount
        db.commit()
        
        logger.info(f"Log cleanup completed: {deleted_count} records deleted (older than {cutoff_date.strftime('%Y-%m-%d')})")
        
    except Exception as e:
        logger.error(f"Error during log cleanup: {str(e)}")
        db.rollback()
    finally:
        db.close()
