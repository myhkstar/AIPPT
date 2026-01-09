"""
Material model - stores material images
"""
import uuid
from datetime import datetime


class Material:
    """
    Material model - represents a material image
    """
    
    def __init__(self, id=None, project_id=None, user_id=None, filename=None, 
                 relative_path=None, url=None, created_at=None, updated_at=None):
        self.id = id or str(uuid.uuid4())
        self.project_id = project_id
        self.user_id = user_id
        self.filename = filename
        self.relative_path = relative_path
        self.url = url
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'filename': self.filename,
            'url': self.url,
            'relative_path': self.relative_path,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
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
                
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                pass
                
        return Material(
            id=data.get('id'),
            project_id=data.get('project_id'),
            user_id=data.get('user_id'),
            filename=data.get('filename'),
            relative_path=data.get('relative_path'),
            url=data.get('url'),
            created_at=created_at,
            updated_at=updated_at
        )

    def __repr__(self):
        return f'<Material {self.id}: {self.filename} (project={self.project_id or "None"})>'
