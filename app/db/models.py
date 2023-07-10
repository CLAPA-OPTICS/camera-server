from sqlalchemy import Column, Integer, String
from .database import Base

class CameraParams(Base):
    __tablename__ = "camera_parameters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    cross_line_x = Column(Integer)
    cross_line_y = Column(Integer)
    gain = Column(Integer)
    gamma = Column(Integer)
    contrast = Column(Integer)
