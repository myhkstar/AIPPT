"""
Page Controller - handles page-related endpoints
"""
import logging
import json
from datetime import datetime
from flask import Blueprint, request, current_app
from utils import success_response, error_response, not_found, bad_request
from utils.auth import auth_required
from services import AIService, FileService, ProjectContext
from services.firestore_service import FirestoreService
from services.task_manager import (
    task_manager, generate_single_page_image_task, edit_page_image_task
)

logger = logging.getLogger(__name__)

page_bp = Blueprint('pages', __name__, url_prefix='/api/projects')
firestore_service = FirestoreService()


def _create_ai_service_from_request(request_data: dict = None) -> AIService:
    """
    Create AI service instance from request data or fallback to environment config
    """
    text_config = None
    image_config = None

    # Try to get API config from request
    if request_data:
        api_config = request_data.get('api_config', {})

        # Extract text API config
        text_api = api_config.get('text_api')
        if text_api and text_api.get('enabled') and text_api.get('api_key'):
            text_config = {
                'provider': text_api.get('provider', 'google'),
                'api_key': text_api.get('api_key'),
                'base_url': text_api.get('base_url'),
                'model': text_api.get('model'),
                'max_tokens': text_api.get('max_tokens'),
                'temperature': text_api.get('temperature'),
            }

        # Extract image API config
        image_api = api_config.get('image_api')
        if image_api and image_api.get('enabled') and image_api.get('api_key'):
            image_config = {
                'provider': image_api.get('provider', 'google'),
                'api_key': image_api.get('api_key'),
                'base_url': image_api.get('base_url'),
                'model': image_api.get('model'),
                'aspect_ratio': image_api.get('aspect_ratio'),
                'resolution': image_api.get('resolution'),
                'style': image_api.get('style'),
            }

    # Fallback to environment config if no API config provided
    if not text_config:
        google_api_key = current_app.config.get('GOOGLE_API_KEY')
        google_api_base = current_app.config.get('GOOGLE_API_BASE')

        if google_api_key:
            text_config = {
                'provider': 'google',
                'api_key': google_api_key,
                'base_url': google_api_base,
                'model': 'gemini-2.5-flash',
            }

    if not image_config:
        google_api_key = current_app.config.get('GOOGLE_API_KEY')
        google_api_base = current_app.config.get('GOOGLE_API_BASE')

        if google_api_key:
            image_config = {
                'provider': 'google',
                'api_key': google_api_key,
                'base_url': google_api_base,
                'model': 'gemini-3-pro-image-preview',
                'aspect_ratio': '16:9',
                'resolution': '2K',
            }

    return AIService(text_config=text_config, image_config=image_config)


@page_bp.route('/<project_id>/pages', methods=['POST'])
@auth_required
def create_page(project_id):
    """
    POST /api/projects/{project_id}/pages - Add new page
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        data = request.get_json()

        if not data or 'order_index' not in data:
            return bad_request("order_index is required")

        # Create new page data
        page_data = {
            'project_id': project_id,
            'order_index': data['order_index'],
            'part': data.get('part'),
            'outline_content': data.get('outline_content'),
            'status': 'DRAFT'
        }

        page_id = firestore_service.create_page(project_id, page_data, user_id)

        # Update other pages' order_index if necessary
        pages = firestore_service.get_pages(project_id, user_id)
        for p in pages:
            if p['id'] != page_id and p['order_index'] >= data['order_index']:
                firestore_service.update_page(
                    project_id, p['id'],
                    {'order_index': p['order_index'] + 1},
                    user_id
                )

        firestore_service.update_project(project_id, {}, user_id)

        # Get updated page
        page = firestore_service.get_page(project_id, page_id, user_id)
        return success_response(page, status_code=201)

    except Exception as e:
        logger.error(f"create_page failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@page_bp.route('/<project_id>/pages/<page_id>', methods=['DELETE'])
@auth_required
def delete_page(project_id, page_id):
    """
    DELETE /api/projects/{project_id}/pages/{page_id} - Delete page
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        # Delete page image if exists
        file_service = FileService()
        file_service.delete_page_image(project_id, page_id)

        # Delete page
        firestore_service.delete_page(project_id, page_id, user_id)

        # Update project
        firestore_service.update_project(project_id, {}, user_id)

        return success_response(message="Page deleted successfully")

    except Exception as e:
        logger.error(f"delete_page failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@page_bp.route('/<project_id>/pages/<page_id>/outline', methods=['PUT'])
@auth_required
def update_page_outline(project_id, page_id):
    """
    PUT /api/projects/{project_id}/pages/{page_id}/outline - Edit page outline
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        data = request.get_json()

        if not data or 'outline_content' not in data:
            return bad_request("outline_content is required")

        firestore_service.update_page(project_id, page_id, {
            'outline_content': data['outline_content']
        }, user_id)

        # Update project
        firestore_service.update_project(project_id, {}, user_id)

        # Get updated page
        page = firestore_service.get_page(project_id, page_id, user_id)
        return success_response(page)

    except Exception as e:
        logger.error(f"update_page_outline failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@page_bp.route('/<project_id>/pages/<page_id>/description', methods=['PUT'])
@auth_required
def update_page_description(project_id, page_id):
    """
    PUT /api/projects/{project_id}/pages/{page_id}/description - Edit description
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        data = request.get_json()

        if not data or 'description_content' not in data:
            return bad_request("description_content is required")

        firestore_service.update_page(project_id, page_id, {
            'description_content': data['description_content']
        }, user_id)

        # Update project
        firestore_service.update_project(project_id, {}, user_id)

        # Get updated page
        page = firestore_service.get_page(project_id, page_id, user_id)
        return success_response(page)

    except Exception as e:
        logger.error(f"update_page_description failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@page_bp.route('/<project_id>/pages/<page_id>/generate/description',
               methods=['POST'])
@auth_required
def generate_page_description(project_id, page_id):
    """
    POST /api/projects/{project_id}/pages/{page_id}/generate/description
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        project = firestore_service.get_project(project_id, user_id)
        if not project:
            return not_found('Project')

        data = request.get_json() or {}
        force_regenerate = data.get('force_regenerate', False)

        # Check if already generated
        if page.get('description_content') and not force_regenerate:
            return bad_request("Description already exists. "
                               "Set force_regenerate=true to regenerate")

        # Get outline content
        outline_content = page.get('outline_content')
        if not outline_content:
            return bad_request("Page must have outline content first")

        # Reconstruct full outline
        all_pages = firestore_service.get_pages(project_id, user_id)
        outline = []
        for p in all_pages:
            oc = p.get('outline_content')
            if oc:
                p_data = oc.copy()
                if p.get('part'):
                    p_data['part'] = p.get('part')
                outline.append(p_data)

        # Initialize AI service
        ai_service = _create_ai_service_from_request(data)

        # Get reference files content and create project context
        from controllers.project_controller import (
            _get_project_reference_files_content
        )
        ref_files_content = _get_project_reference_files_content(
            project_id, user_id
        )
        project_context = ProjectContext(project, ref_files_content)

        # Generate description
        page_data = outline_content.copy()
        if page.get('part'):
            page_data['part'] = page.get('part')

        desc_text = ai_service.generate_page_description(
            project_context,
            outline,
            page_data,
            page.get('order_index', 0) + 1
        )

        # Save description
        desc_content = {
            "text": desc_text,
            "generated_at": datetime.utcnow().isoformat()
        }

        firestore_service.update_page(project_id, page_id, {
            'description_content': desc_content,
            'status': 'DESCRIPTION_GENERATED'
        }, user_id)

        # Get updated page
        page = firestore_service.get_page(project_id, page_id, user_id)
        return success_response(page)

    except Exception as e:
        logger.error(f"generate_page_description failed: {str(e)}",
                     exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@page_bp.route('/<project_id>/pages/<page_id>/generate/image',
               methods=['POST'])
@auth_required
def generate_page_image(project_id, page_id):
    """
    POST /api/projects/{project_id}/pages/{page_id}/generate/image
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        project = firestore_service.get_project(project_id, user_id)
        if not project:
            return not_found('Project')

        data = request.get_json() or {}
        use_template = data.get('use_template', True)
        force_regenerate = data.get('force_regenerate', False)

        # Check if already generated
        if page.get('generated_image_path') and not force_regenerate:
            return bad_request("Image already exists. "
                               "Set force_regenerate=true to regenerate")

        # Get description content
        desc_content = page.get('description_content')
        if not desc_content:
            return bad_request("Page must have description content first")

        # Reconstruct full outline with part structure
        all_pages = firestore_service.get_pages(project_id, user_id)
        outline = []
        current_part = None
        current_part_pages = []

        for p in all_pages:
            oc = p.get('outline_content')
            if not oc:
                continue

            p_data = oc.copy()

            if p.get('part'):
                if current_part and current_part != p.get('part'):
                    outline.append({
                        "part": current_part,
                        "pages": current_part_pages
                    })
                    current_part_pages = []

                current_part = p.get('part')
                if 'part' in p_data:
                    del p_data['part']
                current_part_pages.append(p_data)
            else:
                if current_part:
                    outline.append({
                        "part": current_part,
                        "pages": current_part_pages
                    })
                    current_part = None
                    current_part_pages = []

                outline.append(p_data)

        if current_part:
            outline.append({
                "part": current_part,
                "pages": current_part_pages
            })

        # Initialize services
        ai_service = _create_ai_service_from_request(data)
        file_service = FileService()

        # Create async task
        task_data = {
            'project_id': project_id,
            'task_type': 'GENERATE_PAGE_IMAGE',
            'status': 'PENDING',
            'progress': {
                'total': 1,
                'completed': 0,
                'failed': 0
            }
        }
        task_id = firestore_service.create_task(project_id, task_data, user_id)

        # Submit background task
        task_manager.submit_task(
            task_id,
            generate_single_page_image_task,
            project_id,
            page_id,
            user_id,
            ai_service,
            file_service,
            outline,
            use_template,
            current_app.config.get('DEFAULT_ASPECT_RATIO', '16:9'),
            current_app.config.get('DEFAULT_RESOLUTION', '2K'),
            project.get('extra_requirements')
        )

        return success_response({
            'task_id': task_id,
            'page_id': page_id,
            'status': 'PENDING'
        }, status_code=202)

    except Exception as e:
        logger.error(f"generate_page_image failed: {str(e)}", exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@page_bp.route('/<project_id>/pages/<page_id>/edit/image', methods=['POST'])
@auth_required
def edit_page_image_route(project_id, page_id):
    """
    POST /api/projects/{project_id}/pages/<page_id>/edit/image
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        if not page.get('generated_image_path'):
            return bad_request("Page must have generated image first")

        # Parse request data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        if not data or 'edit_instruction' not in data:
            return bad_request("edit_instruction is required")

        ai_service = _create_ai_service_from_request(data)
        file_service = FileService()

        # Create async task
        task_data = {
            'project_id': project_id,
            'task_type': 'EDIT_PAGE_IMAGE',
            'status': 'PENDING',
            'progress': {
                'total': 1,
                'completed': 0,
                'failed': 0
            }
        }
        task_id = firestore_service.create_task(project_id, task_data, user_id)

        # Submit background task
        task_manager.submit_task(
            task_id,
            edit_page_image_task,
            project_id,
            page_id,
            user_id,
            ai_service,
            file_service,
            data['edit_instruction'],
            current_app.config.get('DEFAULT_ASPECT_RATIO', '16:9'),
            current_app.config.get('DEFAULT_RESOLUTION', '2K')
        )

        return success_response({
            'task_id': task_id,
            'page_id': page_id,
            'status': 'PENDING'
        }, status_code=202)

    except Exception as e:
        logger.error(f"edit_page_image failed: {str(e)}", exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@page_bp.route('/<project_id>/pages/<page_id>/image-versions', methods=['GET'])
@auth_required
def get_page_image_versions(project_id, page_id):
    """
    GET /api/projects/{project_id}/pages/{page_id}/image-versions
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        versions = firestore_service.list_page_image_versions(page_id, user_id)

        return success_response({
            'versions': versions
        })

    except Exception as e:
        logger.error(f"get_page_image_versions failed: {str(e)}",
                     exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@page_bp.route('/<project_id>/pages/<page_id>/image-versions/<version_id>/'
               'set-current', methods=['POST'])
@auth_required
def set_current_image_version(project_id, page_id, version_id):
    """
    POST /api/projects/{project_id}/pages/{page_id}/image-versions/
    {version_id}/set-current
    """
    try:
        user_id = request.user_id
        page = firestore_service.get_page(project_id, page_id, user_id)

        if not page:
            return not_found('Page')

        # Set this version as current
        firestore_service.set_current_page_image_version(
            page_id, version_id, user_id
        )

        # Update page path
        versions = firestore_service.list_page_image_versions(page_id, user_id)
        target_version = next(
            (v for v in versions if v['id'] == version_id), None
        )

        if target_version:
            firestore_service.update_page(project_id, page_id, {
                'generated_image_path': target_version['image_path']
            }, user_id)

        # Get updated page
        page = firestore_service.get_page(project_id, page_id, user_id)
        return success_response(page)

    except Exception as e:
        logger.error(f"set_current_image_version failed: {str(e)}",
                     exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)
