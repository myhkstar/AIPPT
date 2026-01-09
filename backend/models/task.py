"""
Task model - converted to plain Python class for Firestore
"""
import uuid
import json
from datetime import datetime

class Task:
    """
    Task model - tracks asynchronous generation tasks
    """
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.project_id = kwargs.get('project_id')
        self.user_id = kwargs.get('user_id')
        self.task_type = kwargs.get('task_type')
        self.status = kwargs.get('status', 'PENDING')
        self.progress = kwargs.get('progress')  # Can be dict or JSON string
        self.error_message = kwargs.get('error_message')
        
        created_at = kwargs.get('created_at')
        if isinstance(created_at, str):
            self.created_at = datetime.fromisoformat(created_at)
        else:
            self.created_at = created_at or datetime.utcnow()
            
        completed_at = kwargs.get('completed_at')
        if isinstance(completed_at, str):
            self.completed_at = datetime.fromisoformat(completed_at)
        else:
            self.completed_at = completed_at

    def get_progress(self):
        """Parse progress if it's a string"""
        if isinstance(self.progress, str):
            try:
                return json.loads(self.progress)
            except json.JSONDecodeError:
                return {"total": 0, "completed": 0, "failed": 0}
        return self.progress or {"total": 0, "completed": 0, "failed": 0}

    def to_dict(self):
        """Convert to dictionary for Firestore/JSON"""
        return {
            'task_id': self.id,
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.get_progress(),
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'completed_at': self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else self.completed_at,
        }

    @staticmethod
    def from_dict(data):
        return Task(**data)
