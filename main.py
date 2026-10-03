from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import engine, get_db, Base
import models
import schemas

# Cria as tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgendaCare API", version="1.0.0")

@app.get("/")
def read_root():
    return {"status": "online", "app": "AgendaCare API"}

@app.post("/api/v1/auth/register")
def register(prof: schemas.ProfessionalCreate, db: Session = Depends(get_db)):
    existing = db.query(models.ProfessionalModel).filter(models.ProfessionalModel.email == prof.email).first()
    if existing:
        existing.name = prof.name
        existing.specialty = prof.specialty
        existing.phone = prof.phone
        existing.cpf = prof.cpf
        db.commit()
        return {"status": "success", "id": existing.id, "name": existing.name}
    
    db_prof = models.ProfessionalModel(
        id=prof.id,
        name=prof.name,
        email=prof.email,
        specialty=prof.specialty,
        professional_register=prof.professionalRegister,
        cpf=prof.cpf,
        password_hash=prof.password,
        phone=prof.phone,
        signature_url=prof.signatureUrl
    )
    db.add(db_prof)
    db.commit()
    return {"status": "success", "id": db_prof.id, "name": db_prof.name}

@app.post("/api/v1/auth/login")
def login(creds: schemas.ProfessionalLogin, db: Session = Depends(get_db)):
    prof = db.query(models.ProfessionalModel).filter(models.ProfessionalModel.email == creds.email).first()
    if not prof or prof.password_hash != creds.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    
    return {
        "id": prof.id,
        "name": prof.name,
        "email": prof.email,
        "specialty": prof.specialty,
        "professionalRegister": prof.professional_register,
        "phone": prof.phone
    }

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