from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User
from app.schemas.user import UserCreate, Token
from app.core.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.services.config import update_config_date


router = APIRouter(prefix="/auth", tags=["Auth"])

# Secret and algorithm used in JWT
SECRET_KEY = "your-secret-key"  # 🔒 Replace with a secure key in production
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    print("🔐 Validating token:", token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if token.startswith("Bearer "):
            token = token[7:]  # Strip "Bearer "
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ Decoded token payload:", payload)
        username: str = payload.get("sub")
        if username is None:
            print("❌ No username in token payload")
            raise credentials_exception
    except JWTError as e:
        print("❌ JWT decode error:", str(e))
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        print(f"❌ No user found in DB for username: {username}")
        raise credentials_exception

    print(f"✅ Authenticated user: {user.username}")
    return user


# Registration endpoint
@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    print(f'Creating New User {user}')
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f'New User {user} with user-id {new_user.id}')
    access_token = create_access_token({"sub": new_user.username})
    update_config_date(db, new_user.id)
    return Token(access_token=access_token)

# Login endpoint
@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": db_user.username})
    return Token(access_token=access_token)

# Optional: health check
@router.get("/health")
def health_check():
    return {"status": "ok"}
