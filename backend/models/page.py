"""
Page model - converted to plain Python class for Firestore
"""
import uuid
import json
from datetime import datetime

class Page:
    """
    Page model - represents a single PPT page/slide
    """
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.project_id = kwargs.get('project_id')
        self.order_index = kwargs.get('order_index', 0)
        self.part = kwargs.get('part')
        self.outline_content = kwargs.get('outline_content')
        self.description_content = kwargs.get('description_content')
        self.generated_image_path = kwargs.get('generated_image_path')
        self.status = kwargs.get('status', 'DRAFT')
        
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
        image_filename = None
        if self.generated_image_path:
            import os
            image_filename = os.path.basename(self.generated_image_path.replace('\\', '/'))
        
        data = {
            'page_id': self.id,
            'id': self.id,
            'project_id': self.project_id,
            'order_index': self.order_index,
            'part': self.part,
            'outline_content': self.outline_content,
            'description_content': self.description_content,
            'generated_image_url': f'/files/{self.project_id}/pages/{image_filename}' if image_filename else None,
            'generated_image_path': self.generated_image_path,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
        return data

    @staticmethod
    def from_dict(data):
        return Page(**data)
