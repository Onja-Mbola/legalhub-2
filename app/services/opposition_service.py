from datetime import timedelta, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.workflow_enums import ProcessStage
from app.db.session import SessionLocal
from app.models.opposition import Opposition
from app.repositories import opposition as opposition_repo
from app.repositories.dossier import get_dossier_by_id
from app.repositories.opposition import get_all_opposition
from app.schemas.opposition import OppositionCreate, OppositionUpdate, OppositionOut
from app.services.email import send_opposition_email_programmer
from app.services.workflow_guard import WorkflowGuard


def create_opposition_service(
        db: Session,
        dossier_id: int,
        jugement_id: int,
        date_notification: datetime,
) -> Opposition:
    dossier = get_dossier_by_id(db, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")

    if dossier.current_stage != ProcessStage.PAR_DEFAUT.value:
        raise HTTPException(
            status_code=400,
            detail="Vous devez d'abord passer par le Choix du Jugement avant de passer à l'Opposition."
        )

    opposition_possible_jusqua = date_notification + timedelta(days=15)

    obj = OppositionCreate(
        dossier_id=dossier_id,
        jugement_id=jugement_id,
        date_notification=date_notification,
        opposition_possible_jusqua=opposition_possible_jusqua,
    )

    reponse = opposition_repo.create_opposition(db, obj)
    WorkflowGuard.advance(dossier, ProcessStage.OPPOSITION, db)
    return reponse


def get_opposition_service(db: Session, opposition_id: int) -> OppositionOut:
    opposition = opposition_repo.get_opposition_by_id(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition non trouvée")
    return opposition


def get_oppositions_by_dossier_service(db: Session, dossier_id: int):
    return opposition_repo.get_oppositions_by_dossier(db, dossier_id)


def update_opposition_service_hafa(db: Session, opposition_id: int, update_data: OppositionUpdate):
    opposition = opposition_repo.update_opposition(db, opposition_id, update_data)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition non trouvée pour mise à jour")
    return opposition


def update_opposition_service(
        db: Session,
        opposition_id: int,
        update_data: OppositionUpdate
) -> Opposition:
    opposition = opposition_repo.get_opposition_by_id(db, opposition_id)
    if not opposition:
        raise HTTPException(status_code=404, detail="Opposition non trouvée")

    if update_data.date_notification is not None:
        update_data.opposition_possible_jusqua = update_data.date_notification + timedelta(days=15)

    updated_opposition = opposition_repo.update_opposition(db, opposition_id, update_data)
    if not updated_opposition:
        raise HTTPException(status_code=400, detail="Échec de la mise à jour de l'opposition")

    return updated_opposition

