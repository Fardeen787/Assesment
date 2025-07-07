# populate_test_data.py
"""
Populate the database with test medical data for search testing
"""

import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"

class DataPopulator:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.patients = []
        self.records_created = 0
    
    def setup(self):
        """Login as dr_smith"""
        print("🔐 Logging in...")
        response = requests.post(
            f"{self.base_url}/token",
            data={"username": "dr_smith", "password": "SecurePass123!"}
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Login successful")
            return True
        else:
            print("❌ Login failed - make sure dr_smith is registered")
            return False
    
    def create_patients(self):
        """Create test patients"""
        print("\n👥 Creating test patients...")
        
        test_patients = [
            {
                "first_name": "Alice",
                "last_name": "Johnson",
                "date_of_birth": "1975-03-15",
                "gender": "female",
                "email": "alice.johnson@email.com",
                "phone": "555-0201",
                "address": "100 Maple Ave, Boston, MA 02101",
                "ssn": "111-11-1111"
            },
            {
                "first_name": "Robert",
                "last_name": "Williams",
                "date_of_birth": "1960-08-22",
                "gender": "male",
                "email": "robert.williams@email.com",
                "phone": "555-0202",
                "address": "200 Oak St, Boston, MA 02102",
                "ssn": "222-22-2222"
            },
            {
                "first_name": "Maria",
                "last_name": "Garcia",
                "date_of_birth": "1988-12-10",
                "gender": "female",
                "email": "maria.garcia@email.com",
                "phone": "555-0203",
                "address": "300 Pine Rd, Boston, MA 02103",
                "ssn": "333-33-3333"
            },
            {
                "first_name": "James",
                "last_name": "Chen",
                "date_of_birth": "1970-05-18",
                "gender": "male",
                "email": "james.chen@email.com",
                "phone": "555-0204",
                "address": "400 Elm Way, Boston, MA 02104",
                "ssn": "444-44-4444"
            },
            {
                "first_name": "Linda",
                "last_name": "Davis",
                "date_of_birth": "1982-09-30",
                "gender": "female",
                "email": "linda.davis@email.com",
                "phone": "555-0205",
                "address": "500 Birch Ln, Boston, MA 02105",
                "ssn": "555-55-5555"
            }
        ]
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        for patient_data in test_patients:
            response = requests.post(
                f"{self.base_url}/patients",
                json=patient_data,
                headers=headers
            )
            if response.status_code == 200:
                patient = response.json()
                self.patients.append(patient)
                print(f"✅ Created patient: {patient['first_name']} {patient['last_name']}")
            else:
                print(f"❌ Failed to create patient: {response.text}")
    
    def create_medical_records(self):
        """Create diverse medical records for testing search"""
        print("\n📋 Creating medical records...")
        
        if not self.patients:
            print("❌ No patients available")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Medical record templates for various conditions
        medical_scenarios = [
            # Migraine cases
            {
                "patient_idx": 0,
                "record_type": "consultation",
                "days_ago": 5,
                "chief_complaint": "Severe migraine headache with aura, lasted 6 hours",
                "diagnosis": "Migraine with aura, chronic",
                "treatment": "Prescribed sumatriptan 100mg for acute attacks, started propranolol 80mg daily for prevention",
                "medications": "Sumatriptan 100mg PRN, Propranolol 80mg daily",
                "notes": "Patient reports triggers include stress and lack of sleep. Advised lifestyle modifications."
            },
            {
                "patient_idx": 2,
                "record_type": "consultation",
                "days_ago": 15,
                "chief_complaint": "Recurring tension headaches, worse in afternoon",
                "diagnosis": "Tension-type headache, episodic",
                "treatment": "Prescribed ibuprofen 600mg PRN, stress management techniques",
                "medications": "Ibuprofen 600mg as needed",
                "notes": "Headaches related to work stress. Referred to physical therapy for neck tension."
            },
            
            # Diabetes cases
            {
                "patient_idx": 1,
                "record_type": "consultation",
                "days_ago": 7,
                "chief_complaint": "Diabetes follow-up, blood sugar control review",
                "diagnosis": "Type 2 diabetes mellitus, well-controlled",
                "treatment": "Continue metformin 1000mg twice daily, maintain diet and exercise",
                "medications": "Metformin 1000mg BID",
                "notes": "HbA1c 6.8%, down from 7.2%. Patient adherent to medication and lifestyle changes."
            },
            {
                "patient_idx": 3,
                "record_type": "lab_result",
                "days_ago": 10,
                "chief_complaint": "Routine diabetes screening, fasting glucose elevated",
                "diagnosis": "Type 2 diabetes mellitus, newly diagnosed",
                "treatment": "Started metformin 500mg daily, diabetes education provided",
                "medications": "Metformin 500mg daily",
                "notes": "Fasting glucose 156 mg/dL, HbA1c 7.8%. Referred to diabetes educator."
            },
            
            # Cardiovascular cases
            {
                "patient_idx": 1,
                "record_type": "consultation",
                "days_ago": 30,
                "chief_complaint": "Hypertension follow-up, blood pressure check",
                "diagnosis": "Essential hypertension, stage 1",
                "treatment": "Started lisinopril 10mg daily, low sodium diet advised",
                "medications": "Lisinopril 10mg daily",
                "notes": "BP 145/92, target <130/80. Patient educated on DASH diet."
            },
            {
                "patient_idx": 3,
                "record_type": "consultation",
                "days_ago": 20,
                "chief_complaint": "Chest pain on exertion, shortness of breath",
                "diagnosis": "Stable angina pectoris",
                "treatment": "Started metoprolol 50mg BID, nitroglycerin PRN, cardiac workup ordered",
                "medications": "Metoprolol 50mg twice daily, Nitroglycerin 0.4mg sublingual PRN",
                "notes": "ECG shows mild ST changes. Scheduled for stress test."
            },
            
            # Mental health cases
            {
                "patient_idx": 4,
                "record_type": "consultation",
                "days_ago": 3,
                "chief_complaint": "Anxiety, panic attacks, difficulty sleeping",
                "diagnosis": "Generalized anxiety disorder with panic attacks",
                "treatment": "Started sertraline 50mg daily, lorazepam 0.5mg PRN for acute anxiety",
                "medications": "Sertraline 50mg daily, Lorazepam 0.5mg PRN",
                "notes": "Patient reports work-related stress. Referred to therapist for CBT."
            },
            {
                "patient_idx": 2,
                "record_type": "emergency",
                "days_ago": 25,
                "chief_complaint": "Acute anxiety attack, chest pain, hyperventilation",
                "diagnosis": "Panic attack, ruled out cardiac causes",
                "treatment": "Lorazepam 1mg given, breathing exercises taught",
                "medications": "Lorazepam 1mg stat dose",
                "notes": "ECG normal, troponins negative. Patient calmed with reassurance."
            },
            
            # Hyperlipidemia cases
            {
                "patient_idx": 0,
                "record_type": "lab_result",
                "days_ago": 12,
                "chief_complaint": "Lipid panel results, cholesterol elevated",
                "diagnosis": "Hyperlipidemia, mixed type",
                "treatment": "Started atorvastatin 20mg daily, dietary counseling provided",
                "medications": "Atorvastatin 20mg at bedtime",
                "notes": "Total cholesterol 265, LDL 180, HDL 35, Triglycerides 250. Follow up in 3 months."
            },
            {
                "patient_idx": 4,
                "record_type": "consultation",
                "days_ago": 18,
                "chief_complaint": "Follow-up for high cholesterol treatment",
                "diagnosis": "Hypercholesterolemia, improving",
                "treatment": "Continue rosuvastatin 10mg, increase exercise",
                "medications": "Rosuvastatin 10mg daily",
                "notes": "LDL down to 120 from 160. Patient compliant with statin therapy."
            },
            
            # Respiratory cases
            {
                "patient_idx": 2,
                "record_type": "consultation",
                "days_ago": 8,
                "chief_complaint": "Persistent cough, wheezing, shortness of breath",
                "diagnosis": "Asthma, mild persistent",
                "treatment": "Prescribed albuterol inhaler PRN, budesonide inhaler twice daily",
                "medications": "Albuterol HFA 90mcg PRN, Budesonide 180mcg BID",
                "notes": "Peak flow 75% predicted. Triggers include dust and exercise."
            },
            {
                "patient_idx": 1,
                "record_type": "consultation",
                "days_ago": 14,
                "chief_complaint": "Chronic cough, worse at night, post-nasal drip",
                "diagnosis": "Allergic rhinitis with post-nasal drip",
                "treatment": "Started cetirizine 10mg daily, nasal saline rinses",
                "medications": "Cetirizine 10mg daily",
                "notes": "Allergy testing recommended. Avoid known allergens."
            },
            
            # Musculoskeletal cases
            {
                "patient_idx": 3,
                "record_type": "consultation",
                "days_ago": 6,
                "chief_complaint": "Lower back pain, radiating to left leg",
                "diagnosis": "Lumbar radiculopathy, L5-S1",
                "treatment": "Physical therapy, NSAIDs, muscle relaxant as needed",
                "medications": "Naproxen 500mg BID, Cyclobenzaprine 10mg at bedtime PRN",
                "notes": "MRI shows disc herniation at L5-S1. Conservative management first."
            },
            {
                "patient_idx": 0,
                "record_type": "consultation",
                "days_ago": 22,
                "chief_complaint": "Knee pain and swelling after running",
                "diagnosis": "Patellofemoral pain syndrome",
                "treatment": "Rest, ice, compression, elevation. NSAIDs for pain",
                "medications": "Ibuprofen 400mg TID",
                "notes": "Advised on proper running form and gradual return to activity."
            }
        ]
        
        # Create all medical records
        for scenario in medical_scenarios:
            patient = self.patients[scenario["patient_idx"]]
            visit_date = (datetime.now() - timedelta(days=scenario["days_ago"])).isoformat()
            
            record_data = {
                "patient_id": patient["id"],
                "record_type": scenario["record_type"],
                "visit_date": visit_date,
                "chief_complaint": scenario["chief_complaint"],
                "diagnosis": scenario["diagnosis"],
                "treatment": scenario["treatment"],
                "medications": scenario["medications"],
                "notes": scenario["notes"]
            }
            
            response = requests.post(
                f"{self.base_url}/medical-records",
                json=record_data,
                headers=headers
            )
            
            if response.status_code == 200:
                self.records_created += 1
                print(f"✅ Created {scenario['record_type']} record for {patient['first_name']} - {scenario['diagnosis'][:30]}...")
            else:
                print(f"❌ Failed to create record: {response.text}")
    
    def verify_search(self):
        """Test a few searches to verify data is searchable"""
        print("\n🔍 Verifying search functionality...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        test_searches = [
            "migraine headache",
            "diabetes",
            "anxiety",
            "cholesterol"
        ]
        
        for query in test_searches:
            search_data = {
                "query": query,
                "top_k": 5,
                "anonymize": False,
                "rerank": True
            }
            
            response = requests.post(
                f"{self.base_url}/search",
                json=search_data,
                headers=headers
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Search '{query}': Found {len(results)} results")
            else:
                print(f"❌ Search '{query}' failed")
    
    def run(self):
        """Run the data population process"""
        print("🏥 MEDICAL RECORDS TEST DATA POPULATION")
        print("=" * 60)
        
        if not self.setup():
            return
        
        # Check if we already have data
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/patients", headers=headers)
        
        if response.status_code == 200:
            existing_patients = response.json()
            if len(existing_patients) > 1:  # dr_smith might have created one
                print(f"\n⚠️  Found {len(existing_patients)} existing patients")
                print("Do you want to add more test data? (y/n): ", end="")
                if input().lower() != 'y':
                    print("Exiting without adding data.")
                    return
        
        self.create_patients()
        self.create_medical_records()
        
        print(f"\n📊 Summary:")
        print(f"   - Created {len(self.patients)} patients")
        print(f"   - Created {self.records_created} medical records")
        
        self.verify_search()
        
        print("\n✅ Test data population complete!")
        print("You can now run the search quality test: python test_search_quality.py")


if __name__ == "__main__":
    populator = DataPopulator()
    populator.run()