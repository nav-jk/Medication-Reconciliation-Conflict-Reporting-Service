async def create_indexes(db):
    collection = db["reconciliations"]

    await collection.create_index("patient_id")
    await collection.create_index("clinic_id")
    await collection.create_index("versions.timestamp")
    await collection.create_index("versions.conflicts.status")