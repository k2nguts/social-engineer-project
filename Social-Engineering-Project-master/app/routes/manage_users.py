from fastapi import APIRouter, Request, Form, status, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from db.database import MongoDB
from auth.permissions import admin_required

router = APIRouter()
mongo_db = MongoDB()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")  # Ensure 'templates' directory exists

@router.get("/manage_users", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def manage_users(request: Request):
    users = mongo_db.users_collection.find({"role": "user"})
    return templates.TemplateResponse("manage_users.html", {"request": request, "users": users})

@router.post("/api/adduser", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def add_user(request: Request, username: str = Form(...), password: str = Form(...)):
    hashed_password = pwd_context.hash(password)
    mongo_db.users_collection.insert_one({
        "username": username,
        "password": hashed_password,
        "role": "user"
    })
    return RedirectResponse(url="/manage_users", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/deleteuser", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def delete_user(request: Request, username: str = Form(...)):
    mongo_db.users_collection.delete_one({"username": username, "role": "user"})
    return RedirectResponse(url="/manage_users", status_code=status.HTTP_303_SEE_OTHER)
