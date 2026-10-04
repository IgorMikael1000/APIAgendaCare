import hmac
import uuid

from fastapi import Body, Depends, FastAPI, HTTPException, Path, status
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import create_or_update_schema, get_db
import models
import schemas
from schemas import AppointmentSchema, EvolutionRecordSchema

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
    duplicate_credentials = [
        models.ProfessionalModel.email == prof.email,
    ]
    if prof.cpf is not None:
        duplicate_credentials.append(models.ProfessionalModel.cpf == prof.cpf)
    if prof.phone is not None:
        duplicate_credentials.append(models.ProfessionalModel.phone == prof.phone)

    existing = (
        db.query(models.ProfessionalModel)
        .filter(or_(*duplicate_credentials))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail, CPF ou telefone já cadastrados no sistema",
        )
    if db.query(models.ProfessionalModel.id).filter(
        models.ProfessionalModel.id == prof.id
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ID de profissional já cadastrado no sistema",
        )

    password_bytes = prof.password.encode("utf-8")[:72]
    safe_password = password_bytes.decode("utf-8", errors="ignore")
    password_hash = pwd_context.hash(safe_password)

    db_prof = models.ProfessionalModel(
        id=prof.id,
        name=prof.name,
        email=prof.email,
        specialty=prof.specialty,
        specialty_id=prof.specialtyId,
        professional_register=prof.professionalRegister,
        cpf=prof.cpf,
        password_hash=password_hash,
        auth_provider="email",
        phone=prof.phone,
        signature_url=prof.signatureUrl
    )
    db.add(db_prof)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail, CPF, telefone ou ID já cadastrados no sistema",
        )
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
                password_bytes = creds.password.encode("utf-8")[:72]
                safe_password = password_bytes.decode("utf-8", errors="ignore")
                prof.password_hash = pwd_context.hash(safe_password)
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
    if patient.professionalId != professional_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O paciente deve pertencer ao profissional informado",
        )

    p = (
        db.query(models.PatientModel)
        .filter(
            models.PatientModel.id == patient.id,
            models.PatientModel.professional_id == professional_id,
        )
        .first()
    )
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
        owned_by_another_professional = (
            db.query(models.PatientModel.id)
            .filter(
                models.PatientModel.id == patient.id,
                models.PatientModel.professional_id != professional_id,
            )
            .first()
        )
        if owned_by_another_professional:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="O ID do paciente pertence a outro profissional",
            )

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

@app.get(
    "/api/v1/appointments/{professionalId}",
    response_model=list[AppointmentSchema],
)
def get_appointments(
    professional_id: str = Path(..., alias="professionalId"),
    db: Session = Depends(get_db),
):
    appointments = (
        db.query(models.AppointmentModel)
        .filter(models.AppointmentModel.professional_id == professional_id)
        .all()
    )
    return [
        {
            "id": appointment.id,
            "professionalId": appointment.professional_id,
            "patientId": appointment.patient_id,
            "patientName": appointment.patient_name,
            "recurrenceId": appointment.recurrence_id,
            "recurrenceRuleId": appointment.recurrence_rule_id,
            "dateTimeEpoch": appointment.date_time_epoch,
            "durationMinutes": appointment.duration_minutes,
            "status": appointment.status,
            "notes": appointment.notes,
        }
        for appointment in appointments
    ]

@app.post(
    "/api/v1/appointments/{professionalId}",
    response_model=list[AppointmentSchema],
)
def sync_appointments(
    professional_id: str = Path(..., alias="professionalId"),
    appointments: list[AppointmentSchema] = Body(...),
    db: Session = Depends(get_db),
):
    appointment_ids = [appointment.id for appointment in appointments]
    if len(appointment_ids) != len(set(appointment_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A lista contém IDs de agendamento duplicados",
        )
    if any(appointment.professionalId != professional_id for appointment in appointments):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Todos os agendamentos devem pertencer ao profissional informado",
        )

    existing_appointments = (
        db.query(models.AppointmentModel)
        .filter(
            models.AppointmentModel.id.in_(appointment_ids),
            models.AppointmentModel.professional_id == professional_id,
        )
        .all()
    )
    appointments_by_id = {appointment.id: appointment for appointment in existing_appointments}
    foreign_appointments = (
        db.query(models.AppointmentModel.id)
        .filter(
            models.AppointmentModel.id.in_(appointment_ids),
            models.AppointmentModel.professional_id != professional_id,
        )
        .first()
    )
    if foreign_appointments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um ou mais IDs de agendamento pertencem a outro profissional",
        )

    patient_ids = {appointment.patientId for appointment in appointments}
    foreign_patients = (
        db.query(models.PatientModel.id)
        .filter(
            models.PatientModel.id.in_(patient_ids),
            models.PatientModel.professional_id != professional_id,
        )
        .first()
    )
    if foreign_patients:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um ou mais pacientes pertencem a outro profissional",
        )

    for appointment in appointments:
        db_appointment = appointments_by_id.get(appointment.id)
        if db_appointment is None:
            db_appointment = models.AppointmentModel(id=appointment.id)
            db.add(db_appointment)

        db_appointment.professional_id = professional_id
        db_appointment.patient_id = appointment.patientId
        db_appointment.patient_name = appointment.patientName
        db_appointment.recurrence_id = appointment.recurrenceId
        db_appointment.recurrence_rule_id = appointment.recurrenceRuleId
        db_appointment.date_time_epoch = appointment.dateTimeEpoch
        db_appointment.duration_minutes = appointment.durationMinutes
        db_appointment.status = appointment.status
        db_appointment.notes = appointment.notes

    db.commit()
    return appointments

@app.get(
    "/api/v1/evolutions/{professionalId}",
    response_model=list[EvolutionRecordSchema],
)
def get_evolutions(
    professional_id: str = Path(..., alias="professionalId"),
    db: Session = Depends(get_db),
):
    evolutions = (
        db.query(models.EvolutionRecordModel)
        .filter(models.EvolutionRecordModel.professional_id == professional_id)
        .all()
    )
    return [
        {
            "id": evolution.id,
            "appointmentId": evolution.appointment_id,
            "patientId": evolution.patient_id,
            "professionalId": evolution.professional_id,
            "dateEpoch": evolution.date_epoch,
            "activityPerformed": evolution.activity_performed,
            "performanceMetrics": evolution.performance_metrics,
            "textualEvolution": evolution.textual_evolution,
            "observations": evolution.observations,
            "customFields": evolution.custom_fields,
        }
        for evolution in evolutions
    ]

@app.post(
    "/api/v1/evolutions/{professionalId}",
    response_model=list[EvolutionRecordSchema],
)
def sync_evolutions(
    professional_id: str = Path(..., alias="professionalId"),
    evolutions: list[EvolutionRecordSchema] = Body(...),
    db: Session = Depends(get_db),
):
    evolution_ids = [evolution.id for evolution in evolutions]
    if len(evolution_ids) != len(set(evolution_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A lista contém IDs de evolução duplicados",
        )
    if any(evolution.professionalId != professional_id for evolution in evolutions):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Todas as evoluções devem pertencer ao profissional informado",
        )

    existing_evolutions = (
        db.query(models.EvolutionRecordModel)
        .filter(
            models.EvolutionRecordModel.id.in_(evolution_ids),
            models.EvolutionRecordModel.professional_id == professional_id,
        )
        .all()
    )
    evolutions_by_id = {evolution.id: evolution for evolution in existing_evolutions}
    foreign_evolutions = (
        db.query(models.EvolutionRecordModel.id)
        .filter(
            models.EvolutionRecordModel.id.in_(evolution_ids),
            models.EvolutionRecordModel.professional_id != professional_id,
        )
        .first()
    )
    if foreign_evolutions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um ou mais IDs de evolução pertencem a outro profissional",
        )

    patient_ids = {evolution.patientId for evolution in evolutions}
    foreign_patients = (
        db.query(models.PatientModel.id)
        .filter(
            models.PatientModel.id.in_(patient_ids),
            models.PatientModel.professional_id != professional_id,
        )
        .first()
    )
    if foreign_patients:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um ou mais pacientes pertencem a outro profissional",
        )

    appointment_ids = {
        evolution.appointmentId
        for evolution in evolutions
        if evolution.appointmentId is not None
    }
    foreign_linked_appointments = (
        db.query(models.AppointmentModel.id)
        .filter(
            models.AppointmentModel.id.in_(appointment_ids),
            models.AppointmentModel.professional_id != professional_id,
        )
        .first()
    )
    if foreign_linked_appointments:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um ou mais agendamentos pertencem a outro profissional",
        )

    for evolution in evolutions:
        db_evolution = evolutions_by_id.get(evolution.id)
        if db_evolution is None:
            db_evolution = models.EvolutionRecordModel(id=evolution.id)
            db.add(db_evolution)

        db_evolution.appointment_id = evolution.appointmentId
        db_evolution.patient_id = evolution.patientId
        db_evolution.professional_id = professional_id
        db_evolution.date_epoch = evolution.dateEpoch
        db_evolution.activity_performed = evolution.activityPerformed
        db_evolution.performance_metrics = evolution.performanceMetrics
        db_evolution.textual_evolution = evolution.textualEvolution
        db_evolution.observations = evolution.observations
        db_evolution.custom_fields = evolution.customFields

    db.commit()
    return evolutions