from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.team import Team
from models.user import User, UserRole
from services.auth import verify_password, create_token, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    team_name: str
    role: UserRole = UserRole.member


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    team = db.query(Team).filter(Team.name == body.team_name).first()
    if not team:
        team = Team(name=body.team_name)
        db.add(team)
        db.flush()

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
        team_id=team.id,
    )
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username, "team": team.name, "role": user.role}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(user))
