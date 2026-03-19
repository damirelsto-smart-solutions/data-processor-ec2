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
    
class RobotEventUpdate(BaseModel):
    event_time: datetime.time
    kpi_name: str
    kpi_value: int
    robot_id: int
    
class RobotEventRequest(BaseModel):
    events: List[RobotEvent]
    
class RobotEventUpdateRequest(BaseModel):
    events: List[RobotEventUpdate]

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
        

@app.put("/update-robot-event")
async def update_robot_event(request: RobotEventUpdateRequest):
    
    # Normalize input
    if isinstance(request, RobotEventUpdate):
        events = [request]
    else:
        events = request.events

    if not events:
        raise HTTPException(status_code=400, detail="No event provided")

    # Ensure all events belong to same robot
    robot_id = events[0].robot_id
    if any(e.robot_id != robot_id for e in events):
        raise HTTPException(status_code=400, detail="Mixed robot_ids not allowed")

    connection = pymysql.connect(**db_config)

    try:
        with connection.cursor() as cursor:

            # 1️⃣ Get latest IDs for Tray / Divider / Pallet
            sql = """
                SELECT id, KPI_name
                FROM robot_public_info
                WHERE robot_id = %s
                  AND time = (
                      SELECT MAX(time)
                      FROM robot_public_info
                      WHERE robot_id = %s
                        AND KPI_name IN ('Tray number', 'Divider number', 'Pallet number')
                  )
                  AND KPI_name IN ('Tray number', 'Divider number', 'Pallet number');
            """

            cursor.execute(sql, (robot_id, robot_id))
            rows = cursor.fetchall()

            # Convert to dictionary: {KPI_name: id}
            ids = {row[1]: row[0] for row in rows}

            if not ids:
                raise HTTPException(status_code=404, detail="No KPI records found")

            # Optional strict check
            expected = {'Tray number', 'Divider number', 'Pallet number'}
            if not expected.issubset(ids.keys()):
                raise HTTPException(status_code=400, detail="Missing KPI rows")

            # 2️⃣ Update query (single reusable SQL)
            update_sql = """
                UPDATE elsto_test_db.robot_public_info
                SET time = %s, KPI_value = %s
                WHERE id = %s
            """

            # 3️⃣ Apply updates
            for event in events:
                kpi_name = event.kpi_name

                if kpi_name not in ids:
                    continue  # skip unknown KPI

                cursor.execute(
                    update_sql,
                    (event.event_time, event.kpi_value, ids[kpi_name])
                )

            # 4️⃣ Commit once
            connection.commit()

        return {
            "message": "Robot event update successfully"
        }

    except Exception as e:
        connection.rollback()  # important safety
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    finally:
        connection.close()
        
        
@app.get("/")
async def root():
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)