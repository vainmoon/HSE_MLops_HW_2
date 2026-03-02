from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.audit_log import AuditLog, AuditAction
from models.model import Model, ModelVersion, VersionStatus
from models.user import User, UserRole
from services.auth import get_current_user
from services.storage import presigned_upload_url, presigned_download_url, object_key

router = APIRouter(prefix="/models/{model_id}/versions", tags=["versions"])


class VersionCreate(BaseModel):
    training_params: Optional[dict] = None
    metrics: Optional[dict] = None


class StatusUpdate(BaseModel):
    status: VersionStatus


class VersionResponse(BaseModel):
    id: int
    version_number: int
    status: VersionStatus
    artifact_path: Optional[str]
    training_params: Optional[dict]
    metrics: Optional[dict]
    created_by: int
    created_at: datetime
    model_id: int

    class Config:
        from_attributes = True


def get_model_or_404(model_id: int, db: Session) -> Model:
    model = db.get(Model, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


def get_version_or_404(model_id: int, version_id: int, db: Session) -> ModelVersion:
    version = (
        db.query(ModelVersion)
        .filter(ModelVersion.id == version_id, ModelVersion.model_id == model_id)
        .first()
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return version


@router.post("", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
def create_version(
    model_id: int,
    body: VersionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = get_model_or_404(model_id, db)

    if model.team_id != user.team_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    last = (
        db.query(ModelVersion)
        .filter(ModelVersion.model_id == model_id)
        .order_by(ModelVersion.version_number.desc())
        .first()
    )
    next_number = (last.version_number + 1) if last else 1

    version = ModelVersion(
        model_id=model_id,
        version_number=next_number,
        status=VersionStatus.staging,
        training_params=body.training_params,
        metrics=body.metrics,
        created_by=user.id,
    )
    db.add(version)
    db.flush()

    db.add(AuditLog(
        model_id=model_id,
        version_id=version.id,
        action=AuditAction.create_version,
        new_status=VersionStatus.staging.value,
        user_id=user.id,
    ))
    db.commit()
    db.refresh(version)
    return version


@router.get("", response_model=list[VersionResponse])
def list_versions(
    model_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_model_or_404(model_id, db)
    return (
        db.query(ModelVersion)
        .filter(ModelVersion.model_id == model_id)
        .order_by(ModelVersion.version_number)
        .all()
    )


@router.get("/{version_id}", response_model=VersionResponse)
def get_version(
    model_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_version_or_404(model_id, version_id, db)


@router.patch("/{version_id}/status", response_model=VersionResponse)
def update_status(
    model_id: int,
    version_id: int,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in (UserRole.admin, UserRole.team_lead):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or team_lead can change status")

    version = get_version_or_404(model_id, version_id, db)
    old_status = version.status

    if body.status == VersionStatus.production:
        current_prod = (
            db.query(ModelVersion)
            .filter(
                ModelVersion.model_id == model_id,
                ModelVersion.status == VersionStatus.production,
            )
            .first()
        )
        if current_prod:
            current_prod.status = VersionStatus.archived

    version.status = body.status

    db.add(AuditLog(
        model_id=model_id,
        version_id=version.id,
        action=AuditAction.status_changed,
        old_status=old_status.value,
        new_status=body.status.value,
        user_id=user.id,
    ))
    db.commit()
    db.refresh(version)
    return version


@router.post("/{version_id}/upload-url")
def get_upload_url(
    model_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = get_model_or_404(model_id, db)
    if model.team_id != user.team_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    version = get_version_or_404(model_id, version_id, db)

    if not version.artifact_path:
        version.artifact_path = object_key(model_id, version_id)
        db.commit()

    return {"upload_url": presigned_upload_url(model_id, version_id)}


@router.get("/{version_id}/download-url")
def get_download_url(
    model_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    version = get_version_or_404(model_id, version_id, db)
    if not version.artifact_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not uploaded yet")

    return {"download_url": presigned_download_url(model_id, version_id)}
