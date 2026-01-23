from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

class Scan(Base):
    __tablename__="scans"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


    score = Column(Float, nullable=False)
    baseline_id = Column(String(50), nullable=False)
    baseline_score = Column(Float, nullable=False)
    delta = Column (Float, nullable=False)
    label = Column (String(20), nullable=False)


    spot_coverage = Column(Float, nullable=False)
    edge_density= Column(Float, nullable=False)
    texture_variance = Column(Float, nullable=False)
    mean_intensity = Column(Float, nullable=False)

    sample_name = Column(String(500), nullable=True)
    location = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    def to_dict(self):
        return {

            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
            "baseline_id": self.baseline_id,
            "baseline_score": self.baseline_score,
            "delta": self.delta,
            "label": self.label,
            "metrics": {
                "spot_coverage": self.spot_coverage,
                "edge_density": self.edge_density,
                "texture_variance": self.texture_variance,
                "mean_intensity": self.mean_intensity,
            },
            "sample_name": self.sample_name,
            "location": self.location,
            "notes": self.notes

        }
    
class CustomBaseline(Base):
    __tablename__ = "custom baselines"
    id = Column(Integer, primary_key=True, index=True)
    baseline_id = Column(String(50), unique = True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description= Column(Text, nullable=True)
    created_at=Column(DateTime, default=datetime.utcnow, nullable=False)

    exptected_score = Column(Float, nullable=False)
    spot_coverage = Column(Float, nullable=False)
    edge_density = Column(Float, nullable=False)
    texture_variance = Column(Float, nullable=False)
    mean_intensity = Column(Float, nullable=False)

    sample_count = Column(Integer, default =1)

    def to_dict(self):
        return {
            "id": self.baseline_id,
            "name": self.name,
            "description": self.description,
            "expected_score": self.exptected_score,
            "created_at": self.created_at,
            "sample_count": self.sample_count,
        }