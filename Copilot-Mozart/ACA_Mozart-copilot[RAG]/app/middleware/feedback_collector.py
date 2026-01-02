"""
Feedback Collection Module

Collects user feedback for pilot testing and continuous improvement.

Author: Fixia
Date: 2026-01-03
"""

import logging
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger("Aura.Feedback")


class FeedbackType(str, Enum):
    """Types of feedback"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    ACCURACY_ISSUE = "accuracy_issue"
    UI_FEEDBACK = "ui_feedback"
    GENERAL = "general"


class FeedbackRating(str, Enum):
    """Rating levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    OKAY = "okay"
    POOR = "poor"
    TERRIBLE = "terrible"


class FeedbackItem(TypedDict):
    """A single feedback submission"""
    id: str
    timestamp: str
    user_id: Optional[str]
    session_id: Optional[str]
    feedback_type: str
    rating: Optional[str]
    message: str
    context: Dict[str, Any]  # Current screen, action, data
    screenshot_url: Optional[str]
    is_resolved: bool


class FeedbackStats(TypedDict):
    """Aggregated feedback statistics"""
    total_count: int
    by_type: Dict[str, int]
    by_rating: Dict[str, int]
    avg_rating_score: float
    unresolved_count: int


def create_feedback(
    feedback_type: FeedbackType,
    message: str,
    rating: Optional[FeedbackRating] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    screenshot_url: Optional[str] = None,
) -> FeedbackItem:
    """
    Create a new feedback item.
    
    Args:
        feedback_type: Type of feedback
        message: User's feedback message
        rating: Optional rating
        user_id: User identifier
        session_id: Current session
        context: Additional context (screen, action, etc.)
        screenshot_url: Optional screenshot
        
    Returns:
        FeedbackItem ready for storage
    """
    import uuid
    
    feedback: FeedbackItem = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "session_id": session_id,
        "feedback_type": feedback_type.value,
        "rating": rating.value if rating else None,
        "message": message,
        "context": context or {},
        "screenshot_url": screenshot_url,
        "is_resolved": False,
    }
    
    logger.info(f"[FEEDBACK] Created: {feedback['id']} - {feedback_type.value}")
    return feedback


class FeedbackCollector:
    """
    Collects and manages user feedback.
    
    In production, this would persist to Supabase.
    This implementation uses in-memory storage for development.
    """
    
    def __init__(self):
        self._feedback: List[FeedbackItem] = []
    
    def submit(self, feedback: FeedbackItem) -> bool:
        """Submit feedback"""
        self._feedback.append(feedback)
        logger.info(f"[FEEDBACK] Submitted: {feedback['id']}")
        return True
    
    def get_all(self, limit: int = 100) -> List[FeedbackItem]:
        """Get all feedback, newest first"""
        sorted_feedback = sorted(
            self._feedback,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        return sorted_feedback[:limit]
    
    def get_by_type(self, feedback_type: FeedbackType) -> List[FeedbackItem]:
        """Get feedback by type"""
        return [
            f for f in self._feedback
            if f['feedback_type'] == feedback_type.value
        ]
    
    def get_unresolved(self) -> List[FeedbackItem]:
        """Get unresolved feedback"""
        return [f for f in self._feedback if not f['is_resolved']]
    
    def resolve(self, feedback_id: str) -> bool:
        """Mark feedback as resolved"""
        for f in self._feedback:
            if f['id'] == feedback_id:
                f['is_resolved'] = True
                logger.info(f"[FEEDBACK] Resolved: {feedback_id}")
                return True
        return False
    
    def get_stats(self) -> FeedbackStats:
        """Get aggregated statistics"""
        by_type: Dict[str, int] = {}
        by_rating: Dict[str, int] = {}
        rating_scores = []
        
        rating_values = {
            "excellent": 5,
            "good": 4,
            "okay": 3,
            "poor": 2,
            "terrible": 1,
        }
        
        for f in self._feedback:
            # Count by type
            t = f['feedback_type']
            by_type[t] = by_type.get(t, 0) + 1
            
            # Count by rating
            if f['rating']:
                r = f['rating']
                by_rating[r] = by_rating.get(r, 0) + 1
                rating_scores.append(rating_values.get(r, 3))
        
        unresolved_count = len([f for f in self._feedback if not f['is_resolved']])
        avg_score = sum(rating_scores) / len(rating_scores) if rating_scores else 0
        
        return {
            "total_count": len(self._feedback),
            "by_type": by_type,
            "by_rating": by_rating,
            "avg_rating_score": round(avg_score, 2),
            "unresolved_count": unresolved_count,
        }


# Global instance
_feedback_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """Get global feedback collector instance"""
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector


# === Quick Feedback Helpers ===

def submit_quick_feedback(
    message: str,
    rating: FeedbackRating = FeedbackRating.OKAY,
    context: Optional[Dict[str, Any]] = None
) -> FeedbackItem:
    """Quick way to submit general feedback"""
    feedback = create_feedback(
        feedback_type=FeedbackType.GENERAL,
        message=message,
        rating=rating,
        context=context,
    )
    get_feedback_collector().submit(feedback)
    return feedback


def report_accuracy_issue(
    message: str,
    context: Dict[str, Any]
) -> FeedbackItem:
    """Report accuracy/calculation issue"""
    feedback = create_feedback(
        feedback_type=FeedbackType.ACCURACY_ISSUE,
        message=message,
        context=context,
    )
    get_feedback_collector().submit(feedback)
    return feedback
