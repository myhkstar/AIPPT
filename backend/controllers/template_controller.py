"""
Template Controller - handles template-related endpoints
"""
import logging
from flask import Blueprint, request, current_app
from utils import (
    success_response, error_response, not_found, bad_request, allowed_file
)
from utils.auth import auth_required
from services import FileService
from services.firestore_service import FirestoreService
from datetime import datetime

logger = logging.getLogger(__name__)

template_bp = Blueprint('templates', __name__, url_prefix='/api/projects')
user_template_bp = Blueprint(
    'user_templates', __name__, url_prefix='/api/user-templates'
)
firestore_service = FirestoreService()


@template_bp.route('/<project_id>/template', methods=['POST'])
@auth_required
def upload_template(project_id):
    """
    POST /api/projects/{project_id}/template - Upload template image
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        # Check if file is in request
        if 'template_image' not in request.files:
            return bad_request("No file uploaded")

        file = request.files['template_image']

        if file.filename == '':
            return bad_request("No file selected")

        # Validate file extension
        allowed_exts = current_app.config.get(
            'ALLOWED_EXTENSIONS',
            {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        )
        if not allowed_file(file.filename, allowed_exts):
            return bad_request("Invalid file type. "
                               "Allowed types: png, jpg, jpeg, gif, webp")

        # Save template
        file_service = FileService()
        file_path = file_service.save_template_image(file, project_id)

        # Update project
        firestore_service.update_project(project_id, {
            'template_image_path': file_path
        }, user_id)

        # Get filename for URL
        filename = file_path.split('/')[-1]
        url = file_service.get_file_url(project_id, "template", filename)

        return success_response({
            'template_image_url': url
        })

    except Exception as e:
        logger.error(f"upload_template failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@template_bp.route('/<project_id>/template', methods=['DELETE'])
@auth_required
def delete_template(project_id):
    """
    DELETE /api/projects/{project_id}/template - Delete template
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        if not project.get('template_image_path'):
            return bad_request("No template to delete")

        # Delete template file
        file_service = FileService()
        file_service.delete_template(project_id)

        # Update project
        firestore_service.update_project(project_id, {
            'template_image_path': None
        }, user_id)

        return success_response(message="Template deleted successfully")

    except Exception as e:
        logger.error(f"delete_template failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@template_bp.route('/templates', methods=['GET'])
@auth_required
def get_system_templates():
    """
    GET /api/templates - Get system preset templates
    """
    # TODO: Implement system templates in Firestore
    templates = []

    return success_response({
        'templates': templates
    })


# ========== User Template Endpoints ==========

@user_template_bp.route('', methods=['POST'])
@auth_required
def upload_user_template():
    """
    POST /api/user-templates - Upload user template image
    """
    try:
        user_id = request.user_id

        # Check if file is in request
        if 'template_image' not in request.files:
            return bad_request("No file uploaded")

        file = request.files['template_image']

        if file.filename == '':
            return bad_request("No file selected")

        # Validate file extension
        allowed_exts = current_app.config.get(
            'ALLOWED_EXTENSIONS',
            {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        )
        if not allowed_file(file.filename, allowed_exts):
            return bad_request("Invalid file type. "
                               "Allowed types: png, jpg, jpeg, gif, webp")

        # Get optional name
        name = request.form.get('name', None)

        # Get file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        # Generate template ID
        import uuid
        template_id = str(uuid.uuid4())

        # Save template file
        file_service = FileService()
        file_path = file_service.save_user_template(file, template_id)

        # Create template record
        template_data = {
            'id': template_id,
            'user_id': user_id,
            'name': name,
            'file_path': file_path,
            'file_size': file_size
        }
        firestore_service.create_user_template(template_data, user_id)

        # Get updated record
        template = firestore_service.get_user_template(template_id, user_id)

        return success_response(template)

    except Exception as e:
        logger.error(f"upload_user_template failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@user_template_bp.route('', methods=['GET'])
@auth_required
def list_user_templates():
    """
    GET /api/user-templates - Get list of user templates
    """
    try:
        user_id = request.user_id
        templates = firestore_service.list_user_templates(user_id)

        return success_response({
            'templates': templates
        })

    except Exception as e:
        logger.error(f"list_user_templates failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@user_template_bp.route('/<template_id>', methods=['DELETE'])
@auth_required
def delete_user_template(template_id):
    """
    DELETE /api/user-templates/{template_id} - Delete user template
    """
    try:
        user_id = request.user_id
        template = firestore_service.get_user_template(template_id, user_id)

        if not template:
            return not_found('UserTemplate')

        # Delete template file
        file_service = FileService()
        file_service.delete_user_template(template_id)

        # Delete template record
        firestore_service.delete_user_template(template_id, user_id)

        return success_response(message="Template deleted successfully")

    except Exception as e:
        logger.error(f"delete_user_template failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)
