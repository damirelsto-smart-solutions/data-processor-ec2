from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime, date, time
from pydantic import BaseModel

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@your-rds-endpoint:3306/your_database")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the data model
class RobotPublicInfo(Base):
    __tablename__ = "robot_public_info"

    id = Column(Integer, primary_key=True, index=True)  # Assuming an auto-increment ID
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    KPI_name = Column(String(255), nullable=False)
    KPI_value = Column(Integer, nullable=False)
    KPI_explanation = Column(Text, nullable=False)
    robot_id = Column(String(255), nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Pydantic model for request
class RobotEventRequest(BaseModel):
    event_date: date
    event_time: time
    kpi_name: str
    kpi_value: int
    kpi_explanation: str
    robot_id: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/log-robot-event")
async def log_robot_event(request: RobotEventRequest):
    db = SessionLocal()
    try:
        new_entry = RobotPublicInfo(
            date=request.event_date,
            time=request.event_time,
            KPI_name=request.kpi_name,
            KPI_value=request.kpi_value,
            KPI_explanation=request.kpi_explanation,
            robot_id=request.robot_id
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return {"message": "Robot event logged successfully", "id": new_entry.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging robot event: {str(e)}")
    finally:
        db.close()

# Another POST endpoint example - perhaps for batch logging
@app.post("/log-multiple-robot-events")
async def log_multiple_robot_events(requests: list[RobotEventRequest]):
    db = SessionLocal()
    try:
        entries = []
        for req in requests:
            entry = RobotPublicInfo(
                date=req.event_date,
                time=req.event_time,
                KPI_name=req.kpi_name,
                KPI_value=req.kpi_value,
                KPI_explanation=req.kpi_explanation,
                robot_id=req.robot_id
            )
            entries.append(entry)
        db.add_all(entries)
        db.commit()
        for entry in entries:
            db.refresh(entry)
        return {"message": f"{len(entries)} robot events logged successfully", "ids": [e.id for e in entries]}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging robot events: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
