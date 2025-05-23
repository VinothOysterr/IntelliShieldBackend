from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
import schemas
import models
from dependencies import get_db
from typing import List, Dict, Any

router = APIRouter()


@router.post("/", response_model=schemas.MonthlyActivityResponse)
async def create_monthly_activity(monthly_activity: schemas.MonthlyActivityCreate, db: Session = Depends(get_db)):
    # Ensure the FireExtinguisher with the given IS number exists
    db_fire_extinguisher = db.query(models.FireExtinguisher).filter(models.FireExtinguisher.is_number == monthly_activity.is_number).first()

    if not db_fire_extinguisher:
        raise HTTPException(status_code=404, detail="FireExtinguisher with the given IS number not found.")

    # Create the MonthlyActivity instance
    db_monthly_activity = models.MonthlyActivity(**monthly_activity.model_dump())

    # Add and commit the instance to the database
    db.add(db_monthly_activity)
    db.commit()

    # Refresh to get the generated ID and other defaults
    db.refresh(db_monthly_activity)

    return db_monthly_activity


@router.post("/upload-images/{monthly_activity_id}")
async def upload_images(monthly_activity_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    monthly_activity = db.query(models.MonthlyActivity).filter(models.MonthlyActivity.id == monthly_activity_id).first()
    
    if not monthly_activity:
        return {"error": "MonthlyActivity not found"}
    
    for file in files:
        image_data = await file.read()
        new_image = models.MonthlyActivityImage(
            monthly_activity_id=monthly_activity_id,
            image_data=image_data,
            description=file.filename  # Optional: store filename as description
        )
        db.add(new_image)
    
    db.commit()
    return {"message": "Images uploaded successfully"}


@router.get("/", response_model=List[schemas.MonthlyActivityResponse])
async def get_all_monthly_activity(db: Session = Depends(get_db)):
    all_monthly_activity = db.query(models.MonthlyActivity).all()
    
    return all_monthly_activity


@router.put("/{activity_id}", response_model=schemas.MonthlyActivityResponse)
def update_activity_additional_info(activity_id: int, update_data: schemas.AdditionalInfoUpdate, db: Session = Depends(get_db)):
    return perform_additional_info_update(db, activity_id, update_data.additional_info)


def perform_additional_info_update(db: Session, activity_id: int, new_info: Dict[str, Any]):
    activity = db.query(models.MonthlyActivity).filter(models.MonthlyActivity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Initialize additional_info if it's None
    if activity.additional_info is None:
        activity.additional_info = {}

    # Update additional_info with new_info
    activity.additional_info = {**activity.additional_info, **new_info}

    # Commit the changes to the database
    db.commit()
    
    # Refresh the activity instance to get the latest state from the database
    db.refresh(activity)

    return activity  # Ensure to return the updated activity if needed


@router.delete("/{activity_id}", response_model=schemas.MonthlyActivityResponse)
async def delete_monthly_activity(activity_id: int, db: Session = Depends(get_db)):
    db_monthly_activity = db.query(models.MonthlyActivity).filter(models.MonthlyActivity.id == activity_id).first()
    
    if not db_monthly_activity:
        raise HTTPException(status_code=404, detail="MonthlyActivity with the given ID not found.")
    
    db.delete(db_monthly_activity)
    db.commit()
    
    return db_monthly_activity
