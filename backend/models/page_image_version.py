"""
Page Image Version model - stores historical versions of generated images
"""
import uuid
from datetime import datetime


class PageImageVersion:
    """
    Page Image Version model - represents a historical version of a page's generated image
    """
    
    def __init__(self, id=None, page_id=None, user_id=None, image_path=None, 
                 version_number=1, is_current=False, created_at=None):
        self.id = id or str(uuid.uuid4())
        self.page_id = page_id
        self.user_id = user_id
        self.image_path = image_path
        self.version_number = version_number
        self.is_current = is_current
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self, project_id=None):
        """Convert to dictionary"""
        return {
            'version_id': self.id,
            'page_id': self.page_id,
            'user_id': self.user_id,
            'image_path': self.image_path,
            'image_url': f'/files/{project_id}/pages/{self.image_path.split("/")[-1]}' if self.image_path and project_id else None,
            'version_number': self.version_number,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }
    
    @staticmethod
    def from_dict(data):
        """Create from dictionary"""
        if not data:
            return None
            
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                pass
                
        return PageImageVersion(
            id=data.get('id') or data.get('version_id'),
            page_id=data.get('page_id'),
            user_id=data.get('user_id'),
            image_path=data.get('image_path'),
            version_number=data.get('version_number', 1),
            is_current=data.get('is_current', False),
            created_at=created_at
        )

    def __repr__(self):
        return f'<PageImageVersion {self.id}: page={self.page_id}, version={self.version_number}, current={self.is_current}>'
