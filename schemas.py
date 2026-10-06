from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field
from typing import Optional, Dict, Any
from typing import Literal

class ProfessionalCreate(BaseModel):
    id: str = Field(min_length=1)
    deviceId: str = Field(min_length=1)
    firebaseUid: Optional[str] = None
    name: str
    email: str
    specialty: str
    specialtyId: Optional[str] = None
    professionalRegister: Optional[str] = None
    cpf: str = Field(min_length=1)
    password: str
    phone: Optional[str] = None
    signatureUrl: Optional[str] = None

class ProfessionalResponse(BaseModel):
    id: str
    name: str
    email: str
    specialty: str
    cpf: str
    planType: Optional[str] = None
    subscriptionStatus: Optional[str] = None
    trialEndsAt: Optional[datetime] = None
    subscriptionExpiresAt: Optional[datetime] = None
    specialtyId: Optional[str] = None
    professionalRegister: Optional[str] = None
    phone: Optional[str] = None

class ProfessionalLogin(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    idToken: str

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("phone", "phone_number"),
    )
    specialty: Optional[str] = None
    email: Optional[str] = None
    specialty_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("specialtyId", "specialty_id"),
    )
    professional_register: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "professionalRegister",
            "professional_register",
        ),
    )
    signature_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("signatureUrl", "signature_url"),
    )

class SubscriptionVerifyRequest(BaseModel):
    purchaseToken: str
    planType: Literal["MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL"]

class ResetValidation(BaseModel):
    cpf: str
    email: str

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