import hmac
import uuid

from fastapi import FastAPI, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import create_or_update_schema, get_db
import models
import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cria tabelas novas e aplica alterações aditivas às tabelas existentes.
create_or_update_schema()

app = FastAPI(title="AgendaCare API", version="1.0.0")

def professional_response(prof: models.ProfessionalModel):
    return {
        "id": prof.id,
        "name": prof.name,
        "email": prof.email,
        "specialty": prof.specialty,
        "specialtyId": prof.specialty_id,
        "professionalRegister": prof.professional_register,
        "phone": prof.phone,
        "authProvider": prof.auth_provider,
        "firebaseUid": prof.firebase_uid,
    }

@app.get("/")
def read_root():
    return {"status": "online", "app": "AgendaCare API"}

@app.post("/api/v1/auth/register")
def register(prof: schemas.ProfessionalCreate, db: Session = Depends(get_db)):
    existing = db.query(models.ProfessionalModel).filter(models.ProfessionalModel.email == prof.email).first()
    if existing:
        existing.name = prof.name
        existing.specialty = prof.specialty
        existing.specialty_id = prof.specialtyId
        existing.phone = prof.phone
        existing.cpf = prof.cpf
        db.commit()
        return {"status": "success", "id": existing.id, "name": existing.name}
    
    db_prof = models.ProfessionalModel(
        id=prof.id,
        name=prof.name,
        email=prof.email,
        specialty=prof.specialty,
        specialty_id=prof.specialtyId,
        professional_register=prof.professionalRegister,
        cpf=prof.cpf,
        password_hash=pwd_context.hash(prof.password),
        auth_provider="email",
        phone=prof.phone,
        signature_url=prof.signatureUrl
    )
    db.add(db_prof)
    db.commit()
    return {"status": "success", "id": db_prof.id, "name": db_prof.name}

@app.post("/api/v1/auth/login")
def login(creds: schemas.ProfessionalLogin, db: Session = Depends(get_db)):
    prof = db.query(models.ProfessionalModel).filter(models.ProfessionalModel.email == creds.email).first()
    password_valid = False
    if prof and prof.password_hash:
        if pwd_context.identify(prof.password_hash) is None:
            # Migrate passwords stored in plaintext by the previous implementation.
            password_valid = hmac.compare_digest(
                prof.password_hash.encode("utf-8"),
                creds.password.encode("utf-8"),
            )
            if password_valid:
                prof.password_hash = pwd_context.hash(creds.password)
                db.commit()
        else:
            password_valid = pwd_context.verify(creds.password, prof.password_hash)

    if not password_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")

    return professional_response(prof)

@app.post("/api/v1/auth/google", response_model=schemas.ProfessionalResponse)
def google_login(payload: schemas.GoogleLogin, db: Session = Depends(get_db)):
    by_uid = (
        db.query(models.ProfessionalModel)
        .filter(models.ProfessionalModel.firebase_uid == payload.firebase_uid)
        .first()
    )
    by_email = (
        db.query(models.ProfessionalModel)
        .filter(models.ProfessionalModel.email == payload.email)
        .first()
    )
    if by_uid and by_email and by_uid.id != by_email.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O UID e o e-mail pertencem a profissionais diferentes",
        )

    prof = by_uid or by_email
    if prof:
        return professional_response(prof)

    prof = models.ProfessionalModel(
        id=str(uuid.uuid4()),
        name=payload.name,
        email=payload.email,
        specialty="",
        password_hash=None,
        auth_provider="google",
        firebase_uid=payload.firebase_uid,
    )
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return professional_response(prof)

@app.get("/api/v1/patients/{professional_id}")
def get_patients(professional_id: str, db: Session = Depends(get_db)):
    patients = db.query(models.PatientModel).filter(models.PatientModel.professional_id == professional_id).all()
    result = []
    for p in patients:
        result.append({
            "id": p.id,
            "professionalId": p.professional_id,
            "fullName": p.full_name,
            "motherName": p.mother_name,
            "birthDateEpochMillis": p.birth_date_epoch,
            "phone": p.phone,
            "email": p.email,
            "guardianName": p.guardian_name,
            "relationship": p.relationship,
            "notes": p.notes,
            "createdAtEpochMillis": p.created_at_epoch
        })
    return result

@app.post("/api/v1/patients/{professional_id}")
def sync_patient(professional_id: str, patient: schemas.PatientSchema, db: Session = Depends(get_db)):
    p = db.query(models.PatientModel).filter(models.PatientModel.id == patient.id).first()
    if p:
        p.full_name = patient.fullName
        p.mother_name = patient.motherName
        p.birth_date_epoch = patient.birthDateEpochMillis
        p.phone = patient.phone
        p.email = patient.email
        p.guardian_name = patient.guardianName
        p.relationship = patient.relationship
        p.notes = patient.notes
    else:
        p = models.PatientModel(
            id=patient.id,
        professional_id=professional_id,
            full_name=patient.fullName,
            mother_name=patient.motherName,
            birth_date_epoch=patient.birthDateEpochMillis,
            phone=patient.phone,
            email=patient.email,
            guardian_name=patient.guardianName,
            relationship=patient.relationship,
            notes=patient.notes,
            created_at_epoch=patient.createdAtEpochMillis
        )
        db.add(p)
    db.commit()
    return patient