from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from auth.permissions import admin_required


router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/campaigns", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def export_page(request: Request):
    return templates.TemplateResponse("campaigns.html", {"request": request})