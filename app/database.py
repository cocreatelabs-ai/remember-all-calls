from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    status = Column(String, default="uploaded")  # uploaded, transcribing, processing, completed, failed
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

class Transcription(Base):
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, nullable=False, index=True)
    transcription_text = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    transcription_job_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    key_topics = Column(Text, nullable=True)  # JSON string
    sentiment = Column(String, nullable=True)  # positive, negative, neutral
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()