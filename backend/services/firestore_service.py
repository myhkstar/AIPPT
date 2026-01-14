"""
Firestore Service - handles all database operations using Cloud Firestore
"""
import uuid
from datetime import datetime
from firebase_config import get_firebase
from google.cloud import firestore


class FirestoreService:
    def __init__(self):
        self.db, *_ = get_firebase()

    def _get_project_ref(self, project_id):
        return self.db.collection('projects').document(project_id)

    def _get_page_ref(self, project_id, page_id):
        return self._get_project_ref(project_id).collection('pages') \
            .document(page_id)

    # Project Operations
    def create_project(self, data, user_id):
        project_id = data.get('id', str(uuid.uuid4()))
        data['id'] = project_id
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        if 'status' not in data:
            data['status'] = 'DRAFT'

        self.db.collection('projects').document(project_id).set(data)
        return project_id

    def get_project(self, project_id, user_id):
        doc = self.db.collection('projects').document(project_id).get()
        if doc.exists:
            project_data = doc.to_dict()
            if project_data.get('user_id') == user_id:
                return project_data
        return None

    def update_project(self, project_id, data, user_id):
        project = self.get_project(project_id, user_id)
        if not project:
            return False

        data['updated_at'] = datetime.utcnow()
        self.db.collection('projects').document(project_id).update(data)
        return True

    def list_projects(self, user_id):
        docs = self.db.collection('projects') \
            .where('user_id', '==', user_id) \
            .order_by('created_at', direction=firestore.Query.DESCENDING) \
            .stream()
        return [doc.to_dict() for doc in docs]

    def delete_project(self, project_id, user_id):
        project = self.get_project(project_id, user_id)
        if not project:
            return False

        # Delete sub-collections (pages)
        pages = self.db.collection('projects').document(project_id) \
            .collection('pages').stream()
        for page in pages:
            page.reference.delete()

        self.db.collection('projects').document(project_id).delete()
        return True

    # Page Operations
    def create_page(self, project_id, data, user_id):
        # Verify project ownership
        if not self.get_project(project_id, user_id):
            return None

        page_id = data.get('id', str(uuid.uuid4()))
        data['id'] = page_id
        data['project_id'] = project_id
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()

        self._get_page_ref(project_id, page_id).set(data)
        return page_id

    def get_page(self, project_id, page_id, user_id):
        if not self.get_project(project_id, user_id):
            return None

        doc = self._get_page_ref(project_id, page_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def delete_page(self, project_id, page_id, user_id):
        if not self.get_project(project_id, user_id):
            return False

        self._get_page_ref(project_id, page_id).delete()
        return True

    def get_pages(self, project_id, user_id):
        if not self.get_project(project_id, user_id):
            return []

        docs = self._get_project_ref(project_id).collection('pages') \
            .order_by('order_index').stream()
        return [doc.to_dict() for doc in docs]

    def update_page(self, project_id, page_id, data, user_id):
        if not self.get_project(project_id, user_id):
            return False

        data['updated_at'] = datetime.utcnow()
        self._get_page_ref(project_id, page_id).update(data)
        return True

    # Task Operations
    def create_task(self, project_id, data, user_id):
        if not self.get_project(project_id, user_id):
            return None

        task_id = data.get('id', str(uuid.uuid4()))
        data['id'] = task_id
        data['project_id'] = project_id
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow()

        self.db.collection('tasks').document(task_id).set(data)
        return task_id

    def get_task(self, task_id, user_id):
        doc = self.db.collection('tasks').document(task_id).get()
        if doc.exists:
            task_data = doc.to_dict()
            if task_data.get('user_id') == user_id:
                return task_data
        return None

    def update_task(self, task_id, data, user_id):
        task = self.get_task(task_id, user_id)
        if not task:
            return False
        self.db.collection('tasks').document(task_id).update(data)
        return True

    # Reference File Operations
    def create_reference_file(self, data, user_id):
        ref_id = data.get('id', str(uuid.uuid4()))
        data['id'] = ref_id
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()

        self.db.collection('reference_files').document(ref_id).set(data)
        return ref_id

    def get_reference_file(self, ref_id, user_id):
        doc = self.db.collection('reference_files').document(ref_id).get()
        if doc.exists:
            ref_data = doc.to_dict()
            if ref_data.get('user_id') == user_id:
                return ref_data
        return None

    def list_project_reference_files(self, project_id, user_id):
        docs = self.db.collection('reference_files') \
            .where('project_id', '==', project_id) \
            .where('user_id', '==', user_id) \
            .stream()
        return [doc.to_dict() for doc in docs]

    def update_reference_file(self, ref_id, data, user_id):
        ref = self.get_reference_file(ref_id, user_id)
        if not ref:
            return False
        data['updated_at'] = datetime.utcnow()
        self.db.collection('reference_files').document(ref_id).update(data)
        return True

    # Material Operations
    def create_material(self, data, user_id):
        material_id = data.get('id', str(uuid.uuid4()))
        data['id'] = material_id
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()

        self.db.collection('materials').document(material_id).set(data)
        return material_id

    def get_material(self, material_id, user_id):
        doc = self.db.collection('materials').document(material_id).get()
        if doc.exists:
            material_data = doc.to_dict()
            if material_data.get('user_id') == user_id:
                return material_data
        return None

    # Page Image Version Operations
    def create_page_image_version(self, data, user_id):
        version_id = data.get('id', str(uuid.uuid4()))
        data['id'] = version_id
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow()

        self.db.collection('page_image_versions').document(version_id) \
            .set(data)
        return version_id

    def list_page_image_versions(self, page_id, user_id):
        docs = self.db.collection('page_image_versions') \
            .where('page_id', '==', page_id) \
            .where('user_id', '==', user_id) \
            .order_by('version_number', direction=firestore.Query.DESCENDING) \
            .stream()
        return [doc.to_dict() for doc in docs]

    def set_current_page_image_version(self, page_id, version_id, user_id):
        # Mark all versions for this page as not current
        versions = self.db.collection('page_image_versions') \
            .where('page_id', '==', page_id) \
            .where('user_id', '==', user_id) \
            .stream()

        batch = self.db.batch()
        for doc in versions:
            batch.update(doc.reference, {'is_current': False})

        # Mark the target version as current
        batch.update(
            self.db.collection('page_image_versions').document(version_id),
            {'is_current': True}
        )
        batch.commit()
        return True

    def delete_project_pages(self, project_id, user_id):
        """Delete all pages for a project"""
        if not self.get_project(project_id, user_id):
            return False

        pages = self.db.collection('projects').document(project_id) \
            .collection('pages').stream()
        batch = self.db.batch()
        for page in pages:
            batch.delete(page.reference)
        batch.commit()
        return True

    # User Template Operations
    def create_user_template(self, data, user_id):
        template_id = data.get('id', str(uuid.uuid4()))
        data['id'] = template_id
        data['user_id'] = user_id
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()

        self.db.collection('user_templates').document(template_id).set(data)
        return template_id

    def get_user_template(self, template_id, user_id):
        doc = self.db.collection('user_templates').document(template_id).get()
        if doc.exists:
            template_data = doc.to_dict()
            if template_data.get('user_id') == user_id:
                return template_data
        return None

    def list_user_templates(self, user_id):
        docs = self.db.collection('user_templates') \
            .where('user_id', '==', user_id) \
            .order_by('created_at', direction=firestore.Query.DESCENDING) \
            .stream()
        return [doc.to_dict() for doc in docs]

    def delete_user_template(self, template_id, user_id):
        template = self.get_user_template(template_id, user_id)
        if not template:
            return False
        self.db.collection('user_templates').document(template_id).delete()
        return True
