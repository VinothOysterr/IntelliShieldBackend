from sqlalchemy import Boolean, Column, Integer, String, Date, ForeignKey, LargeBinary, JSON
from sqlalchemy.orm import relationship
from database import Base
import bcrypt
from cryptography.fernet import Fernet
import os

# Generate and save this key securely; it should be consistent for encryption and decryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)


class SuperAdmin(Base):
    __tablename__ = "super_admin"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def set_password(self, password: str):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))


class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    full_name = Column(String(50))
    location = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(Date)
    updated_at = Column(Date)
    hashed_password = Column(String)
    number_of_licenses = Column(Integer, default=0)
    
    fire_extinguishers = relationship("FireExtinguisher", back_populates="admin")

    def set_password(self, password: str):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    mobile = Column(String(15), unique=True, nullable=False)
    doj = Column(Date, nullable=False)
    role = Column(String(50), default="Unknown")
    aadhaar = Column(String(100), unique=True)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=True)
    
    def set_password(self, password: str):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
    
    def encrypt_aadhaar(self, aadhaar: str):
        encrypted_aadhaar = cipher_suite.encrypt(aadhaar.encode('utf-8'))
        self.aadhaar = encrypted_aadhaar.decode('utf-8')

    def decrypt_aadhaar(self) -> str:
        decrypted_aadhaar = cipher_suite.decrypt(self.aadhaar.encode('utf-8'))
        return decrypted_aadhaar.decode('utf-8')

unique_model = {
    'Water Type': 'WAT',
    'Foam Type': 'FOT',
    'CO2 Type': 'COT',
    'DCP Type': 'DCT',
    'K Type kitchen': 'KIT',
    'Clean Agent Type': 'CAT',
    'Water Mist Type': 'WMT'
}


class FireExtinguisher(Base):
    __tablename__ = 'fireextinguisher'
    
    id = Column(Integer, primary_key=True, index=True)
    cylinder_number = Column(String(25), nullable=False)
    type_of_extinguisher = Column(String(50), nullable=False)
    is_number = Column(String(50), index=True, unique=True, nullable=False)
    location_tag_number = Column(String(50), nullable=False)
    location = Column(String(50), nullable=False)
    service_provider = Column(String(50), nullable=False)
    uom = Column(String(5), nullable=False)
    net_weight = Column(String(20), nullable=False)
    capacity = Column(String(20), nullable=False)
    date_of_refilling = Column(Date, nullable=False)
    due_of_refilling = Column(Date, nullable=False)
    date_of_hpt = Column(Date, nullable=False)
    due_of_hpt = Column(Date, nullable=False)
    manufacturing_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    admin_id = Column(Integer, ForeignKey("admin.id"))
    admin = relationship("Admin", back_populates="fire_extinguishers")
    
    monthly_activities = relationship("MonthlyActivity", back_populates="fire_extinguisher")

    def generate_is_number(self):
        unique_code = unique_model.get(self.type_of_extinguisher, 'UNK')
        return f'ISN-{unique_code}-{self.cylinder_number}'


class MonthlyActivity(Base):
    __tablename__ = 'monthlyactivity'
    
    id = Column(Integer, primary_key=True, index=True)
    is_number = Column(String(50), ForeignKey('fireextinguisher.is_number'), nullable=False)
    inspection_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    capacity_uom = Column(String(20), nullable=False)
    weight = Column(String(20), nullable=False)
    pressure = Column(String(50), nullable=False)
    cylinder_nozzle = Column(Boolean, nullable=False)
    operating_lever = Column(Boolean, nullable=False)
    safety_pin = Column(Boolean, nullable=False)
    pressure_gauge = Column(Boolean, nullable=False)
    paint_peeled_off = Column(Boolean, nullable=False)
    presence_of_rust = Column(Boolean, nullable=False)
    damaged_cylinder = Column(Boolean, nullable=False)
    dent_on_body = Column(Boolean, nullable=False)
    complaints = Column(String(255))
    inspectors_name = Column(String(50), nullable=False)
    additional_info = Column(JSON, default=dict)
    
    fire_extinguisher = relationship("FireExtinguisher", back_populates="monthly_activities")
    
    # Relationship to store multiple images
    images = relationship("MonthlyActivityImage", back_populates="monthly_activity", cascade="all, delete-orphan")
    

class MonthlyActivityImage(Base):
    __tablename__ = 'monthly_activity_images'
    
    id = Column(Integer, primary_key=True, index=True)
    monthly_activity_id = Column(Integer, ForeignKey('monthlyactivity.id'), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    description = Column(String(255))  # Optional: description or type of image
    
    monthly_activity = relationship("MonthlyActivity", back_populates="images")