"""
File Service - handles all file operations using Firebase Storage
"""
import os
import io
from pathlib import Path
from typing import Optional
from werkzeug.utils import secure_filename
from PIL import Image
from firebase_config import get_firebase
import logging

class FileService:
    """Service for file management using Firebase Storage"""
    
    def __init__(self, upload_folder: str = None):
        """Initialize file service"""
        # upload_folder is kept for compatibility but we use Firebase
        _, self.bucket = get_firebase()
    
    def _get_blob_path(self, project_id: str, file_type: str, filename: str) -> str:
        """Get blob path in Firebase Storage"""
        return f"projects/{project_id}/{file_type}/{filename}"
    
    def save_template_image(self, file, project_id: str) -> str:
        """Save template image to Firebase Storage"""
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
        filename = f"template.{ext}"
        blob_path = self._get_blob_path(project_id, "template", filename)
        
        blob = self.bucket.blob(blob_path)
        # Upload from file stream
        file.seek(0)
        blob.upload_from_file(file, content_type=f"image/{ext}")
        
        return blob_path
    
    def save_generated_image(self, image: Image.Image, project_id: str, 
                           page_id: str, image_format: str = 'PNG', 
                           version_number: int = None) -> str:
        """Save generated image to Firebase Storage"""
        ext = image_format.lower()
        if version_number is not None:
            filename = f"{page_id}_v{version_number}.{ext}"
        else:
            import time
            timestamp = int(time.time() * 1000)
            filename = f"{page_id}_{timestamp}.{ext}"
            
        blob_path = self._get_blob_path(project_id, "pages", filename)
        blob = self.bucket.blob(blob_path)
        
        # Save PIL image to byte stream
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image_format)
        img_byte_arr.seek(0)
        
        blob.upload_from_file(img_byte_arr, content_type=f"image/{ext}")
        
        return blob_path

    def save_material_image(self, image: Image.Image, project_id: Optional[str],
                              image_format: str = 'PNG') -> str:
        """Save material image to Firebase Storage from PIL Image"""
        ext = image_format.lower()
        import time
        timestamp = int(time.time() * 1000)
        filename = f"material_{timestamp}.{ext}"

        if project_id:
            blob_path = self._get_blob_path(project_id, "materials", filename)
        else:
            blob_path = f"global_materials/{filename}"

        blob = self.bucket.blob(blob_path)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image_format)
        img_byte_arr.seek(0)

        blob.upload_from_file(img_byte_arr, content_type=f"image/{ext}")

        return blob_path

    def save_material_file(self, file, project_id: Optional[str]) -> str:
        """Save material file to Firebase Storage from file stream"""
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'

        import time
        timestamp = int(time.time() * 1000)
        filename = f"material_{timestamp}.{ext}"

        if project_id:
            blob_path = self._get_blob_path(project_id, "materials", filename)
        else:
            blob_path = f"global_materials/{filename}"

        blob = self.bucket.blob(blob_path)
        file.seek(0)
        blob.upload_from_file(file, content_type=f"image/{ext}")

        return blob_path
    
    def get_file_url(self, project_id: Optional[str], file_type: str, filename: str) -> str:
        """Generate signed URL for frontend access"""
        if project_id:
            blob_path = self._get_blob_path(project_id, file_type, filename)
        else:
            blob_path = f"global_materials/{filename}"
            
        blob = self.bucket.blob(blob_path)
        # Generate a signed URL that expires in 1 hour
        return blob.generate_signed_url(expiration=3600)
    
    def delete_project_files(self, project_id: str) -> bool:
        """Delete all files for a project in Firebase Storage"""
        prefix = f"projects/{project_id}/"
        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()
        return True

    def delete_template(self, project_id: str) -> bool:
        """Delete template for project"""
        prefix = f"projects/{project_id}/template/"
        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()
        return True

    def delete_page_image(self, project_id: str, page_id: str) -> bool:
        """Delete page image"""
        prefix = f"projects/{project_id}/pages/{page_id}"
        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()
        return True

    def save_user_template(self, file, template_id: str) -> str:
        """Save user template to Firebase Storage"""
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
        filename = f"template.{ext}"
        blob_path = f"user-templates/{template_id}/{filename}"
        
        blob = self.bucket.blob(blob_path)
        file.seek(0)
        blob.upload_from_file(file, content_type=f"image/{ext}")
        
        return blob_path

    def delete_user_template(self, template_id: str) -> bool:
        """Delete user template"""
        prefix = f"user-templates/{template_id}/"
        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()
        return True

    def get_absolute_path(self, relative_path: str) -> str:
        """
        Firebase Storage doesn't have absolute local paths.
        This might be used for temporary file processing.
        We'll return a placeholder or download to a temp file if needed.
        """
        # For now, return the relative path (blob path)
        return relative_path

    def file_exists(self, blob_path: str) -> bool:
        """Check if blob exists"""
        blob = self.bucket.blob(blob_path)
        return blob.exists()
