from sqlalchemy.orm import Session

from . import models, schemas


def get_camera_params(db: Session, camera_id: int):
    return db.query(models.CameraParams).filter(models.CameraParams.id == camera_id).first()


def get_camera_params(db: Session, camera_name: int):
    return db.query(models.CameraParams).filter(models.CameraParams.id == camera_name).first()


def create_camera_params(db: Session, item: schemas.ParamsCreate):
    db_item = models.CameraParams(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
