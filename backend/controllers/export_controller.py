"""
Export Controller - handles file export endpoints
"""
import os
import logging
import tempfile
import shutil
from flask import Blueprint, request, current_app
from utils import error_response, not_found, bad_request, success_response
from utils.auth import auth_required
from services import ExportService, FileService
from services.firestore_service import FirestoreService

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/api/projects')
firestore_service = FirestoreService()


@export_bp.route('/<project_id>/export/pptx', methods=['GET'])
@auth_required
def export_pptx(project_id):
    """
    GET /api/projects/{project_id}/export/pptx?filename=... - Export PPTX
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        # Get all pages
        pages = firestore_service.get_pages(project_id, user_id)

        if not pages:
            return bad_request("No pages found for project")

        # Initialize file service
        file_service = FileService()

        # Create temp directory for images and output
        temp_dir = tempfile.mkdtemp()
        try:
            image_paths = []
            for page in pages:
                blob_path = page.get('generated_image_path')
                if blob_path:
                    # Download image to temp path
                    filename = blob_path.split('/')[-1]
                    local_img_path = os.path.join(temp_dir, filename)
                    blob = file_service.bucket.blob(blob_path)
                    blob.download_to_filename(local_img_path)
                    image_paths.append(local_img_path)

            if not image_paths:
                return bad_request("No generated images found for project")

            # Get filename
            filename = request.args.get(
                'filename', f'presentation_{project_id}.pptx'
            )
            if not filename.endswith('.pptx'):
                filename += '.pptx'

            output_path = os.path.join(temp_dir, filename)

            # Generate PPTX file
            ExportService.create_pptx_from_images(
                image_paths, output_file=output_path
            )

            # Upload to Firebase Storage
            export_blob_path = f"projects/{project_id}/exports/{filename}"
            blob = file_service.bucket.blob(export_blob_path)
            blob.upload_from_filename(output_path)

            # Get signed URL
            url = file_service.get_file_url(project_id, "exports", filename)

            return success_response(
                data={
                    "download_url": url,
                    "download_url_absolute": url,
                },
                message="Export PPTX completed"
            )

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"export_pptx failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/export/pdf', methods=['GET'])
@auth_required
def export_pdf(project_id):
    """
    GET /api/projects/{project_id}/export/pdf?filename=... - Export PDF
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        # Get all pages
        pages = firestore_service.get_pages(project_id, user_id)

        if not pages:
            return bad_request("No pages found for project")

        # Initialize file service
        file_service = FileService()

        # Create temp directory for images and output
        temp_dir = tempfile.mkdtemp()
        try:
            image_paths = []
            for page in pages:
                blob_path = page.get('generated_image_path')
                if blob_path:
                    # Download image to temp path
                    filename = blob_path.split('/')[-1]
                    local_img_path = os.path.join(temp_dir, filename)
                    blob = file_service.bucket.blob(blob_path)
                    blob.download_to_filename(local_img_path)
                    image_paths.append(local_img_path)

            if not image_paths:
                return bad_request("No generated images found for project")

            # Get filename
            filename = request.args.get(
                'filename', f'presentation_{project_id}.pdf'
            )
            if not filename.endswith('.pdf'):
                filename += '.pdf'

            output_path = os.path.join(temp_dir, filename)

            # Generate PDF file
            ExportService.create_pdf_from_images(
                image_paths, output_file=output_path
            )

            # Upload to Firebase Storage
            export_blob_path = f"projects/{project_id}/exports/{filename}"
            blob = file_service.bucket.blob(export_blob_path)
            blob.upload_from_filename(output_path)

            # Get signed URL
            url = file_service.get_file_url(project_id, "exports", filename)

            return success_response(
                data={
                    "download_url": url,
                    "download_url_absolute": url,
                },
                message="Export PDF completed"
            )

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"export_pdf failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)
