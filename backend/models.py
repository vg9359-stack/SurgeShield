import uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class Dam(Base):
    __tablename__ = "dams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    height_m = Column(Float, nullable=False)
    storage_volume_mcm = Column(Float, nullable=False)

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    population = Column(Integer, default=0)
    elevation_m = Column(Float)

class SimulationRun(Base):
    __tablename__ = "simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dam_id = Column(Integer, ForeignKey("dams.id"), nullable=True)
    failure_type = Column(String(50))
    peak_discharge_m3s = Column(Float)
    formation_time_min = Column(Float)
    breach_width_m = Column(Float)
    run_at = Column(DateTime(timezone=True), server_default=func.now())