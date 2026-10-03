from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProfessionalCreate(BaseModel):
    id: str
    name: str
    email: str
    specialty: str
    professionalRegister: Optional[str] = None
    cpf: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    signatureUrl: Optional[str] = None

class ProfessionalLogin(BaseModel):
    email: str
    password: str

class PatientSchema(BaseModel):
    id: str
    professionalId: str
    fullName: str
    motherName: str
    birthDateEpochMillis: int
    phone: Optional[str] = None
    email: Optional[str] = None
    guardianName: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None
    createdAtEpochMillis: int