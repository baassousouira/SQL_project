from sketches import TableSketch
from stream_loader import OpenFDAStreamLoader
from engine import MiniSqlEngine, SketchDB

# (1) Create a TableSketch
db = SketchDB()

db.add_table("patients", TableSketch())
db.add_table("drugs", TableSketch())
db.add_table("reactions", TableSketch())

# (2) Stream some FAERS data
loader = OpenFDAStreamLoader(database=db, max_records=500)
print("🌀 Streaming FAERS data... can take a while 🥱")

loader.stream()
print("Streaming DONE 🕺🏼")

# (3) Create an SQL motor
engine = MiniSqlEngine(db)
print("Engine created 😎")

# (4) Test some requests
queries = [
    "SELECT COUNT(*) FROM patients",
    "SELECT AVG(age) FROM patients",
    "SELECT COUNT(*) FROM drugs WHERE drug_name='IBUPROFEN'",
    "SELECT COUNT(*) FROM reactions WHERE reaction='HEADACHE'",
    "SELECT COUNT(*) FROM drugs, reactions WHERE drugs.patient_id = reactions.patient_id"
]

for query in queries:
    print("\nRequest : ", query)
    print("Approxiamte result: ", engine.execute(query=query))