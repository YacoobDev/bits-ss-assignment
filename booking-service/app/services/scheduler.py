import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.services.booking_logic import expire_stale_holds

logger = logging.getLogger(__name__)

def run_expiry_job():
    db = SessionLocal()
    try:
        reclaimed = expire_stale_holds(db)
        if reclaimed > 0:
            logger.info(f"[Expiry Job] Reclaimed {reclaimed} expired slot holds.")
    except Exception as e:
        logger.error(f"[Expiry Job Error]: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every 5 seconds to automatically expire abandoned holds
    scheduler.add_job(run_expiry_job, 'interval', seconds=5)
    scheduler.start()
    logger.info("Background hold-expiration scheduler started.")
