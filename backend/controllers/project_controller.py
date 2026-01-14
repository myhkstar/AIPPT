"""
Project Controller - handles project-related endpoints
"""
import logging
import os
import uuid
from flask import Blueprint, request, current_app
from utils import success_response, error_response, not_found, bad_request
from utils.auth_middleware import auth_required
from services import AIService, ProjectContext
from services.firestore_service import FirestoreService
from services.task_manager import (
    task_manager,
    generate_descriptions_task,
    generate_images_task
)
from services.usage_service import UsageService
from datetime import datetime

logger = logging.getLogger(__name__)

project_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


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



def _create_ai_service_from_request(request_data: dict = None) -> AIService:
    """
    Create AI service instance from request data or fallback to environment
    config
    
    Args:
        request_data: Request data that may contain API configurations
        
    Returns:
        AIService instance
        
    Raises:
        ValueError: If no valid API configuration is found
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
            logger.info(
                f"Using frontend text API config: {text_config['provider']}"
            )
        
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
            logger.info(
                f"Using frontend image API config: {image_config['provider']}"
            )
    
    # Fallback to environment config if no API config provided
    # Check if running in Cloud Run (K_SERVICE env var exists)
    is_cloud_run = os.getenv('K_SERVICE') is not None
    
    if not text_config:
        google_api_key = current_app.config.get('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY')
        google_api_base = current_app.config.get('GOOGLE_API_BASE')
        
        # Explicit fallback: If key exists or we are in Cloud Run, force use Google/Gemini
        if google_api_key or is_cloud_run:
            text_config = {
                'provider': 'google',
                'api_key': google_api_key or '',  # Empty string triggers ADC in provider
                'base_url': google_api_base,
                'model': current_app.config.get('GOOGLE_TEXT_MODEL', 'gemini-2.5-flash'),
            }
            logger.info(f"Using environment text API config: google (model: {text_config['model']})")
    
    if not image_config:
        google_api_key = current_app.config.get('GOOGLE_API_KEY')
        google_api_base = current_app.config.get('GOOGLE_API_BASE')
        
        if google_api_key or is_cloud_run:
            image_config = {
                'provider': 'google',
                'api_key': google_api_key or '',  # Empty string triggers ADC in provider
                'base_url': google_api_base,
                'model': current_app.config.get('GOOGLE_IMAGE_MODEL', 'gemini-3-pro-image-preview'),
                'aspect_ratio': '16:9',
                'resolution': '2K',
            }
            logger.info(f"Using environment image API config: google (model: {image_config['model']})")
    
    # 检查是否至少有一个可用的配置
    if not text_config and not image_config:
        raise ValueError(
            "No valid API configuration found. Please configure at least one "
            "API in the frontend or set GOOGLE_API_KEY in environment "
            "variables (or run in Cloud Run with ADC)."
        )
    
    try:
        return AIService(text_config=text_config, image_config=image_config)
    except Exception as e:
        logger.error(f"Failed to create AI service: {str(e)}")
        raise ValueError(f"Failed to initialize AI service: {str(e)}")


def _get_project_reference_files_content(
    project_id: str, user_id: str
) -> list:
    """
    Get reference files content for a project
    """
    reference_files = firestore_service.list_project_reference_files(
        project_id, user_id
    )
    
    files_content = []
    for ref_file in reference_files:
        if (ref_file.get('parse_status') == 'completed' and
                ref_file.get('markdown_content')):
            files_content.append({
                'filename': ref_file.get('filename'),
                'content': ref_file.get('markdown_content')
            })
    
    return files_content


def _reconstruct_outline_from_pages(pages: list) -> list:
    """
    Reconstruct outline structure from Page objects
    
    Args:
        pages: List of Page objects ordered by order_index
        
    Returns:
        Outline structure (list) with optional part grouping
    """
    outline = []
    current_part = None
    current_part_pages = []
    
    for page in pages:
        outline_content = page.get_outline_content()
        if not outline_content:
            continue
            
        page_data = outline_content.copy()
        
        # 如果当前页面属于一个 part
        if page.part:
            # 如果这是新的 part，先保存之前的 part（如果有）
            if current_part and current_part != page.part:
                outline.append({
                    "part": current_part,
                    "pages": current_part_pages
                })
                current_part_pages = []
            
            current_part = page.part
            # 移除 part 字段，因为它在顶层
            if 'part' in page_data:
                del page_data['part']
            current_part_pages.append(page_data)
        else:
            # 如果当前页面不属于任何 part，先保存之前的 part（如果有）
            if current_part:
                outline.append({
                    "part": current_part,
                    "pages": current_part_pages
                })
                current_part = None
                current_part_pages = []
            
            # 直接添加页面
            outline.append(page_data)
    
    # 保存最后一个 part（如果有）
    if current_part:
        outline.append({
            "part": current_part,
            "pages": current_part_pages
        })
    
    return outline


@project_bp.route('', methods=['GET'])
@auth_required
def list_projects():
    """
    GET /api/projects - Get all projects (for history)
    """
    try:
        user_id = request.user_id
        projects = firestore_service.list_projects(user_id)
        
        return success_response({
            'projects': projects,
            'total': len(projects)
        })
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('', methods=['POST'])
@auth_required
def create_project():
    """
    POST /api/projects - Create a new project
    """
    try:
        user_id = request.user_id
        data = request.get_json()
        
        if not data:
            return bad_request("Request body is required")
        
        creation_type = data.get('creation_type', 'idea')
        
        # Create project data
        project_data = {
            'creation_type': creation_type,
            'idea_prompt': data.get('idea_prompt'),
            'outline_text': data.get('outline_text'),
            'description_text': data.get('description_text'),
            'status': 'DRAFT'
        }
        
        project_id = firestore_service.create_project(project_data, user_id)
        
        return success_response({
            'project_id': project_id,
            'status': 'DRAFT',
            'pages': []
        }, status_code=201)
    
    except Exception as e:
        logging.exception("Detailed Error:")
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>', methods=['GET'])
@auth_required
def get_project(project_id):
    """
    GET /api/projects/{project_id} - Get project details
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)
        
        if not project:
            return not_found('Project')
            
        # Get pages
        pages = firestore_service.get_pages(project_id, user_id)
        project['pages'] = pages
        
        return success_response(project)
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>', methods=['PUT'])
@auth_required
def update_project(project_id):
    """
    PUT /api/projects/{project_id} - Update project
    """
    try:
        user_id = request.user_id
        data = request.get_json()
        
        # Update project fields
        update_data = {}
        if 'idea_prompt' in data:
            update_data['idea_prompt'] = data['idea_prompt']
        if 'extra_requirements' in data:
            update_data['extra_requirements'] = data['extra_requirements']
            
        if update_data:
            firestore_service.update_project(project_id, update_data, user_id)
            
        # Update page order if provided
        if 'pages_order' in data:
            pages_order = data['pages_order']
            for index, page_id in enumerate(pages_order):
                firestore_service.update_page(
                    project_id, page_id, {'order_index': index}, user_id
                )
        
        return success_response(
            firestore_service.get_project(project_id, user_id)
        )
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>', methods=['DELETE'])
@auth_required
def delete_project(project_id):
    """
    DELETE /api/projects/{project_id} - Delete project
    """
    try:
        user_id = request.user_id
        
        # Delete project files from Storage
        from services.file_service import FileService
        file_service = FileService()
        file_service.delete_project_files(project_id)
        
        # Delete from Firestore
        firestore_service.delete_project(project_id, user_id)
        
        return success_response(message="Project deleted successfully")
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>/generate/outline', methods=['POST'])
@auth_required
def generate_outline(project_id):
    """
    POST /api/projects/{project_id}/generate/outline - Generate outline
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)
        
        if not project:
            return not_found('Project')
        
        # Initialize AI service
        request_data = request.get_json() if request.is_json else {}
        ai_service = _create_ai_service_from_request(request_data)
        
        # Get reference files content and create project context
        reference_files_content = _get_project_reference_files_content(
            project_id, user_id
        )
        
        # 根据项目类型选择不同的处理方式
        if project.get('creation_type') == 'outline':
            if not project.get('outline_text'):
                return bad_request(
                    "outline_text is required for outline type project"
                )
            
            project_context = ProjectContext(project, reference_files_content)
            outline = ai_service.parse_outline_text(project_context)
        elif project.get('creation_type') == 'descriptions':
            return bad_request(
                "Use /generate/from-description endpoint for descriptions type"
            )
        else:
            data = request.get_json() or {}
            idea_prompt = data.get('idea_prompt') or project.get('idea_prompt')
            
            if not idea_prompt:
                return bad_request("idea_prompt is required")
            
            firestore_service.update_project(
                project_id, {'idea_prompt': idea_prompt}, user_id
            )
            project['idea_prompt'] = idea_prompt
            
            project_context = ProjectContext(project, reference_files_content)
            outline = ai_service.generate_outline(project_context)
        
        # Flatten outline to pages
        pages_data = ai_service.flatten_outline(outline)
        
        # Delete existing pages
        firestore_service.delete_project_pages(project_id, user_id)
        
        # Create pages from outline
        pages_list = []
        for i, page_data in enumerate(pages_data):
            page_dict = {
                'project_id': project_id,
                'user_id': user_id,
                'order_index': i,
                'part': page_data.get('part'),
                'status': 'DRAFT',
                'outline_content': {
                    'title': page_data.get('title'),
                    'points': page_data.get('points', [])
                }
            }
            
            page_id = firestore_service.create_page(page_dict, user_id)
            page_dict['id'] = page_id
            pages_list.append(page_dict)
        
        # Update project status
        firestore_service.update_project(project_id, {
            'status': 'OUTLINE_GENERATED',
            'updated_at': datetime.utcnow()
        }, user_id)
        
        # Record usage
        usage = ai_service.last_usage
        tokens = usage.get('total_tokens', 0)
        UsageService.record_usage(
            user_id, 
            f"Generate Outline for Project {project_id}", 
            None, 
            tokens
        )
        
        return success_response({
            'pages': pages_list
        })
    
    except Exception as e:
        logger.error(f"generate_outline failed: {str(e)}", exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@project_bp.route('/<project_id>/generate/from-description', methods=['POST'])
@auth_required
def generate_from_description(project_id):
    """
    POST /api/projects/{project_id}/generate/from-description
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        if project.get('creation_type') != 'descriptions':
            return bad_request(
                "This endpoint is only for descriptions type projects"
            )

        # Get description text
        data = request.get_json() or {}
        description_text = (data.get('description_text') or
                            project.get('description_text'))

        if not description_text:
            return bad_request("description_text is required")

        firestore_service.update_project(project_id, {
            'description_text': description_text
        }, user_id)
        project['description_text'] = description_text

        # Initialize AI service
        ai_service = _create_ai_service_from_request(data)

        # Get reference files content and create project context
        reference_files_content = _get_project_reference_files_content(
            project_id, user_id
        )
        project_context = ProjectContext(project, reference_files_content)

        logger.info(f"开始从描述生成大纲和页面描述: 项目 {project_id}")

        # Step 1: Parse description to outline
        logger.info("Step 1: 解析描述文本到大纲结构...")
        outline = ai_service.parse_description_to_outline(project_context)
        logger.info(f"大纲解析完成，共 {len(ai_service.flatten_outline(outline))} 页")

        # Step 2: Split description into page descriptions
        logger.info("Step 2: 切分描述文本到每页描述...")
        page_descriptions = ai_service.parse_description_to_page_descriptions(
            project_context, outline
        )
        logger.info(f"描述切分完成，共 {len(page_descriptions)} 页")

        # Step 3: Flatten outline to pages
        pages_data = ai_service.flatten_outline(outline)

        if len(pages_data) != len(page_descriptions):
            logger.warning(
                f"页面数量不匹配: 大纲 {len(pages_data)} 页, "
                f"描述 {len(page_descriptions)} 页"
            )
            min_count = min(len(pages_data), len(page_descriptions))
            pages_data = pages_data[:min_count]
            page_descriptions = page_descriptions[:min_count]

        # Step 4: Delete existing pages
        firestore_service.delete_project_pages(project_id, user_id)

        # Step 5: Create pages with both outline and description
        pages_list = []
        for i, (page_data, page_desc) in enumerate(
            zip(pages_data, page_descriptions)
        ):
            page_dict = {
                'project_id': project_id,
                'user_id': user_id,
                'order_index': i,
                'part': page_data.get('part'),
                'status': 'DESCRIPTION_GENERATED',
                'outline_content': {
                    'title': page_data.get('title'),
                    'points': page_data.get('points', [])
                },
                'description_content': {
                    "text": page_desc,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }

            page_id = firestore_service.create_page(page_dict, user_id)
            page_dict['id'] = page_id
            pages_list.append(page_dict)

        # Update project status
        firestore_service.update_project(project_id, {
            'status': 'DESCRIPTIONS_GENERATED',
            'updated_at': datetime.utcnow()
        }, user_id)

        logger.info(f"从描述生成完成: 项目 {project_id}, 创建了 {len(pages_list)} 个页面")

        # Record usage (this endpoint calls multiple AI methods, we take the
        # last one or aggregate)
        # For simplicity, we'll record the last usage which is usually the
        # most significant
        usage = ai_service.last_usage
        tokens = usage.get('total_tokens', 0)
        UsageService.record_usage(
            user_id, 
            f"Generate from Description for Project {project_id}", 
            None, 
            tokens
        )

        return success_response({
            'pages': pages_list,
            'status': 'DESCRIPTIONS_GENERATED'
        })

    except Exception as e:
        logger.error(f"generate_from_description failed: {str(e)}",
                     exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@project_bp.route('/<project_id>/generate/descriptions', methods=['POST'])
@auth_required
def generate_descriptions(project_id):
    """
    POST /api/projects/{project_id}/generate/descriptions
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        allowed_statuses = [
            'OUTLINE_GENERATED',
            'DRAFT',
            'DESCRIPTIONS_GENERATED'
        ]
        if project.get('status') not in allowed_statuses:
            return bad_request("Project must have outline generated first")

        # Get pages
        pages = firestore_service.get_pages(project_id, user_id)

        if not pages:
            return bad_request("No pages found for project")

        # Reconstruct outline from pages
        outline = _reconstruct_outline_from_pages(pages)

        data = request.get_json() or {}
        max_workers = data.get(
            'max_workers',
            current_app.config.get('MAX_DESCRIPTION_WORKERS', 5)
        )

        # Create task
        task_id = str(uuid.uuid4())
        task_data = {
            'id': task_id,
            'project_id': project_id,
            'user_id': user_id,
            'task_type': 'GENERATE_DESCRIPTIONS',
            'status': 'PENDING',
            'progress': {
                'total': len(pages),
                'completed': 0,
                'failed': 0
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        firestore_service.create_task(task_data, user_id)

        # Initialize AI service
        ai_service = _create_ai_service_from_request(data)

        # Get reference files content and create project context
        reference_files_content = _get_project_reference_files_content(
            project_id, user_id
        )
        project_context = ProjectContext(project, reference_files_content)

        # Submit background task
        task_manager.submit_task(
            task_id,
            generate_descriptions_task,
            project_id,
            user_id,
            ai_service,
            project_context,
            outline,
            max_workers
        )

        # Update project status
        firestore_service.update_project(project_id, {
            'status': 'GENERATING_DESCRIPTIONS'
        }, user_id)

        return success_response({
            'task_id': task_id,
            'status': 'GENERATING_DESCRIPTIONS',
            'total_pages': len(pages)
        }, status_code=202)

    except Exception as e:
        logger.error(f"generate_descriptions failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>/generate/images', methods=['POST'])
@auth_required
def generate_images(project_id):
    """
    POST /api/projects/{project_id}/generate/images
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        # Get pages
        pages = firestore_service.get_pages(project_id, user_id)

        if not pages:
            return bad_request("No pages found for project")

        # Reconstruct outline from pages
        outline = _reconstruct_outline_from_pages(pages)

        data = request.get_json() or {}
        max_workers = data.get(
            'max_workers',
            current_app.config.get('MAX_IMAGE_WORKERS', 8)
        )
        use_template = data.get('use_template', True)

        # Create task
        task_id = str(uuid.uuid4())
        task_data = {
            'id': task_id,
            'project_id': project_id,
            'user_id': user_id,
            'task_type': 'GENERATE_IMAGES',
            'status': 'PENDING',
            'progress': {
                'total': len(pages),
                'completed': 0,
                'failed': 0
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        firestore_service.create_task(task_data, user_id)

        # Initialize services
        ai_service = _create_ai_service_from_request(data)

        from services import FileService
        file_service = FileService()

        # Submit background task
        task_manager.submit_task(
            task_id,
            generate_images_task,
            project_id,
            user_id,
            ai_service,
            file_service,
            outline,
            use_template,
            max_workers,
            current_app.config['DEFAULT_ASPECT_RATIO'],
            current_app.config['DEFAULT_RESOLUTION'],
            project.get('extra_requirements')
        )

        # Update project status
        firestore_service.update_project(project_id, {
            'status': 'GENERATING_IMAGES'
        }, user_id)

        return success_response({
            'task_id': task_id,
            'status': 'GENERATING_IMAGES',
            'total_pages': len(pages)
        }, status_code=202)

    except Exception as e:
        logger.error(f"generate_images failed: {str(e)}", exc_info=True)
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>/tasks/<task_id>', methods=['GET'])
@auth_required
def get_task_status(project_id, task_id):
    """
    GET /api/projects/{project_id}/tasks/{task_id}
    """
    try:
        user_id = request.user_id
        task = firestore_service.get_task(task_id, user_id)

        if not task or task.get('project_id') != project_id:
            return not_found('Task')

        return success_response(task)

    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@project_bp.route('/<project_id>/refine/outline', methods=['POST'])
@auth_required
def refine_outline(project_id):
    """
    POST /api/projects/{project_id}/refine/outline
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        data = request.get_json()

        if not data or not data.get('user_requirement'):
            return bad_request("user_requirement is required")

        user_requirement = data['user_requirement']

        # Get current outline from pages
        pages = firestore_service.get_pages(project_id, user_id)

        if not pages:
            logger.info(f"项目 {project_id} 当前没有页面，将从空开始生成")
            current_outline = []
        else:
            current_outline = _reconstruct_outline_from_pages(pages)

        # Initialize AI service
        ai_service = _create_ai_service_from_request(data)

        # Get reference files content and create project context
        reference_files_content = _get_project_reference_files_content(
            project_id, user_id
        )
        project_context = ProjectContext(project, reference_files_content)

        # Get previous requirements from request
        previous_requirements = data.get('previous_requirements', [])

        # Refine outline
        logger.info(f"开始修改大纲: 项目 {project_id}, 用户要求: {user_requirement}")
        refined_outline = ai_service.refine_outline(
            current_outline=current_outline,
            user_requirement=user_requirement,
            project_context=project_context,
            previous_requirements=previous_requirements
        )

        # Flatten outline to pages
        pages_data = ai_service.flatten_outline(refined_outline)

        # 保存已有的页面描述（按标题匹配）
        descriptions_map = {}
        old_status_map = {}

        for old_page in pages:
            old_outline = old_page.get('outline_content')
            if old_outline and old_outline.get('title'):
                title = old_outline.get('title')
                if old_page.get('description_content'):
                    descriptions_map[title] = old_page.get(
                        'description_content'
                    )
                if old_page.get('status') in [
                    'DESCRIPTION_GENERATED',
                    'IMAGE_GENERATED',
                    'COMPLETED'
                ]:
                    old_status_map[title] = old_page.get('status')

        # Delete existing pages
        firestore_service.delete_project_pages(project_id, user_id)

        # Create pages from refined outline
        pages_list = []
        for i, page_data in enumerate(pages_data):
            title = page_data.get('title')
            
            page_dict = {
                'project_id': project_id,
                'user_id': user_id,
                'order_index': i,
                'part': page_data.get('part'),
                'status': old_status_map.get(title, 'DRAFT'),
                'outline_content': {
                    'title': title,
                    'points': page_data.get('points', [])
                }
            }
            
            if title in descriptions_map:
                page_dict['description_content'] = descriptions_map[title]

            page_id = firestore_service.create_page(page_dict, user_id)
            page_dict['id'] = page_id
            pages_list.append(page_dict)

        # Update project status
        firestore_service.update_project(project_id, {
            'status': 'OUTLINE_GENERATED',
            'updated_at': datetime.utcnow()
        }, user_id)

        return success_response({
            'pages': pages_list
        })

    except Exception as e:
        logger.error(f"refine_outline failed: {str(e)}", exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)


@project_bp.route('/<project_id>/refine/descriptions', methods=['POST'])
@auth_required
def refine_descriptions(project_id):
    """
    POST /api/projects/{project_id}/refine/descriptions
    """
    try:
        user_id = request.user_id
        project = firestore_service.get_project(project_id, user_id)

        if not project:
            return not_found('Project')

        data = request.get_json()
        if not data or not data.get('user_requirement'):
            return bad_request("user_requirement is required")

        user_requirement = data['user_requirement']

        # Get pages
        pages = firestore_service.get_pages(project_id, user_id)
        if not pages:
            return bad_request("No pages found for project")

        # Prepare current descriptions for AI
        current_descriptions = []
        for i, page in enumerate(pages):
            current_descriptions.append({
                'index': i + 1,
                'title': page.get('outline_content', {}).get(
                    'title', 'Untitled'
                ),
                'description_content': page.get(
                    'description_content', {}
                ).get('text', '')
            })

        # Initialize AI service
        ai_service = _create_ai_service_from_request(data)

        # Get reference files content and create project context
        reference_files_content = _get_project_reference_files_content(
            project_id, user_id
        )
        project_context = ProjectContext(project, reference_files_content)

        # Get outline
        outline = _reconstruct_outline_from_pages(pages)

        # Refine descriptions
        logger.info(f"开始修改描述: 项目 {project_id}, 用户要求: {user_requirement}")
        refined_descriptions = ai_service.refine_descriptions(
            current_descriptions=current_descriptions,
            user_requirement=user_requirement,
            project_context=project_context,
            outline=outline,
            previous_requirements=data.get('previous_requirements', [])
        )

        if len(refined_descriptions) != len(pages):
            logger.warning(
                f"Refined descriptions count mismatch: "
                f"{len(refined_descriptions)} vs {len(pages)}"
            )
            # Use the smaller count to avoid index errors
            min_count = min(len(refined_descriptions), len(pages))
            refined_descriptions = refined_descriptions[:min_count]
            pages = pages[:min_count]

        # Update pages in Firestore
        for page, new_desc in zip(pages, refined_descriptions):
            firestore_service.update_page(project_id, page['id'], {
                'description_content': {
                    'text': new_desc,
                    'generated_at': datetime.utcnow().isoformat()
                },
                'status': 'DESCRIPTION_GENERATED'
            }, user_id)

        # Update project status
        firestore_service.update_project(project_id, {
            'status': 'DESCRIPTIONS_GENERATED',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Get updated pages
        updated_pages = firestore_service.get_pages(project_id, user_id)

        return success_response({
            'pages': updated_pages,
            'status': 'DESCRIPTIONS_GENERATED'
        })

    except Exception as e:
        logger.error(f"refine_descriptions failed: {str(e)}", exc_info=True)
        return error_response('AI_SERVICE_ERROR', str(e), 503)

