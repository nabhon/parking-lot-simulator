from tinydb import TinyDB, Query
from datetime import datetime

db = TinyDB("parking_data.json")
plates = db.table("plates")
Plate = Query()

FEE_PER_HOUR = 20.0

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
    duration = (exit_time - entry_time).total_seconds() / 3600
    fee = round(duration * FEE_PER_HOUR, 2)

    plates.update({
        "exit_time": exit_time.isoformat(),
        "fee": fee
    }, doc_ids=[record.doc_id])

    return "exit", fee
