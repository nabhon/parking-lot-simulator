from tinydb import TinyDB, Query
from datetime import datetime
import math

db = TinyDB("parking_data.json")
plates = db.table("plates")
Plate = Query()

FIRST_HOUR_FEE = 20.0
ADDITIONAL_HOUR_FEE = 40.0

def handle_entry_detection(plate_number):
    record = plates.get((Plate.plate_number == plate_number) & (Plate.exit_time == None))
    if record:
        return "already_inside", 0.0

    plates.insert({
        "plate_number": plate_number,
        "entry_time": datetime.now().isoformat(),
        "exit_time": None,
        "fee": None
    })
    return "entry", 0.0

def handle_exit_detection(plate_number):
    record = plates.get((Plate.plate_number == plate_number) & (Plate.exit_time == None))
    if not record:
        return "not_found", 0.0

    exit_time = datetime.now()
    entry_time = datetime.fromisoformat(record["entry_time"])
    duration_hours = (exit_time - entry_time).total_seconds() / 3600
    
    # Round up to the next hour
    total_hours = math.ceil(duration_hours)
    
    # Calculate fee: first hour at 20 baht, remaining hours at 40 baht
    if total_hours <= 1:
        fee = FIRST_HOUR_FEE
    else:
        fee = FIRST_HOUR_FEE + (total_hours - 1) * ADDITIONAL_HOUR_FEE

    plates.update({
        "exit_time": exit_time.isoformat(),
        "fee": fee
    }, doc_ids=[record.doc_id])

    return "exit", fee
