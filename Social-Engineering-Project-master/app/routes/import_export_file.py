from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from utils.csv_utils import save_csv_to_directory, save_formatted_csv_to_directory
from db.database import MongoDB
from auth.permissions import admin_required
import os
import logging


router = APIRouter()
mongo_db = MongoDB()

templates = Jinja2Templates(directory="templates")


@router.post("/api/upload", dependencies=[Depends(admin_required)])
async def upload_file(file: UploadFile = File(...)):
    try:
        upload_directory = "./uploads"
        os.makedirs(upload_directory, exist_ok=True)  # Ensure upload directory exists
        file_location = os.path.join(upload_directory, file.filename)
        
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        # Call the function to insert victims from the uploaded file
        mongo_db.insert_victim_from_file(file_location)
        return {"info": "File uploaded and victims inserted successfully"}
    except Exception as e:
        logging.error(f"Failed to upload file and insert victims: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/export", response_class=HTMLResponse, dependencies=[Depends(admin_required)])
async def export_page(request: Request):
    return templates.TemplateResponse("export_data.html", {"request": request})

@router.get("/api/export_data/opened", dependencies=[Depends(admin_required)])
async def export_opened_emails():
    try:
        fields_to_export = ["name", "surname", "email", "department", "num_of_opened", "mail_opening_info"]
        data = list(mongo_db.victims_collection.find({"num_of_opened": {"$gt": 0}}, {"_id": 0}))
        if not data:
            raise HTTPException(status_code=404, detail="No opened emails found.")
        
        filepath = await save_formatted_csv_to_directory(data, "opened_emails.csv", fields_to_export)
        return FileResponse(filepath, media_type="text/csv", filename="opened_emails.csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/export_data/clicked", dependencies=[Depends(admin_required)])
async def export_clicked_links():
    try:
        fields_to_export = ["name", "surname", "email", "department", "num_of_clicked", "link_clicking_info"]
        data = list(mongo_db.victims_collection.find({"num_of_clicked": {"$gt": 0}}, {"_id": 0}))
        if not data:
            raise HTTPException(status_code=404, detail="No clicked links found.")
        
        filepath = await save_formatted_csv_to_directory(data, "clicked_links.csv", fields_to_export)
        return FileResponse(filepath, media_type="text/csv", filename="clicked_links.csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/export_data/submitted", dependencies=[Depends(admin_required)])
async def export_submitted_data():
    try:
        fields_to_export = ["name", "surname", "email", "department", "num_of_submitted", "data_submitting_info"]
        data = list(mongo_db.victims_collection.find({"num_of_submitted": {"$gt": 0}}, {"_id": 0}))
        if not data:
            raise HTTPException(status_code=404, detail="No submitted data found.")
        
        filepath = await save_formatted_csv_to_directory(data, "submitted_data.csv", fields_to_export)
        return FileResponse(filepath, media_type="text/csv", filename="submitted_data.csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/export_data/all", dependencies=[Depends(admin_required)])
async def export_all_data():
    try:
        data = list(mongo_db.victims_collection.find({}, {"_id": 0}))
        if not data:
            raise HTTPException(status_code=404, detail="No data found.")
        
        filepath = await save_csv_to_directory(data, "all_data.csv")
        return FileResponse(filepath, media_type="text/csv", filename="all_data.csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
