from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from db.database import MongoDB
from db.models import Victim
from auth.permissions import admin_required, authentication_required
import logging
from typing import List

router = APIRouter()
mongo_db = MongoDB()
templates = Jinja2Templates(directory="templates")  # Ensure 'templates' directory exists

@router.get("/api/analytics", response_class=JSONResponse, dependencies=[Depends(authentication_required)])
async def get_analytics():
    try:
        analytics_data = mongo_db.get_analytics_data()
        if analytics_data:
            return JSONResponse(content=analytics_data)
        else:
            raise HTTPException(status_code=500, detail="Failed to get analytics data")
    except Exception as e:
        logging.error(f"Failed to get analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")

@router.get("/victim_info", response_class=HTMLResponse,  dependencies=[Depends(admin_required)])
async def victim_info(request: Request, token: str):
    victim = mongo_db.get_victim_by_token(token)
    if victim:
        return templates.TemplateResponse("victim_info.html", {"request": request, "victim": victim})
    else:
        raise HTTPException(status_code=404, detail="Victim not found")

@router.get("/victims_analytics", response_class=HTMLResponse,  dependencies=[Depends(authentication_required)])
async def victims_analytics(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@router.get("/api/victims", response_model=List[Victim],  dependencies=[Depends(admin_required)])
async def read_victims():
    try:
        victims_summary = mongo_db.get_victims_summary()
        victims = [
            Victim(
                token=victim["token"],
                name=victim["name"],
                surname=victim["surname"],
                email=victim["email"],
                status=victim["status"],
                department=victim["department"]
            )
            for victim in victims_summary
        ]
        return victims
    except Exception as e:
        logging.error(f"Failed to fetch victims: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch victims")
