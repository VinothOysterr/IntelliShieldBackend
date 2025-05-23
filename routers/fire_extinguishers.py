from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends,  HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import models
import schemas
import logging
from sqlalchemy import desc
from dependencies import get_db, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()


# @router.post("/", response_model=schemas.FireExtinguisherResponse)
# async def create_fire_extinguisher(fire_extinguisher: schemas.FireExtinguisherCreate, db: Session = Depends(get_db), current_admin: models.Admin = Depends(get_current_admin)):
#     db_fire_extinguisher = models.FireExtinguisher(**fire_extinguisher.model_dump(), admin_id=current_admin.id)
#     db_fire_extinguisher.is_number = db_fire_extinguisher.generate_is_number()
#     db.add(db_fire_extinguisher)
#     db.commit()
#     db.refresh(db_fire_extinguisher)
#     return db_fire_extinguisher

@router.post("/", response_model=schemas.FireExtinguisherResponse)
async def create_fire_extinguisher(
    fire_extinguisher: schemas.FireExtinguisherCreate,
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin),
):
    # Count the fire extinguishers already created by the admin
    extinguisher_count = db.query(models.FireExtinguisher).filter_by(admin_id=current_admin.id).count()
    
    # Check if the admin has reached their license limit
    if extinguisher_count >= current_admin.license_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached the limit of {current_admin.license_limit} fire extinguishers."
        )
    
    # Proceed with creating the fire extinguisher
    db_fire_extinguisher = models.FireExtinguisher(**fire_extinguisher.model_dump(), admin_id=current_admin.id)
    db_fire_extinguisher.is_number = db_fire_extinguisher.generate_is_number()
    db.add(db_fire_extinguisher)
    db.commit()
    db.refresh(db_fire_extinguisher)
    return db_fire_extinguisher

@router.get("/{is_number}", response_model=schemas.FireExtinguisherSummaryResponse)
async def read_fire_extinguisher_by_is_number(is_number: str, db: Session = Depends(get_db)):
    # Query the fire extinguisher by its is_number
    fire_extinguisher = db.query(models.FireExtinguisher).filter(models.FireExtinguisher.is_number == is_number).first()
    
    if fire_extinguisher is None:
        raise HTTPException(status_code=404, detail="Fire extinguisher not found")

    # Check if there are any monthly activities
    if len(fire_extinguisher.monthly_activities) > 0:
        last_updated_data = fire_extinguisher.monthly_activities[-1]
    else:
        # If no monthly activities exist, return the summary with a non-compliant flag
        return schemas.FireExtinguisherSummaryResponse(
            sl_no=fire_extinguisher.id,
            serial_no=fire_extinguisher.is_number,
            location_name=fire_extinguisher.location,
            location_tag_no=fire_extinguisher.location_tag_number,
            cylinder_number=fire_extinguisher.cylinder_number,
            date_of_refilling=fire_extinguisher.date_of_refilling,
            due_of_refilling=fire_extinguisher.due_of_refilling,
            type_of_extinguisher=fire_extinguisher.type_of_extinguisher,
            net_weight=fire_extinguisher.net_weight,
            uom=fire_extinguisher.uom,
            due_of_hpt=fire_extinguisher.due_of_hpt,
            expiry_date=fire_extinguisher.expiry_date,
            non_compliant=True  # Set non_compliant flag as True if no inspections
        )

    # Check individual attributes in the latest inspection data (last_updated_data)
    failed_checks = [
        attr for attr in [
            "cylinder_nozzle",
            "operating_lever",
            "safety_pin",
            "pressure_gauge",
        ] if not getattr(last_updated_data, attr)
    ] + [
        attr for attr in [
            "paint_peeled_off",
            "presence_of_rust",
            "damaged_cylinder",
            "dent_on_body",
        ] if getattr(last_updated_data, attr)
    ]
    
    # Remove items from failed_checks that are in additional_info
    failed_checks = [item for item in failed_checks if item not in last_updated_data.additional_info]

    # If there are no failed checks, return the fire extinguisher summary as compliant
    if not failed_checks:
        return schemas.FireExtinguisherSummaryResponse(
            sl_no=fire_extinguisher.id,
            serial_no=fire_extinguisher.is_number,
            location_name=fire_extinguisher.location,
            location_tag_no=fire_extinguisher.location_tag_number,
            cylinder_number=fire_extinguisher.cylinder_number,
            date_of_refilling=fire_extinguisher.date_of_refilling,
            due_of_refilling=fire_extinguisher.due_of_refilling,
            type_of_extinguisher=fire_extinguisher.type_of_extinguisher,
            net_weight=fire_extinguisher.net_weight,
            uom=fire_extinguisher.uom,
            due_of_hpt=fire_extinguisher.due_of_hpt,
            expiry_date=fire_extinguisher.expiry_date,
            non_compliant=False  # No failed checks means compliant
        )

    # Check if all the failed checks are in the additional_info, if so, return compliant
    if all(item in last_updated_data.additional_info for item in failed_checks):
        return schemas.FireExtinguisherSummaryResponse(
            sl_no=fire_extinguisher.id,
            serial_no=fire_extinguisher.is_number,
            location_name=fire_extinguisher.location,
            location_tag_no=fire_extinguisher.location_tag_number,
            cylinder_number=fire_extinguisher.cylinder_number,
            date_of_refilling=fire_extinguisher.date_of_refilling,
            due_of_refilling=fire_extinguisher.due_of_refilling,
            type_of_extinguisher=fire_extinguisher.type_of_extinguisher,
            net_weight=fire_extinguisher.net_weight,
            uom=fire_extinguisher.uom,
            due_of_hpt=fire_extinguisher.due_of_hpt,
            expiry_date=fire_extinguisher.expiry_date,
            non_compliant=False  # Compliant since defects are acknowledged in additional_info
        )

    # If there are failed checks that are not covered in additional_info, raise an exception
    raise HTTPException(
        status_code=400,
        detail={
            "message": f"Fire extinguisher not compliant with safety standards:",
            "id": fire_extinguisher.monthly_activities[-1].id,
            "defects": failed_checks
        }
    )


@router.get("/web_old/{is_number}", response_model=schemas.FireExtinguisherSummaryResponse)
async def read_fe_data_old_method(is_number: str, db: Session = Depends(get_db)):
    fire_extinguisher = db.query(models.FireExtinguisher).filter(models.FireExtinguisher.is_number == is_number).first()
    
    if fire_extinguisher is None:
        raise HTTPException(status_code=404, detail="Fire extinguisher not found")
    
    return schemas.FireExtinguisherSummaryResponse(
        sl_no=fire_extinguisher.id,
        serial_no=fire_extinguisher.is_number,
        location_name=fire_extinguisher.location,
        location_tag_no=fire_extinguisher.location_tag_number,
        cylinder_number=fire_extinguisher.cylinder_number,
        date_of_refilling=fire_extinguisher.date_of_refilling,
        due_of_refilling=fire_extinguisher.due_of_refilling,
        type_of_extinguisher=fire_extinguisher.type_of_extinguisher,
        net_weight=fire_extinguisher.net_weight,
        uom=fire_extinguisher.uom,
        due_of_hpt=fire_extinguisher.due_of_hpt,
        expiry_date=fire_extinguisher.expiry_date
    )


@router.get("/web/{is_number}", response_model=schemas.FireExtinguisherResponse)
async def read_fire_extinguisher_by_is_number(is_number: str, db: Session = Depends(get_db)):
    fire_extinguisher = db.query(models.FireExtinguisher).filter(models.FireExtinguisher.is_number == is_number).first()

    if fire_extinguisher is None:
        raise HTTPException(status_code=404, detail="Fire extinguisher not found")
    
    return fire_extinguisher

@router.get("/filter/{is_number}")
async def filter_fire_extinguishers(
    is_number: str,
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    # Query the fire extinguisher
    fire_extinguisher = db.query(models.FireExtinguisher).filter(
        models.FireExtinguisher.is_number == is_number
    ).first()
    
    if fire_extinguisher is None:
        raise HTTPException(status_code=404, detail="Fire extinguisher not found")

    # Convert fire extinguisher to dict for modification
    fire_ext_dict = {
        "id": fire_extinguisher.id,
        "is_number": fire_extinguisher.is_number,
        "type_of_extinguisher": fire_extinguisher.type_of_extinguisher,
        "capacity": fire_extinguisher.capacity,
        "uom": fire_extinguisher.uom,
        "location": fire_extinguisher.location,
        "location_tag_number": fire_extinguisher.location_tag_number,
        "cylinder_number": fire_extinguisher.cylinder_number,
        "manufacturing_date": fire_extinguisher.manufacturing_date.strftime("%Y-%m-%d") if fire_extinguisher.manufacturing_date else None,
        "expiry_date": fire_extinguisher.expiry_date.strftime("%Y-%m-%d") if fire_extinguisher.expiry_date else None,
        "date_of_refilling": fire_extinguisher.date_of_refilling.strftime("%Y-%m-%d") if fire_extinguisher.date_of_refilling else None,
        "due_of_refilling": fire_extinguisher.due_of_refilling.strftime("%Y-%m-%d") if fire_extinguisher.due_of_refilling else None,
        "date_of_hpt": fire_extinguisher.date_of_hpt.strftime("%Y-%m-%d") if fire_extinguisher.date_of_hpt else None,
        "due_of_hpt": fire_extinguisher.due_of_hpt.strftime("%Y-%m-%d") if fire_extinguisher.due_of_hpt else None,
        "service_provider": fire_extinguisher.service_provider,
        "net_weight": str(fire_extinguisher.net_weight) if fire_extinguisher.net_weight else None,
        "admin_id": fire_extinguisher.admin_id
    }

    # Get all monthly activities
    activities = fire_extinguisher.monthly_activities if fire_extinguisher.monthly_activities else []
    
    # Convert string dates to datetime objects for comparison
    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Filter activities based on date range
    filtered_activities = []
    for activity in activities:
        activity_date = activity.inspection_date
        
        # Check if the activity date falls within the range
        if start_date_obj and end_date_obj:
            if start_date_obj <= activity_date <= end_date_obj:
                filtered_activities.append(activity)
        elif start_date_obj and not end_date_obj:
            if activity_date >= start_date_obj:
                filtered_activities.append(activity)
        elif end_date_obj and not start_date_obj:
            if activity_date <= end_date_obj:
                filtered_activities.append(activity)
        else:
            filtered_activities.append(activity)

    # Convert filtered activities to list of dicts with proper formatting
    formatted_activities = []
    for activity in filtered_activities:
        activity_dict = {
            "id": activity.id,
            "is_number": activity.is_number,
            "inspection_date": activity.inspection_date.strftime("%Y-%m-%d"),
            "due_date": activity.due_date.strftime("%Y-%m-%d"),
            "inspectors_name": activity.inspectors_name,
            "weight": str(activity.weight),
            "capacity_uom": activity.capacity_uom,
            "pressure": activity.pressure,
            "operating_lever": activity.operating_lever,
            "safety_pin": activity.safety_pin,
            "pressure_gauge": activity.pressure_gauge,
            "cylinder_nozzle": activity.cylinder_nozzle,
            "paint_peeled_off": activity.paint_peeled_off,
            "presence_of_rust": activity.presence_of_rust,
            "dent_on_body": activity.dent_on_body,
            "damaged_cylinder": activity.damaged_cylinder,
            "complaints": activity.complaints,
            "additional_info": activity.additional_info
        }
        formatted_activities.append(activity_dict)

    # Add filtered activities to fire extinguisher dict
    fire_ext_dict["monthly_activities"] = formatted_activities

    return {"fire_extinguisher": fire_ext_dict}

@router.get("/fe_data/{admin_id}", response_model=List[schemas.FireExtinguisherResponse])
async def read_fire_extinguisher_by_admin_id(admin_id: int, db: Session = Depends(get_db)):
    fire_extinguishers = db.query(models.FireExtinguisher).filter(models.FireExtinguisher.admin_id == admin_id).all()
    if not fire_extinguishers:
        raise HTTPException(status_code=404, detail="Fire extinguishers not found")
    return fire_extinguishers