from fastapi import FastAPI, HTTPException
import pymysql
from pydantic import BaseModel
import json
import datetime

app = FastAPI()

# Database config
db_config = {
    'host': 'elstotestdb.c10mcecamvcb.eu-north-1.rds.amazonaws.com',
    'user': 'elstoAdmin',
    'password': 'ElstoDashboardDatabase2026!',
    'database': 'elsto_test_db',
    'port': 3306
}

class RobotEventRequest(BaseModel):
    event_date: datetime.date
    event_time: datetime.time
    kpi_name: str
    kpi_value: int
    kpi_explanation: str
    robot_id: int

@app.post("/log-robot-event")
async def log_robot_event(request: RobotEventRequest):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO robot_public_info 
            (date, time, KPI_name, KPI_value, KPI_explanation, robot_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                request.event_date,
                request.event_time,
                request.kpi_name,
                request.kpi_value,
                request.kpi_explanation,
                request.robot_id
            ))
        connection.commit()
        return {"message": "Robot event logged successfully", "id": cursor.lastrowid}
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