"""
API routes for notifications in the CCT Backend application.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.config.database import get_db
from app.models import schemas
from app.services import notification_service
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[schemas.Notification])
@router.get("/", response_model=List[schemas.Notification])
def get_user_notifications(
    limit: int = 100,
    unread_only: bool = False,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get notifications for the current user.
    
    This endpoint allows a user to retrieve their notifications.
    The user must be authenticated.
    """
    return notification_service.get_user_notifications(db, current_user.id, limit, unread_only)

@router.put("/{notification_id}/read", response_model=schemas.Notification)
def mark_notification_as_read(
    notification_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read.
    
    This endpoint allows a user to mark one of their notifications as read.
    The user must be authenticated.
    """
    notification = notification_service.mark_notification_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.put("/read-all", response_model=Dict[str, Any])
def mark_all_notifications_as_read(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications for the current user as read.
    
    This endpoint allows a user to mark all their notifications as read.
    The user must be authenticated.
    """
    count = notification_service.mark_all_notifications_as_read(db, current_user.id)
    return {"message": f"Marked {count} notifications as read"}

@router.post("/test", response_model=Dict[str, Any])
def send_test_notification(
    title: str,
    message: str,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Send a test notification to the current user.
    
    This endpoint allows a user to send a test notification to themselves.
    The user must be authenticated.
    """
    results = notification_service.send_notification(
        db,
        current_user.id,
        title,
        message,
        "test"
    )
    
    return {
        "message": "Test notification sent",
        "results": results
    }
