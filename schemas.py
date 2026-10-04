from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from typing import Literal

class ProfessionalCreate(BaseModel):
    id: str = Field(min_length=1)
    name: str
    email: str
    specialty: str
    specialtyId: Optional[str] = None
    professionalRegister: Optional[str] = None
    cpf: Optional[str] = None
    password: str
    phone: Optional[str] = None
    signatureUrl: Optional[str] = None

class ProfessionalResponse(BaseModel):
    id: str
    name: str
    email: str
    specialty: str
    specialtyId: Optional[str] = None
    professionalRegister: Optional[str] = None
    phone: Optional[str] = None

class ProfessionalLogin(BaseModel):
    email: str
    password: str

class AppointmentSchema(BaseModel):
    id: str = Field(min_length=1)
    professionalId: str = Field(min_length=1)
    patientId: str = Field(min_length=1)
    patientName: str
    recurrenceId: Optional[str] = None
    recurrenceRuleId: Optional[str] = None
    dateTimeEpoch: int
    durationMinutes: int
    status: Literal[
        "SCHEDULED",
        "CONFIRMED",
        "COMPLETED",
        "PENDING",
        "ABSENT",
        "CANCELLED",
    ]
    notes: Optional[str] = None

class EvolutionRecordSchema(BaseModel):
    id: str = Field(min_length=1)
    appointmentId: Optional[str] = Field(default=None, min_length=1)
    patientId: str = Field(min_length=1)
    professionalId: str = Field(min_length=1)
    dateEpoch: int
    activityPerformed: str
    performanceMetrics: Optional[str] = None
    textualEvolution: str
    observations: Optional[str] = None
    customFields: Optional[Dict[str, Any]] = None

class PatientSchema(BaseModel):
    id: str = Field(min_length=1)
    professionalId: str = Field(min_length=1)
    fullName: str
    motherName: str
    birthDateEpochMillis: int
    phone: Optional[str] = None
    email: Optional[str] = None
    guardianName: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None
    createdAtEpochMillis: int