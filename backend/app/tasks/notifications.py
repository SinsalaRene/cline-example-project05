"""Notification tasks."""
from app.tasks.base import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="send.notification")
def send_notification(self, user_id: str, notification_type: str, message: str):
    """Send a notification to a user."""
    logger.info(f"Sending {notification_type} notification to user {user_id}: {message}")
    # TODO: Implement actual notification sending
    return {"status": "sent", "user_id": user_id, "type": notification_type}


@celery_app.task(bind=True, name="process.approval")
def process_approval(self, rule_id: int, approver_id: str):
    """Process approval notification."""
    logger.info(f"Processing approval for rule {rule_id} by user {approver_id}")
    return {"status": "processed", "rule_id": rule_id}