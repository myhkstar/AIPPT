"""
Reference File model - converted to plain Python class for Firestore
"""
import uuid
from datetime import datetime

class ReferenceFile:
    """
    Reference File model - represents an uploaded reference file
    """
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.project_id = kwargs.get('project_id')
        self.user_id = kwargs.get('user_id')
        self.filename = kwargs.get('filename')
        self.file_path = kwargs.get('file_path')
        self.file_size = kwargs.get('file_size', 0)
        self.file_type = kwargs.get('file_type')
        self.parse_status = kwargs.get('parse_status', 'pending')
        self.markdown_content = kwargs.get('markdown_content')
        self.error_message = kwargs.get('error_message')
        self.mineru_batch_id = kwargs.get('mineru_batch_id')
        
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

    def to_dict(self, include_content=True):
        """Convert to dictionary for Firestore/JSON"""
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'parse_status': self.parse_status,
            'error_message': self.error_message,
            'mineru_batch_id': self.mineru_batch_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
        
        if include_content:
            result['markdown_content'] = self.markdown_content
            
        return result

    @staticmethod
    def from_dict(data):
        return ReferenceFile(**data)
