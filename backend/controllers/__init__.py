import logging
logger = logging.getLogger(__name__)

logger.info("Importing project_controller...")
from .project_controller import project_bp
logger.info("Importing page_controller...")
from .page_controller import page_bp
logger.info("Importing template_controller...")
from .template_controller import template_bp, user_template_bp
logger.info("Importing export_controller...")
from .export_controller import export_bp
logger.info("Importing file_controller...")
from .file_controller import file_bp
logger.info("Importing material_controller...")
from .material_controller import material_bp, material_global_bp
logger.info("Importing reference_file_controller...")
from .reference_file_controller import reference_file_bp
logger.info("Importing api_config_controller...")
from .api_config_controller import api_config_bp
logger.info("Importing auth_controller...")
from .auth_controller import auth_bp
logger.info("Importing user_controller...")
from .user_controller import user_bp
logger.info("Importing admin_controller...")
from .admin_controller import admin_bp
logger.info("All controllers imported in __init__.py")

__all__ = [
    'project_bp', 
    'page_bp', 
    'template_bp', 
    'user_template_bp', 
    'export_bp', 
    'file_bp', 
    'material_bp',
    'material_global_bp',
    'reference_file_bp',
    'api_config_bp',
    'auth_bp',
    'user_bp',
    'admin_bp'
]
