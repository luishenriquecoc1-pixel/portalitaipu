from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import verify_password, hash_password, create_access_token, get_current_user, require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...),
                db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request, "error": "Usuario ou senha incorretos"
        })

    token = create_access_token(data={"sub": user.id})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=86400)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/api/users", tags=["users"])
async def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    users = db.query(User).filter(User.is_active == True).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name,
             "role": u.role, "email": u.email, "avatar_color": u.avatar_color} for u in users]


@router.post("/api/users", tags=["users"])
async def create_user(request: Request, db: Session = Depends(get_db),
                       admin: User = Depends(require_admin)):
    data = await request.json()
    existing = db.query(User).filter(
        (User.username == data["username"]) | (User.email == data["email"])
    ).first()
    if existing:
        return {"error": "Usuario ou email ja existe"}

    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        full_name=data["full_name"],
        role=data.get("role", "editor"),
        avatar_color=data.get("avatar_color", "#6366f1"),
    )
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username}


@router.put("/api/users/me/dark-mode", tags=["users"])
async def toggle_dark_mode(request: Request, db: Session = Depends(get_db),
                           user: User = Depends(get_current_user)):
    data = await request.json()
    user.dark_mode = data.get("dark_mode", not user.dark_mode)
    db.commit()
    return {"dark_mode": user.dark_mode}
