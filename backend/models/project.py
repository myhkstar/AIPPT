"""
Project model - converted to plain Python class for Firestore
"""
import uuid
from datetime import datetime

class Project:
    """
    Project model - represents a PPT project
    """
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.idea_prompt = kwargs.get('idea_prompt')
        self.outline_text = kwargs.get('outline_text')
        self.description_text = kwargs.get('description_text')
        self.extra_requirements = kwargs.get('extra_requirements')
        self.creation_type = kwargs.get('creation_type', 'idea')
        self.template_image_path = kwargs.get('template_image_path')
        self.status = kwargs.get('status', 'DRAFT')
        
        # Handle datetime conversion if coming from Firestore
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

    def to_dict(self, include_pages=False):
        """Convert to dictionary for Firestore/JSON"""
        data = {
            'project_id': self.id,
            'id': self.id,
            'user_id': self.user_id,
            'idea_prompt': self.idea_prompt,
            'outline_text': self.outline_text,
            'description_text': self.description_text,
            'extra_requirements': self.extra_requirements,
            'creation_type': self.creation_type,
            'template_image_url': f'/files/{self.id}/template/{self.template_image_path.split("/")[-1]}' if self.template_image_path and '/' in self.template_image_path else None,
            'template_image_path': self.template_image_path,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
        return data

    @staticmethod
    def from_dict(data):
        return Project(**data)
