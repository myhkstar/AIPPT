"""
User Template model - converted to plain Python class for Firestore
"""
import uuid
from datetime import datetime

class UserTemplate:
    """
    User Template model - represents a user-uploaded template
    """
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.name = kwargs.get('name')
        self.file_path = kwargs.get('file_path')
        self.file_size = kwargs.get('file_size')
        
        created_at = kwargs.get('created_at')
        if isinstance(created_at, str):
            self.created_at = datetime.fromisoformat(created_at)
        else:
            self.created_at = created_at or datetime.utcnow()
            
        updated_at = kwargs.get('updated_at')
        if isinstance(updated_at, str):
            self.updated_at = datetime.fromisoformat(updated_at)
        else:
            self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for Firestore/JSON"""
        # Extract filename for URL compatibility
        filename = None
        if self.file_path:
            import os
            filename = os.path.basename(self.file_path.replace('\\', '/'))
            
        return {
            'template_id': self.id,
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'template_image_url': f'/files/user-templates/{self.id}/{filename}' if filename else None,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }

    @staticmethod
    def from_dict(data):
        return UserTemplate(**data)
