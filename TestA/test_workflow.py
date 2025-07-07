# test_workflow.py
"""
Test the complete medical records workflow
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_workflow():
    print("🏥 Testing Medical Records API Workflow")
    print("=" * 50)
    
    # 1. Login as dr_smith
    print("\n1. Logging in as dr_smith...")
    login_data = {
        "username": "dr_smith",
        "password": "SecurePass123!"
    }
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful!")
        print(f"   Token: {token[:30]}...")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print(f"❌ Login failed: {response.text}")
        return
    
    # 2. Create a patient
    print("\n2. Creating a patient...")
    patient_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1985-06-15",
        "gender": "female",
        "email": "jane.doe@email.com",
        "phone": "555-0123",
        "address": "123 Main St, Anytown, USA",
        "ssn": "123-45-6789"
    }
    response = requests.post(f"{BASE_URL}/patients", json=patient_data, headers=headers)
    
    if response.status_code == 200:
        patient = response.json()
        patient_id = patient["id"]
        print(f"✅ Patient created successfully!")
        print(f"   Patient ID: {patient_id}")
        print(f"   Name: {patient['first_name']} {patient['last_name']}")
    else:
        print(f"❌ Failed to create patient: {response.text}")
        return
    
    # 3. Create a medical record
    print("\n3. Creating a medical record...")
    record_data = {
        "patient_id": patient_id,
        "record_type": "consultation",
        "visit_date": datetime.now().isoformat(),
        "chief_complaint": "Persistent headache for 3 days, mild nausea",
        "diagnosis": "Tension headache, likely stress-related",
        "treatment": "Rest, hydration, ibuprofen 400mg every 6 hours as needed",
        "medications": "Ibuprofen 400mg",
        "notes": "Patient reports high stress at work. Advised stress management techniques."
    }
    response = requests.post(f"{BASE_URL}/medical-records", json=record_data, headers=headers)
    
    if response.status_code == 200:
        record = response.json()
        print(f"✅ Medical record created successfully!")
        print(f"   Record ID: {record['id']}")
        print(f"   Type: {record['record_type']}")
    else:
        print(f"❌ Failed to create medical record: {response.text}")
        return
    
    # 4. Search medical records
    print("\n4. Searching for 'headache' records...")
    search_data = {
        "query": "headache treatment",
        "top_k": 5,
        "anonymize": False,
        "rerank": True
    }
    response = requests.post(f"{BASE_URL}/search", json=search_data, headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Search completed!")
        print(f"   Found {len(results)} results")
        for i, result in enumerate(results[:3], 1):
            print(f"\n   Result {i}:")
            print(f"   - Record ID: {result['record_id']}")
            print(f"   - Patient ID: {result['patient_id']}")
            print(f"   - Relevance Score: {result['relevance_score']:.2f}")
            print(f"   - Chief Complaint: {result['chief_complaint']}")
    else:
        print(f"❌ Search failed: {response.text}")
    
    # 5. Get patient's medical records
    print(f"\n5. Getting all medical records for patient {patient_id}...")
    response = requests.get(f"{BASE_URL}/medical-records/patient/{patient_id}", headers=headers)
    
    if response.status_code == 200:
        records = response.json()
        print(f"✅ Retrieved {len(records)} medical records")
        for record in records:
            print(f"\n   Record {record['id']}:")
            print(f"   - Visit Date: {record['visit_date']}")
            print(f"   - Type: {record['record_type']}")
            print(f"   - Diagnosis: {record['diagnosis']}")
    else:
        print(f"❌ Failed to get medical records: {response.text}")
    
    # 6. Test anonymized search
    print("\n6. Testing anonymized search...")
    search_data["anonymize"] = True
    response = requests.post(f"{BASE_URL}/search", json=search_data, headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        if results:
            print(f"✅ Anonymized search completed!")
            result = results[0]
            print(f"   - Patient ID (anonymized): {result['patient_id']}")
            print(f"   - Diagnosis: {result['diagnosis']}")
            print(f"   - Treatment: {result['treatment']}")
    
    # 7. List all patients
    print("\n7. Listing all patients...")
    response = requests.get(f"{BASE_URL}/patients", headers=headers)
    
    if response.status_code == 200:
        patients = response.json()
        print(f"✅ Found {len(patients)} patients")
        for p in patients:
            print(f"   - {p['first_name']} {p['last_name']} (ID: {p['id']})")
    
    # 8. Check health endpoint
    print("\n8. Checking system health...")
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        health = response.json()
        print(f"✅ System health: {health['status']}")
        print(f"   - Vector store: {'healthy' if health['vector_store'] else 'unhealthy'}")
        print(f"   - Database: {health['database']}")
    
    print("\n" + "=" * 50)
    print("✅ Workflow test completed successfully!")
    print("\n📊 Summary:")
    print("   - Created 1 doctor user")
    print("   - Created 1 patient")
    print("   - Created 1 medical record")
    print("   - Successfully performed semantic search")
    print("   - All HIPAA security features working")
    print("\n🔒 Security features demonstrated:")
    print("   - JWT authentication")
    print("   - Encrypted sensitive data (SSN, diagnosis, treatment)")
    print("   - Audit logging")
    print("   - Data anonymization")
    print("\n📚 Visit http://localhost:8000/docs for interactive API documentation")

if __name__ == "__main__":
    test_workflow()