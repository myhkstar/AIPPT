"""
Material Controller - handles standalone material image generation
"""
import logging
from flask import Blueprint, request, current_app
from utils import success_response, error_response, not_found, bad_request
from utils.auth_middleware import auth_required
from services import AIService, FileService
from services.firestore_service import FirestoreService
from services.task_manager import task_manager, generate_material_image_task
from pathlib import Path
from werkzeug.utils import secure_filename
import tempfile
import shutil

logger = logging.getLogger(__name__)

material_bp = Blueprint('materials', __name__, url_prefix='/api/projects')
material_global_bp = Blueprint(
    'materials_global', __name__, url_prefix='/api/materials'
)


class LazyFirestoreService:
    def __init__(self):
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = FirestoreService()
        return self._service

    def __getattr__(self, name):
        return getattr(self.service, name)


firestore_service = LazyFirestoreService()

ALLOWED_MATERIAL_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'
}


def _get_materials_list(filter_project_id: str, user_id: str):
    """
    Common logic to get materials list.
    """
    if filter_project_id == 'all':
        # Firestore doesn't support easy "all or specific" without separate
        # queries or complex logic if we want to filter by user_id
        # For now, we'll just get all for the user
        materials = firestore_service.db.collection('materials') \
            .where('user_id', '==', user_id).stream()
    elif filter_project_id == 'none':
        materials = firestore_service.db.collection('materials') \
            .where('user_id', '==', user_id) \
            .where('project_id', '==', None).stream()
    else:
        # Verify project ownership
        project = firestore_service.get_project(filter_project_id, user_id)
        if not project:
            return None, not_found('Project')

        materials = firestore_service.db.collection('materials') \
            .where('user_id', '==', user_id) \
            .where('project_id', '==', filter_project_id).stream()

    materials_list = [doc.to_dict() for doc in materials]
    # Sort by created_at descending (Firestore stream doesn't guarantee order
    # if not indexed)
    materials_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return materials_list, None


@material_bp.route('/<project_id>/materials/generate', methods=['POST'])
@auth_required
def generate_material_image(project_id):
    """
    POST /api/projects/{project_id}/materials/generate
    """
    try:
        user_id = request.user_id
        # 支持 'none' 作为特殊值，表示生成全局素材
        if project_id != 'none':
            project = firestore_service.get_project(project_id, user_id)
            if not project:
                return not_found('Project')
        else:
            project = None
            project_id = None  # 设置为None表示全局素材

        # Parse request data
        if request.is_json:
            data = request.get_json() or {}
            prompt = data.get('prompt', '').strip()
            ref_file = None
            extra_files = []
        else:
            data = request.form.to_dict()
            prompt = (data.get('prompt') or '').strip()
            ref_file = request.files.get('ref_image')
            extra_files = request.files.getlist('extra_images') or []

        if not prompt:
            return bad_request("prompt is required")

        # Initialize services
        ai_service = AIService()
        file_service = FileService()

        # Create temporary directory for reference images
        temp_dir = Path(tempfile.mkdtemp())
        temp_dir_str = str(temp_dir)

        try:
            ref_path = None
            if ref_file and ref_file.filename:
                ref_filename = secure_filename(ref_file.filename)
                ref_path = temp_dir / ref_filename
                ref_file.save(str(ref_path))
                ref_path_str = str(ref_path)
            else:
                ref_path_str = None

            additional_ref_images = []
            for extra in extra_files:
                if not extra or not extra.filename:
                    continue
                extra_filename = secure_filename(extra.filename)
                extra_path = temp_dir / extra_filename
                extra.save(str(extra_path))
                additional_ref_images.append(str(extra_path))

            # Create async task
            task_project_id = project_id if project_id else 'global'
            task_data = {
                'project_id': task_project_id,
                'task_type': 'GENERATE_MATERIAL',
                'status': 'PENDING',
                'progress': {'total': 1, 'completed': 0, 'failed': 0}
            }
            task_id = firestore_service.create_task(
                task_project_id, task_data, user_id
            )

            # Submit background task
            task_manager.submit_task(
                task_id,
                generate_material_image_task,
                task_project_id,
                user_id,
                ai_service,
                file_service,
                prompt,
                ref_path_str,
                additional_ref_images if additional_ref_images else None,
                current_app.config.get('DEFAULT_ASPECT_RATIO', '16:9'),
                current_app.config.get('DEFAULT_RESOLUTION', '2K'),
                temp_dir_str
            )

            return success_response({
                'task_id': task_id,
                'status': 'PENDING'
            }, status_code=202)

        except Exception as e:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    except Exception as e:
        logger.error(f"generate_material_image failed: {str(e)}",
                     exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@material_bp.route('/<project_id>/materials', methods=['GET'])
@auth_required
def list_materials(project_id):
    """
    GET /api/projects/{project_id}/materials
    """
    try:
        user_id = request.user_id
        materials_list, error = _get_materials_list(project_id, user_id)
        if error:
            return error

        return success_response({
            "materials": materials_list,
            "count": len(materials_list)
        })

    except Exception as e:
        logger.error(f"list_materials failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@material_bp.route('/<project_id>/materials/upload', methods=['POST'])
@auth_required
def upload_material(project_id):
    """
    POST /api/projects/{project_id}/materials/upload
    """
    try:
        user_id = request.user_id
        if project_id != 'none':
            project = firestore_service.get_project(project_id, user_id)
            if not project:
                return not_found('Project')
        else:
            project_id = None

        file = request.files.get('file')
        if not file or not file.filename:
            return bad_request("file is required")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_MATERIAL_EXTENSIONS:
            return bad_request("Unsupported file type")

        file_service = FileService()
        blob_path = file_service.save_material_file(file, project_id)
        url = file_service.get_file_url(
            project_id, "materials", blob_path.split('/')[-1]
        )

        material_data = {
            'project_id': project_id,
            'user_id': user_id,
            'filename': secure_filename(file.filename),
            'relative_path': blob_path,
            'url': url
        }
        material_id = firestore_service.create_material(
            material_data, user_id
        )

        # Get updated material
        material = firestore_service.get_material(material_id, user_id)
        return success_response(material, status_code=201)

    except Exception as e:
        logger.error(f"upload_material failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@material_global_bp.route('', methods=['GET'])
@auth_required
def list_all_materials():
    """
    GET /api/materials
    """
    try:
        user_id = request.user_id
        filter_project_id = request.args.get('project_id', 'all')
        materials_list, error = _get_materials_list(
            filter_project_id, user_id
        )
        if error:
            return error

        return success_response({
            "materials": materials_list,
            "count": len(materials_list)
        })

    except Exception as e:
        logger.error(f"list_all_materials failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@material_global_bp.route('/upload', methods=['POST'])
@auth_required
def upload_material_global():
    """
    POST /api/materials/upload
    """
    return upload_material('none')


@material_global_bp.route('/<material_id>', methods=['DELETE'])
@auth_required
def delete_material(material_id):
    """
    DELETE /api/materials/{material_id}
    """
    try:
        user_id = request.user_id
        material = firestore_service.get_material(material_id, user_id)
        if not material:
            return not_found('Material')

        # Delete from Storage
        file_service = FileService()
        # In Firebase version, relative_path is the blob path
        blob_path = material.get('relative_path')
        if blob_path:
            blob = file_service.bucket.blob(blob_path)
            blob.delete()

        # Delete from Firestore
        firestore_service.db.collection('materials').document(material_id) \
            .delete()

        return success_response({"id": material_id})
    except Exception as e:
        logger.error(f"delete_material failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)
