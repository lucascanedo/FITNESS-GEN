from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    cpf = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    birth_date = Column(DateTime, nullable=False)
    sex = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def age(self):
        """Retorna a idade atual baseada na data de nascimento."""
        today = datetime.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    # Relacionamento: Um estudante pode ter várias avaliações e planos
    assessments = relationship("Assessment", back_populates="student")
    plans = relationship("Plan", back_populates="student")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    height_m = Column(Float)
    weight_kg = Column(Float)
    chest_cm = Column(Float)
    waist_cm = Column(Float)
    hips_cm = Column(Float)
    left_arm_cm = Column(Float)
    right_arm_cm = Column(Float)
    left_thigh_cm = Column(Float)
    right_thigh_cm = Column(Float)
    left_calf_cm = Column(Float)
    right_calf_cm = Column(Float)
    body_fat_percent = Column(Float)
    muscle_mass_kg = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    objectives = Column(JSON)   # JSON string
    posture = Column(JSON)      # JSON string
    injuries = Column(JSON)     # JSON string
    restrictions = Column(JSON) # JSON string
    history = Column(JSON)      # JSON string
    level = Column(String)
    freq_per_week = Column(Integer)
    session_time_min = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="assessments")
    plans = relationship("Plan", back_populates="assessment")

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    plan_json = Column(JSON)  # JSON string com treino do LLM
    created_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="plans")
    student = relationship("Student", back_populates="plans")
