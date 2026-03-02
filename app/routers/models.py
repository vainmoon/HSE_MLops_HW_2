from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.model import Model
from models.user import User
from services.auth import get_current_user

router = APIRouter(prefix="/models", tags=["models"])


class ModelCreate(BaseModel):
    name: str
    task_type: str
    description: Optional[str] = None


class ModelResponse(BaseModel):
    id: int
    name: str
    task_type: str
    description: Optional[str]
    team_id: int
    created_by: int

    class Config:
        from_attributes = True


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    body: ModelCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = Model(
        name=body.name,
        task_type=body.task_type,
        description=body.description,
        team_id=user.team_id,
        created_by=user.id,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("", response_model=list[ModelResponse])
def list_models(
    name: Optional[str] = None,
    team_id: Optional[int] = None,
    task_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Model)
    if name:
        q = q.filter(Model.name.ilike(f"%{name}%"))
    if team_id:
        q = q.filter(Model.team_id == team_id)
    if task_type:
        q = q.filter(Model.task_type == task_type)
    return q.all()


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    model = db.get(Model, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model
