# Removed SQLAlchemy for Firestore migration
db = None


from .project import Project
from .page import Page
from .task import Task
from .user_template import UserTemplate
from .page_image_version import PageImageVersion
from .material import Material
from .reference_file import ReferenceFile

__all__ = ['db', 'Project', 'Page', 'Task', 'UserTemplate', 'PageImageVersion', 'Material', 'ReferenceFile']

