"""
Backend configuration file
"""
import os

# 基础配置
_current_file = os.path.realpath(__file__)
BASE_DIR = os.path.dirname(_current_file)
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Flask配置
class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    
    # 文件存储配置
    # In Cloud Run, /tmp is the only writable directory
    if os.getenv('K_SERVICE'):
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
        
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_REFERENCE_FILE_EXTENSIONS = {
        'pdf', 'docx', 'pptx', 'doc', 'ppt', 'xlsx', 'xls', 'csv', 'txt', 'md'
    }
    
    # AI服务配置
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GOOGLE_API_BASE = os.getenv('GOOGLE_API_BASE', '')
    
    # MinerU 文件解析服务配置
    MINERU_TOKEN = os.getenv('MINERU_TOKEN', '')
    MINERU_API_BASE = os.getenv('MINERU_API_BASE', 'https://mineru.net')
    
    # AI Model Configuration
    GOOGLE_TEXT_MODEL = os.getenv('GOOGLE_TEXT_MODEL', 'gemini-2.5-flash')
    GOOGLE_IMAGE_MODEL = os.getenv('GOOGLE_IMAGE_MODEL', 'gemini-3-pro-image-preview')
    IMAGE_CAPTION_MODEL = os.getenv('IMAGE_CAPTION_MODEL', 'gemini-2.5-flash')
    
    # 并发配置
    MAX_DESCRIPTION_WORKERS = int(os.getenv('MAX_DESCRIPTION_WORKERS', '5'))
    MAX_IMAGE_WORKERS = int(os.getenv('MAX_IMAGE_WORKERS', '8'))
    
    # 图片生成配置
    DEFAULT_ASPECT_RATIO = "16:9"
    DEFAULT_RESOLUTION = "2K"
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# 根据环境变量选择配置
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
