# Implementation Plan - Migration to Cloud Run & Firebase

This plan outlines the steps to migrate the AI PPT application from a local SQLite/File System setup to Google Cloud Run with Firestore and Firebase Storage, including JWT-based authentication for embedding.

## Phase 1: Infrastructure & Dependencies
- [ ] Add `firebase-admin` and `PyJWT` to `pyproject.toml`.
- [ ] Create `backend/firebase_config.py` for Firebase initialization.
- [ ] Create `backend/utils/auth.py` for JWT verification middleware.

## Phase 2: Backend Refactoring (Data Layer)
- [ ] Refactor `backend/services/file_service.py` to use Firebase Storage.
- [ ] Create Firestore-based data access layer (Repository pattern or direct Firestore calls).
- [ ] Update `backend/models/` to be plain Python objects (or keep as is but bypass SQLAlchemy).
- [ ] Update `backend/app.py` to initialize Firebase and remove SQLite logic.

## Phase 3: Backend Refactoring (Controllers)
- [ ] Update `project_controller.py`, `page_controller.py`, etc., to use Firestore.
- [ ] Add `user_id` filtering to all database queries.
- [ ] Apply JWT verification middleware to all protected routes.

## Phase 4: Frontend Refactoring
- [ ] Update API client to extract JWT from URL/Storage and include in headers.
- [ ] Update image/file handling to use Firebase Storage URLs (Signed URLs).

## Phase 5: Deployment Preparation
- [ ] Optimize `Dockerfile` for Cloud Run.
- [ ] Document required environment variables for Cloud Run.
- [ ] (Optional) Create GitHub Actions workflow for CI/CD.

## Environment Variables Needed
- `GOOGLE_APPLICATION_CREDENTIALS` (or Service Account JSON string)
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `JWT_PUBLIC_KEY` (for verifying tokens from the parent site)
- `GOOGLE_API_KEY` (existing)
- `CORS_ORIGINS` (existing)
