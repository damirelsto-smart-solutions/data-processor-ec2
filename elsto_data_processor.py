from fastapi import FastAPI, HTTPException
import pymysql
from pydantic import BaseModel
import json
import datetime
from typing import List, Union

app = FastAPI()

# Database config
db_config = {
    'host': 'elstotestdb.c10mcecamvcb.eu-north-1.rds.amazonaws.com',
    'user': 'elstoAdmin',
    'password': 'ElstoDashboardDatabase2026!',
    'database': 'elsto_test_db',
    'port': 3306
}

class RobotEvent(BaseModel):
    event_date: datetime.date
    event_time: datetime.time
    kpi_name: str
    kpi_value: int
    kpi_explanation: str
    robot_id: int
    
class RobotEventRequest(BaseModel):
    events: List[RobotEvent]

@app.post("/log-robot-event")
async def log_robot_event(request: Union[RobotEvent, RobotEventRequest]):
    if isinstance(request, RobotEvent):
        events = [request]
    else:
        events = request.events
    if not events:
        raise HTTPException(status_code=400, detail="No event provided")
    
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO robot_public_info 
            (date, time, KPI_name, KPI_value, KPI_explanation, robot_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            values = []
            for event in events:
                values.append((
                    event.event_date,
                    event.event_time,
                    event.kpi_name,
                    event.kpi_value,
                    event.kpi_explanation,
                    event.robot_id
                ))
                
            cursor.executemany(sql, values)
        connection.commit()
        return {
            "message": "Robot event logged successfully", 
            "id": cursor.lastrowid,
            "event_count": len(events)
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        connection.close()

@app.get("/")
async def root():
    return {"message": "Use POST /log-robot-event to save data"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)