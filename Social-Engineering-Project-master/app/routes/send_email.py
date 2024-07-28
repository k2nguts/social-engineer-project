import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from db.database import MongoDB
from utils.mail import send_email
from db.mail_content import EMAIL_SUBJECT, EMAIL_MESSAGE_BODY, IMG_PATHS, GHOST_IMAGE_PATH
from auth.permissions import admin_required
from datetime import datetime

router = APIRouter()
mongo_db = MongoDB()

@router.get("/api/send_email/", dependencies=[Depends(admin_required)])
async def send_email_endpoint(token: str = Query(...)):
    victim = mongo_db.get_victim_by_token(token)
    if not victim:
        raise HTTPException(status_code=404, detail="Victim not found")
    
    name_surname = victim["name"] + " " + victim["surname"]
    await send_email(victim["email"], EMAIL_SUBJECT, EMAIL_MESSAGE_BODY, token, name_surname, IMG_PATHS)
    mongo_db.victims_collection.update_one({"token": token}, {"$set": {"status": "Delivered"}})
    return {"message": "Email sent successfully"}


@router.post("/api/send_emails_to_all_victims", dependencies=[Depends(admin_required)])
async def send_emails_to_all_victims():
    try:
        victims = mongo_db.get_victims_summary()
        for victim in victims:
            name_surname = victim["name"] + " " + victim["surname"]
            await send_email(victim["email"], EMAIL_SUBJECT, EMAIL_MESSAGE_BODY, victim["token"], name_surname, IMG_PATHS)
            mongo_db.victims_collection.update_one({"token": victim["token"]}, {"$set": {"status": "Delivered"}})
        return {"message": "Emails sent to all victims successfully"}
    except Exception as e:
        logging.error(f"Failed to send emails to all victims: {e}")
        raise HTTPException(status_code=500, detail="Failed to send emails to all victims")

#Get GHOST IMAGE FROM VICTIM
@router.get("/api/send_image")
async def send_image(token: str = Query(None)):
    open_date = datetime.now()
    if not token:
        return FileResponse(GHOST_IMAGE_PATH, media_type="image/png")

    # Retrieve victim from MongoDB using token
    victim = mongo_db.get_victim_by_token(token)
    if not victim:
        return FileResponse(GHOST_IMAGE_PATH, media_type="image/png")

    # Update victim's open info
    update_result = mongo_db.update_victim_open_info(token, open_date)
    if update_result:
        logging.info(f"Updated open info for victim with token {token}")
    else:
        logging.error(f"Failed to update open info for victim with token {token}")

    return FileResponse(GHOST_IMAGE_PATH, media_type="image/png")