from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List, Dict, Any, Optional


class Token(BaseModel):
    access_token: str
    token_type: str
    admin_id: int
    location: str

class UserToken(BaseModel):
    access_token: str
    token_type: str
    username: str

class SuperAdminToken(BaseModel):
    access_token: str
    token_type: str
    admin_id: int
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    lic: int 

class AdminLogin(BaseModel):
    username: str
    password: str
    

class UserBase(BaseModel):
    username: str
    name: str
    mobile: str
    role: str
    doj: date


class UserCreate(UserBase):
    password: str
    aadhaar: str


class UserResponse(UserBase):
    id: int
    created_at: date
    updated_at: date

    class Config:
        from_attributes = True


class SuperAdminBase(BaseModel):
    username: str


class SuperAdminCreate(SuperAdminBase):
    password: str


class SuperAdminResponse(SuperAdminBase):
    id: int

    class Config:
        from_attributes = True


class AdminBase(BaseModel):
    username: str
    email: str
    full_name: str
    is_active: bool
    location: str
    number_of_licenses: int


class AdminCreate(AdminBase):
    password: str


class AdminResponse(AdminBase):
    id: int
    created_at: date
    updated_at: date
    fire_extinguishers: List["FireExtinguisherResponse"] = []

    class Config:
        from_attributes = True


class AdminListResponse(BaseModel):
    username: str
    location: str
    license_count: int


class FireExtinguisherBase(BaseModel):
    cylinder_number: str
    type_of_extinguisher: str
    location_tag_number: str
    location: str
    service_provider: str
    uom: str
    net_weight: str
    capacity: str
    date_of_refilling: date
    due_of_refilling: date
    date_of_hpt: date
    due_of_hpt: date
    manufacturing_date: date
    expiry_date: date


class FireExtinguisherCreate(FireExtinguisherBase):
    pass


class FireExtinguisherResponse(FireExtinguisherBase):
    id: int
    is_number: str
    admin_id: int
    monthly_activities: List["MonthlyActivityResponse"] = []

    class Config:
        from_attributes = True


class FireExtinguisherSummaryResponse(BaseModel):
    sl_no: int  # This could be a calculated field based on the index in the response
    serial_no: str
    location_name: str
    location_tag_no: str
    cylinder_number: str
    date_of_refilling: date
    due_of_refilling: date
    type_of_extinguisher: str
    net_weight: str
    uom: str
    due_of_hpt: date
    expiry_date: date

    class Config:
        form_attributes = True


class MonthlyActivityBase(BaseModel):
    is_number: str
    inspection_date: date
    due_date: date
    capacity_uom: str
    weight: str
    pressure: str
    cylinder_nozzle: bool
    operating_lever: bool
    safety_pin: bool
    pressure_gauge: bool
    paint_peeled_off: bool
    presence_of_rust: bool
    damaged_cylinder: bool
    dent_on_body: bool
    complaints: str
    inspectors_name: str
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    
class MonthlyActivityCreate(MonthlyActivityBase):
    pass


class MonthlyActivityImageResponse(BaseModel):
    id: int
    description: Optional[str]

    class Config:
        orm_mode = True


class MonthlyActivityResponse(MonthlyActivityBase):
    id: int
    images: List[MonthlyActivityImageResponse] = []  # List of images
    
    class Config:
        from_attributes = True

        
class AdditionalInfoUpdate(BaseModel):
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
