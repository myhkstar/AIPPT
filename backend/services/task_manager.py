"""
Task Manager - handles background tasks using ThreadPoolExecutor
No need for Celery or Redis, uses in-memory task tracking
"""
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Dict
from datetime import datetime
from services.firestore_service import FirestoreService
from services.usage_service import UsageService

logger = logging.getLogger(__name__)
firestore_service = FirestoreService()


class TaskManager:
    """Simple task manager using ThreadPoolExecutor"""

    def __init__(self, max_workers: int = 4):
        """Initialize task manager"""
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}  # task_id -> Future
        self.lock = threading.Lock()

    def submit_task(self, task_id: str, func: Callable, *args, **kwargs):
        """Submit a background task"""
        future = self.executor.submit(func, task_id, *args, **kwargs)

        with self.lock:
            self.active_tasks[task_id] = future

        # Add callback to clean up when done
        future.add_done_callback(lambda f: self._cleanup_task(task_id))

    def _cleanup_task(self, task_id: str):
        """Clean up completed task"""
        with self.lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    def is_task_active(self, task_id: str) -> bool:
        """Check if task is still running"""
        with self.lock:
            return task_id in self.active_tasks

    def shutdown(self):
        """Shutdown the executor"""
        self.executor.shutdown(wait=True)


# Global task manager instance
task_manager = TaskManager(max_workers=4)


def generate_descriptions_task(task_id: str, project_id: str, user_id: str,
                               ai_service, project_context,
                               outline: List[Dict], max_workers: int = 5):
    """
    Background task for generating page descriptions
    """
    try:
        # Update status to PROCESSING
        firestore_service.update_task(task_id, {
            'status': 'PROCESSING',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Flatten outline to get pages
        pages_data = ai_service.flatten_outline(outline)

        # Get all pages for this project
        pages = firestore_service.get_pages(project_id, user_id)

        if len(pages) != len(pages_data):
            raise ValueError("Page count mismatch")

        # Initialize progress
        progress = {
            "total": len(pages),
            "completed": 0,
            "failed": 0
        }
        firestore_service.update_task(task_id, {'progress': progress}, user_id)

        # Generate descriptions in parallel
        completed = 0
        failed = 0

        def generate_single_desc(page_id, page_outline, page_index):
            try:
                desc_text = ai_service.generate_page_description(
                    project_context, outline, page_outline, page_index
                )

                desc_content = {
                    "text": desc_text,
                    "generated_at": datetime.utcnow().isoformat()
                }

                return (page_id, desc_content, None)
            except Exception as e:
                logger.error(f"Failed to generate description for page "
                             f"{page_id}: {str(e)}")
                return (page_id, None, str(e))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(generate_single_desc, page['id'],
                                page_data, i)
                for i, (page, page_data) in enumerate(
                    zip(pages, pages_data), 1
                )
            ]

            for future in as_completed(futures):
                page_id, desc_content, error = future.result()

                if error:
                    firestore_service.update_page(
                        project_id, page_id, {'status': 'FAILED'}, user_id
                    )
                    failed += 1
                else:
                    # Update page in Firestore
                    firestore_service.update_page(project_id, page_id, {
                        'description_content': desc_content,
                        'status': 'DESCRIPTION_GENERATED'
                    }, user_id)
                    
                    # Record usage
                    usage = ai_service.last_usage
                    tokens = usage.get('total_tokens', 0)
                    UsageService.record_usage(
                        user_id, 
                        f"Generate Description for Project {project_id}", 
                        None, 
                        tokens
                    )
                    
                    completed += 1

                # Update task progress
                progress['completed'] = completed
                progress['failed'] = failed
                firestore_service.update_task(
                    task_id, {'progress': progress}, user_id
                )

        # Mark task as completed
        firestore_service.update_task(task_id, {
            'status': 'COMPLETED',
            'completed_at': datetime.utcnow()
        }, user_id)

        if failed == 0:
            firestore_service.update_project(
                project_id, {'status': 'DESCRIPTIONS_GENERATED'}, user_id
            )

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        firestore_service.update_task(task_id, {
            'status': 'FAILED',
            'error_message': str(e),
            'completed_at': datetime.utcnow()
        }, user_id)


def generate_images_task(task_id: str, project_id: str, user_id: str,
                         ai_service, file_service, outline: List[Dict],
                         use_template: bool = True, max_workers: int = 8,
                         aspect_ratio: str = "16:9", resolution: str = "2K",
                         extra_requirements: str = None):
    """
    Background task for generating page images
    """
    try:
        # Update task status to PROCESSING
        firestore_service.update_task(task_id, {
            'status': 'PROCESSING',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Get all pages for this project
        pages = firestore_service.get_pages(project_id, user_id)
        pages_data = ai_service.flatten_outline(outline)

        # Get template path if use_template
        ref_image_path = None
        if use_template:
            ref_image_path = file_service.get_template_path(project_id)

        if not ref_image_path:
            raise ValueError("No template image found for project")

        # Initialize progress
        progress = {
            "total": len(pages),
            "completed": 0,
            "failed": 0
        }
        firestore_service.update_task(
            task_id, {'progress': progress}, user_id
        )

        # Generate images in parallel
        completed = 0
        failed = 0

        def generate_single_image(page_id, page_data, page_index):
            try:
                # Get page from Firestore
                page_obj = firestore_service.get_page(
                    project_id, page_id, user_id
                )
                if not page_obj:
                    raise ValueError(f"Page {page_id} not found")

                # Update page status
                firestore_service.update_page(
                    project_id, page_id, {'status': 'GENERATING'}, user_id
                )

                # Get description content
                desc_content = page_obj.get('description_content')
                if not desc_content:
                    raise ValueError("No description content for page")

                desc_text = desc_content.get('text', '')
                if not desc_text and desc_content.get('text_content'):
                    text_content = desc_content.get('text_content', [])
                    if isinstance(text_content, list):
                        desc_text = '\n'.join(text_content)
                    else:
                        desc_text = str(text_content)

                # Extract image URLs
                page_additional_ref_images = []
                has_material_images = False
                if desc_text:
                    image_urls = ai_service.extract_image_urls_from_markdown(
                        desc_text
                    )
                    if image_urls:
                        page_additional_ref_images = image_urls
                        has_material_images = True

                # Generate image prompt
                prompt = ai_service.generate_image_prompt(
                    outline, page_data, desc_text, page_index,
                    has_material_images=has_material_images,
                    extra_requirements=extra_requirements
                )

                # Generate image
                image = ai_service.generate_image(
                    prompt, ref_image_path, aspect_ratio, resolution,
                    additional_ref_images=page_additional_ref_images
                    if page_additional_ref_images else None
                )

                if not image:
                    raise ValueError("Failed to generate image")

                # Save image
                image_path = file_service.save_generated_image(
                    image, project_id, page_id
                )

                return (page_id, image_path, None)

            except Exception as e:
                logger.error(f"Failed to generate image for page {page_id}: "
                             f"{str(e)}")
                return (page_id, None, str(e))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(generate_single_image, page['id'],
                                page_data, i)
                for i, (page, page_data) in enumerate(
                    zip(pages, pages_data), 1
                )
            ]

            for future in as_completed(futures):
                page_id, image_path, error = future.result()

                if error:
                    firestore_service.update_page(
                        project_id, page_id, {'status': 'FAILED'}, user_id
                    )
                    failed += 1
                else:
                    firestore_service.update_page(project_id, page_id, {
                        'generated_image_path': image_path,
                        'status': 'COMPLETED'
                    }, user_id)
                    
                    # Record usage
                    usage = ai_service.last_usage
                    tokens = usage.get('total_tokens', 0)
                    UsageService.record_usage(
                        user_id, 
                        f"Generate Image for Project {project_id}", 
                        image_path, 
                        tokens
                    )
                    
                    completed += 1

                # Update task progress
                progress['completed'] = completed
                progress['failed'] = failed
                firestore_service.update_task(
                    task_id, {'progress': progress}, user_id
                )

        # Mark task as completed
        firestore_service.update_task(task_id, {
            'status': 'COMPLETED',
            'completed_at': datetime.utcnow()
        }, user_id)

        if failed == 0:
            firestore_service.update_project(
                project_id, {'status': 'COMPLETED'}, user_id
            )

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        firestore_service.update_task(task_id, {
            'status': 'FAILED',
            'error_message': str(e),
            'completed_at': datetime.utcnow()
        }, user_id)


def generate_single_page_image_task(
    task_id: str, project_id: str, page_id: str, user_id: str,
    ai_service, file_service, outline: List[Dict],
    use_template: bool = True, aspect_ratio: str = "16:9",
    resolution: str = "2K", extra_requirements: str = None
):
    """
    Background task for generating a single page image
    """
    try:
        # Update task status to PROCESSING
        firestore_service.update_task(task_id, {
            'status': 'PROCESSING',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Get page from Firestore
        page_obj = firestore_service.get_page(project_id, page_id, user_id)
        if not page_obj:
            raise ValueError(f"Page {page_id} not found")

        # Update page status
        firestore_service.update_page(
            project_id, page_id, {'status': 'GENERATING'}, user_id
        )

        # Get template path if use_template
        ref_image_path = None
        if use_template:
            ref_image_path = file_service.get_template_path(project_id)

        if not ref_image_path:
            raise ValueError("No template image found for project")

        # Get description content
        desc_content = page_obj.get('description_content')
        if not desc_content:
            raise ValueError("No description content for page")

        desc_text = desc_content.get('text', '')
        if not desc_text and desc_content.get('text_content'):
            text_content = desc_content.get('text_content', [])
            if isinstance(text_content, list):
                desc_text = '\n'.join(text_content)
            else:
                desc_text = str(text_content)

        # Extract image URLs
        page_additional_ref_images = []
        has_material_images = False
        if desc_text:
            image_urls = ai_service.extract_image_urls_from_markdown(desc_text)
            if image_urls:
                page_additional_ref_images = image_urls
                has_material_images = True

        # Find page data in outline
        pages_data = ai_service.flatten_outline(outline)
        page_data = None
        page_index = 1

        # Try to find by order_index
        order_index = page_obj.get('order_index', 1)
        if 0 < order_index <= len(pages_data):
            page_data = pages_data[order_index - 1]
            page_index = order_index

        if not page_data:
            raise ValueError(f"Could not find page data for page {page_id}")

        # Generate image prompt
        prompt = ai_service.generate_image_prompt(
            outline, page_data, desc_text, page_index,
            has_material_images=has_material_images,
            extra_requirements=extra_requirements
        )

        # Generate image
        image = ai_service.generate_image(
            prompt, ref_image_path, aspect_ratio, resolution,
            additional_ref_images=page_additional_ref_images
            if page_additional_ref_images else None
        )

        if not image:
            raise ValueError("Failed to generate image")

        # Save image
        image_path = file_service.save_generated_image(
            image, project_id, page_id
        )

        # Create a new version record
        versions = firestore_service.list_page_image_versions(page_id, user_id)
        version_number = len(versions) + 1

        version_data = {
            'page_id': page_id,
            'user_id': user_id,
            'image_path': image_path,
            'version_number': version_number,
            'is_current': True,
            'created_at': datetime.utcnow()
        }
        version_id = firestore_service.create_page_image_version(
            version_data, user_id
        )
        firestore_service.set_current_page_image_version(
            page_id, version_id, user_id
        )

        # Update page
        firestore_service.update_page(project_id, page_id, {
            'generated_image_path': image_path,
            'status': 'COMPLETED'
        }, user_id)

        # Mark task as completed
        firestore_service.update_task(task_id, {
            'status': 'COMPLETED',
            'completed_at': datetime.utcnow()
        }, user_id)

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        firestore_service.update_task(task_id, {
            'status': 'FAILED',
            'error_message': str(e),
            'completed_at': datetime.utcnow()
        }, user_id)

        firestore_service.update_page(
            project_id, page_id, {'status': 'FAILED'}, user_id
        )


def edit_page_image_task(
    task_id: str, project_id: str, page_id: str, user_id: str,
    ai_service, file_service, edit_prompt: str,
    aspect_ratio: str = "16:9", resolution: str = "2K"
):
    """
    Background task for editing a page image
    """
    try:
        # Update task status to PROCESSING
        firestore_service.update_task(task_id, {
            'status': 'PROCESSING',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Get page from Firestore
        page_obj = firestore_service.get_page(project_id, page_id, user_id)
        if not page_obj:
            raise ValueError(f"Page {page_id} not found")

        # Update page status
        firestore_service.update_page(
            project_id, page_id, {'status': 'GENERATING'}, user_id
        )

        # Get current image path
        current_image_path = page_obj.get('generated_image_path')
        if not current_image_path:
            raise ValueError("No current image to edit")

        # Get full path for editing
        full_current_image_path = file_service.get_full_path(current_image_path)

        # Edit image
        image = ai_service.edit_image(
            edit_prompt, full_current_image_path, aspect_ratio, resolution
        )

        if not image:
            raise ValueError("Failed to edit image")

        # Save image
        image_path = file_service.save_generated_image(
            image, project_id, page_id
        )

        # Create a new version record
        versions = firestore_service.list_page_image_versions(page_id, user_id)
        version_number = len(versions) + 1

        version_data = {
            'page_id': page_id,
            'user_id': user_id,
            'image_path': image_path,
            'version_number': version_number,
            'is_current': True,
            'created_at': datetime.utcnow()
        }
        version_id = firestore_service.create_page_image_version(
            version_data, user_id
        )
        firestore_service.set_current_page_image_version(
            page_id, version_id, user_id
        )

        # Update page
        firestore_service.update_page(project_id, page_id, {
            'generated_image_path': image_path,
            'status': 'COMPLETED'
        }, user_id)

        # Mark task as completed
        firestore_service.update_task(task_id, {
            'status': 'COMPLETED',
            'completed_at': datetime.utcnow()
        }, user_id)

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        firestore_service.update_task(task_id, {
            'status': 'FAILED',
            'error_message': str(e),
            'completed_at': datetime.utcnow()
        }, user_id)

        firestore_service.update_page(
            project_id, page_id, {'status': 'FAILED'}, user_id
        )


def generate_material_image_task(
    task_id: str, project_id: str, user_id: str,
    ai_service, file_service, prompt: str,
    ref_image_path: str = None,
    additional_ref_images: List[str] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "2K",
    temp_dir: str = None
):
    """
    Background task for generating a material image
    """
    try:
        # Update task status to PROCESSING
        firestore_service.update_task(task_id, {
            'status': 'PROCESSING',
            'updated_at': datetime.utcnow()
        }, user_id)

        # Generate image
        image = ai_service.generate_image(
            prompt,
            ref_image_path=ref_image_path,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            additional_ref_images=additional_ref_images
        )

        if not image:
            raise ValueError("Failed to generate material image")

        # Save image
        import uuid
        filename = f"material_{str(uuid.uuid4())[:8]}.png"

        # Note: file_service.save_material_image in Firebase version
        # returns blob_path
        blob_path = file_service.save_material_image(
            image, project_id if project_id != 'global' else None
        )

        # Get signed URL for the result
        url = file_service.get_file_url(
            project_id if project_id != 'global' else None,
            "materials",
            blob_path.split('/')[-1]
        )

        # Create material record
        material_data = {
            'project_id': project_id if project_id != 'global' else None,
            'user_id': user_id,
            'filename': filename,
            'relative_path': blob_path,
            'url': url,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        firestore_service.create_material(material_data, user_id)

        # Mark task as completed
        firestore_service.update_task(task_id, {
            'status': 'COMPLETED',
            'result': {'url': url, 'relative_path': blob_path},
            'completed_at': datetime.utcnow()
        }, user_id)

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        firestore_service.update_task(task_id, {
            'status': 'FAILED',
            'error_message': str(e),
            'completed_at': datetime.utcnow()
        }, user_id)
    finally:
        # Clean up temp directory if provided
        if temp_dir:
            import shutil
            import os
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")
