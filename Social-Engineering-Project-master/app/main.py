from fastapi import FastAPI, Request, HTTPException, Form, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from auth.auth import AuthHandler
from routes import send_email, import_export_file, manage_users, analytics, phishing_routes, campaigns, users_groups,Landing_page,email_template

app = FastAPI()

# Auth handler setup
auth_handler = AuthHandler()

# CORS Settings
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(import_export_file.router)
app.include_router(send_email.router)
app.include_router(manage_users.router)
app.include_router(analytics.router)
app.include_router(phishing_routes.router)
app.include_router(campaigns.router)
app.include_router(users_groups.router)
app.include_router(Landing_page.router)
app.include_router(email_template.router)

def get_session_token(request: Request):
    session_token = request.cookies.get("access_token")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session token not found"
        )
    return session_token

def admin_required(request: Request, auth_handler: AuthHandler = Depends(AuthHandler)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token not found",
        )
    user = auth_handler.get_current_user(token)
    if not auth_handler.is_admin(user["username"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
@app.get("/control_panel_login", response_class=HTMLResponse)
async def read_login_form(request: Request):
    return templates.TemplateResponse("control_panel_login.html", {"request": request})

@app.post("/control_panel_login", response_class=HTMLResponse)
async def control_panel_login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = auth_handler.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Generate JWT token
    access_token = auth_handler.create_access_token({"sub": user["username"]})

    # Store session token in MongoDB
    auth_handler.store_session_token(access_token, username)

    if user["role"] == "admin":
        redirect_url = "/admin_dashboard"
    elif user["role"] == "user":
        redirect_url = "/user_dashboard"
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access"
        )

    response = RedirectResponse(
        url=redirect_url, status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/admin_dashboard", response_class=HTMLResponse)
async def read_admin_dashboard(request: Request, token: str = Depends(get_session_token)):
    user = auth_handler.get_current_user(token)
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access"
        )

    return templates.TemplateResponse(
        "admin_dashboard.html", {"request": request, "username": user["username"]}
    )

@app.get("/user_dashboard", response_class=HTMLResponse)
async def read_user_dashboard(request: Request, token: str = Depends(get_session_token)):
    user = auth_handler.get_current_user(token)
    if user["role"] != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access"
        )

    return templates.TemplateResponse(
        "user_dashboard.html", {"request": request, "username": user["username"]}
    )

@app.post("/logout", response_class=HTMLResponse)
async def logout(request: Request, token: str = Depends(get_session_token)):
    # Remove session token from MongoDB
    auth_handler.remove_session_token(token)
    # Clear session token cookie
    response = RedirectResponse(url="/control_panel_login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
