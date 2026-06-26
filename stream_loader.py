import requests
import time

class OpenFDAStreamLoader:
    BASE_URL = "https://api.fda.gov/drug/event.json"

    def __init__(self, database, limit = 100, max_records=None, exact_tables=None):
        self.database = database
        self.limit = limit
        self.max_records = max_records #set to None to stream the whole data
        self.exact_tables = exact_tables

    def stream(self):
        skip = 0
        total_processed = 0

        while True:
            url = f"{self.BASE_URL}?limit={self.limit}&skip={skip}"

            try:
                response = requests.get(url=url, timeout=10)
                data = response.json()

            except Exception as e:
                print("/!\ API error !")
                break

            if "results" not in data:
                print("No result 😣")
                break

            batch = data["results"]

            if len(batch) == 0:
                print("No result 😣")
                break

            for entry in batch:
                self._process_entry(entry)
                total_processed +=1

                if self.max_records and total_processed >= self.max_records:
                    print("Max records reached !")
                    return
                
            skip += self.limit
            time.sleep(0.1)

    def _process_entry(self, entry):
        patient = entry.get("patient", {})
        patient_id = entry.get("safetyreportid", None)
        age = patient.get("patientonsetage", None)
        try:
            age = float(age)
        except:
            age = None
        sex = patient.get("patientsex", None)
        serious = int(entry.get("serious", 0))

        # Patient Table
        patient_row = {
            "patient_id" : patient_id,
            "age" : age,
            "sex" : sex,
            "serious" : serious
        }
        self.database.get_table("patients").update_row(patient_row)

        if self.exact_tables is not None:
            self.exact_tables["patients"].update_row(patient_row)

        # Drugs table
        drugs = patient.get("drug", [])
        for drug in drugs:
            name = drug.get("medicinalproduct", None)
            if name is None:
                continue

            drug_row = {"patient_id": patient_id, "drug_name": name}
            self.database.get_table("drugs").update_row(drug_row)

            if self.exact_tables is not None:
                self.exact_tables["drugs"].update_row(drug_row)

        # Reactions table
        reactions = patient.get("reaction", [])
        for r in reactions:
            reaction = r.get("reactionmeddrapt", None)

            if reaction is None:
                continue

            reaction_row = {"patient_id": patient_id, "reaction": reaction}

            self.database.get_table("reactions").update_row(reaction_row)

            if self.exact_tables is not None:
                self.exact_tables["reactions"].update_row(reaction_row)
