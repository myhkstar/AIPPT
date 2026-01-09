"""
Reference File Controller - handles file upload and parsing
"""
import os
import logging
import re
import uuid
import threading
import tempfile
import shutil
from datetime import datetime
from urllib.parse import unquote
from pathlib import Path
from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename

from utils.response import (
    success_response, error_response, bad_request, not_found
)
from utils.auth import auth_required
from services.file_parser_service import FileParserService
from services.firestore_service import FirestoreService
from services.file_service import FileService

logger = logging.getLogger(__name__)

reference_file_bp = Blueprint('reference_file', __name__)
firestore_service = FirestoreService()


def _allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _get_file_type(filename: str) -> str:
    """Get file type from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return 'unknown'


def _parse_file_async(file_id: str, user_id: str, blob_path: str,
                      filename: str, config: dict):
    """
    Parse file asynchronously in background
    """
    try:
        # Update status to parsing
        firestore_service.update_reference_file(file_id, {
            'parse_status': 'parsing',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Download file from Firebase Storage to local temp path
        file_service = FileService()
        temp_dir = tempfile.mkdtemp()
        local_path = os.path.join(temp_dir, filename)

        blob = file_service.bucket.blob(blob_path)
        blob.download_to_filename(local_path)

        # Initialize parser service
        parser = FileParserService(
            mineru_token=config['MINERU_TOKEN'],
            mineru_api_base=config['MINERU_API_BASE'],
            google_api_key=config['GOOGLE_API_KEY'],
            google_api_base=config['GOOGLE_API_BASE'],
            image_caption_model=config['IMAGE_CAPTION_MODEL']
        )

        # Parse file
        logger.info(f"Starting to parse file: {filename}")
        batch_id, markdown_content, error_message, failed_image_count = \
            parser.parse_file(local_path, filename)

        # Update Firestore
        update_data = {
            'mineru_batch_id': batch_id,
            'updated_at': datetime.utcnow()
        }

        if error_message:
            update_data['parse_status'] = 'failed'
            update_data['error_message'] = error_message
            logger.error(f"File parsing failed: {error_message}")
        else:
            update_data['parse_status'] = 'completed'
            update_data['markdown_content'] = markdown_content
            if failed_image_count > 0:
                logger.warning(f"File parsing completed: {filename}, "
                               f"but {failed_image_count} images failed "
                               f"to generate captions")
            else:
                logger.info(f"File parsing completed: {filename}")

        firestore_service.update_reference_file(file_id, update_data, user_id)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"Error in async file parsing: {str(e)}", exc_info=True)
        try:
            firestore_service.update_reference_file(file_id, {
                'parse_status': 'failed',
                'error_message': f"Parsing error: {str(e)}",
                'updated_at': datetime.utcnow()
            }, user_id)
        except Exception as db_error:
            logger.error(f"Failed to update error status: {str(db_error)}")


@reference_file_bp.route('/upload', methods=['POST'])
@auth_required
def upload_reference_file():
    """
    POST /api/reference-files/upload - Upload a reference file
    """
    try:
        user_id = request.user_id

        # Check if file is in request
        if 'file' not in request.files:
            return bad_request("No file provided")

        file = request.files['file']

        # Get filename
        original_filename = file.filename
        if not original_filename or original_filename == '':
            content_disposition = request.headers.get('Content-Disposition', '')
            if content_disposition:
                filename_match = re.search(
                    r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)',
                    content_disposition
                )
                if filename_match:
                    original_filename = filename_match.group(1).strip('"\'')
                    try:
                        original_filename = unquote(original_filename)
                    except:
                        pass

        if not original_filename or original_filename == '':
            return bad_request("No file selected or filename "
                               "could not be determined")

        logger.info(f"Received file upload: {original_filename}")

        # Check file extension
        allowed_extensions = current_app.config.get(
            'ALLOWED_REFERENCE_FILE_EXTENSIONS',
            {'.pdf', '.docx', '.pptx', '.txt', '.md', '.xlsx', '.csv'}
        )
        if not _allowed_file(original_filename, allowed_extensions):
            return bad_request(f"File type not allowed. "
                               f"Allowed types: {', '.join(allowed_extensions)}")

        # Get project_id (optional)
        project_id = request.form.get('project_id')
        if project_id == 'none' or not project_id:
            project_id = None
        else:
            # Verify project exists
            project = firestore_service.get_project(project_id, user_id)
            if not project:
                return not_found('Project')

        # Secure filename
        filename = secure_filename(original_filename)
        if not filename or filename == '':
            ext = _get_file_type(original_filename)
            if ext == 'unknown':
                ext = 'file'
            filename = f"file_{uuid.uuid4().hex[:8]}.{ext}"

        # Save to Firebase Storage
        file_service = FileService()
        # Generate unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        unique_filename = f"{unique_id}_{filename}"

        if project_id:
            blob_path = f"projects/{project_id}/reference_files/{unique_filename}"
        else:
            blob_path = f"users/{user_id}/reference_files/{unique_filename}"

        blob = file_service.bucket.blob(blob_path)
        file.seek(0)
        blob.upload_from_file(file)

        file_size = blob.size
        file_type = _get_file_type(original_filename)

        # Create Firestore record
        ref_data = {
            'project_id': project_id,
            'user_id': user_id,
            'filename': original_filename,
            'file_path': blob_path,  # Use blob path as file_path
            'file_size': file_size,
            'file_type': file_type,
            'parse_status': 'pending'
        }

        ref_id = firestore_service.create_reference_file(ref_data, user_id)

        logger.info(f"File uploaded: {original_filename} (ID: {ref_id})")

        # Get updated record
        ref_file = firestore_service.get_reference_file(ref_id, user_id)

        return success_response({'file': ref_file})

    except Exception as e:
        logger.error(f"Error uploading reference file: {str(e)}",
                     exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@reference_file_bp.route('/<file_id>', methods=['GET'])
@auth_required
def get_reference_file(file_id):
    """
    GET /api/reference-files/<file_id> - Get reference file information
    """
    try:
        user_id = request.user_id
        reference_file = firestore_service.get_reference_file(file_id, user_id)
        if not reference_file:
            return not_found('Reference file')

        return success_response({'file': reference_file})

    except Exception as e:
        logger.error(f"Error getting reference file: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@reference_file_bp.route('/<file_id>', methods=['DELETE'])
@auth_required
def delete_reference_file(file_id):
    """
    DELETE /api/reference-files/<file_id> - Delete a reference file
    """
    try:
        user_id = request.user_id
        reference_file = firestore_service.get_reference_file(file_id, user_id)
        if not reference_file:
            return not_found('Reference file')

        # Delete from Storage
        file_service = FileService()
        blob_path = reference_file.get('file_path')
        if blob_path:
            blob = file_service.bucket.blob(blob_path)
            blob.delete()

        # Delete from Firestore
        firestore_service.db.collection('reference_files').document(file_id) \
            .delete()

        logger.info(f"Deleted reference file: {file_id}")

        return success_response({'message': 'File deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting reference file: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@reference_file_bp.route('/project/<project_id>', methods=['GET'])
@auth_required
def list_project_reference_files(project_id):
    """
    GET /api/reference-files/project/<project_id>
    """
    try:
        user_id = request.user_id
        if project_id == 'all':
            docs = firestore_service.db.collection('reference_files') \
                .where('user_id', '==', user_id).stream()
        elif project_id in ['global', 'none']:
            docs = firestore_service.db.collection('reference_files') \
                .where('user_id', '==', user_id) \
                .where('project_id', '==', None).stream()
        else:
            # Verify project exists
            project = firestore_service.get_project(project_id, user_id)
            if not project:
                return not_found('Project')

            docs = firestore_service.db.collection('reference_files') \
                .where('user_id', '==', user_id) \
                .where('project_id', '==', project_id).stream()

        files = [doc.to_dict() for doc in docs]

        return success_response({
            'files': files
        })

    except Exception as e:
        logger.error(f"Error listing reference files: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@reference_file_bp.route('/<file_id>/parse', methods=['POST'])
@auth_required
def trigger_file_parse(file_id):
    """
    POST /api/reference-files/<file_id>/parse
    """
    try:
        user_id = request.user_id
        reference_file = firestore_service.get_reference_file(file_id, user_id)
        if not reference_file:
            return not_found('Reference file')

        if reference_file.get('parse_status') == 'parsing':
            return success_response({
                'file': reference_file,
                'message': 'File is already being parsed'
            })

        # Update status to pending
        firestore_service.update_reference_file(file_id, {
            'parse_status': 'pending',
            'error_message': None,
            'markdown_content': None,
            'mineru_batch_id': None
        }, user_id)

        # Get config for background task
        config = {
            'MINERU_TOKEN': current_app.config.get('MINERU_TOKEN'),
            'MINERU_API_BASE': current_app.config.get('MINERU_API_BASE'),
            'GOOGLE_API_KEY': current_app.config.get('GOOGLE_API_KEY'),
            'GOOGLE_API_BASE': current_app.config.get('GOOGLE_API_BASE'),
            'IMAGE_CAPTION_MODEL': current_app.config.get('IMAGE_CAPTION_MODEL')
        }

        # Start async parsing
        thread = threading.Thread(
            target=_parse_file_async,
            args=(
                file_id,
                user_id,
                reference_file.get('file_path'),
                reference_file.get('filename'),
                config
            )
        )
        thread.daemon = True
        thread.start()

        logger.info(f"Triggered parsing for file: "
                    f"{reference_file.get('filename')} (ID: {file_id})")

        return success_response({
            'file': firestore_service.get_reference_file(file_id, user_id),
            'message': 'Parsing started'
        })

    except Exception as e:
        logger.error(f"Error triggering file parse: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@reference_file_bp.route('/<file_id>/associate', methods=['POST'])
@auth_required
def associate_file_to_project(file_id):
    """
    POST /api/reference-files/<file_id>/associate
    """
    try:
        user_id = request.user_id
        reference_file = firestore_service.get_reference_file(file_id, user_id)
        if not reference_file:
            return not_found('Reference file')

        data = request.get_json() or {}
        project_id = data.get('project_id')

        if not project_id:
            return bad_request("project_id is required")

        # Verify project exists
        project = firestore_service.get_project(project_id, user_id)
        if not project:
            return not_found('Project')

        # Update file's project_id
        firestore_service.update_reference_file(file_id, {
            'project_id': project_id
        }, user_id)

        logger.info(f"Associated reference file {file_id} to project {project_id}")

        return success_response({
            'file': firestore_service.get_reference_file(file_id, user_id)
        })

    except Exception as e:
        logger.error(f"Error associating reference file: {str(e)}",
                     exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@reference_file_bp.route('/<file_id>/dissociate', methods=['POST'])
@auth_required
def dissociate_file_from_project(file_id):
    """
    POST /api/reference-files/<file_id>/dissociate
    """
    try:
        user_id = request.user_id
        reference_file = firestore_service.get_reference_file(file_id, user_id)
        if not reference_file:
            return not_found('Reference file')

        # Remove project association
        firestore_service.update_reference_file(file_id, {
            'project_id': None
        }, user_id)

        logger.info(f"Dissociated reference file {file_id} from project")

        return success_response({
            'file': firestore_service.get_reference_file(file_id, user_id),
            'message': 'File removed from project'
        })

    except Exception as e:
        logger.error(f"Error dissociating reference file: {str(e)}",
                     exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)
