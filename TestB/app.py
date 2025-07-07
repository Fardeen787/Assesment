# app.py
import streamlit as st
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

# Import from local modules
from orchestrator import EnhancedMedicalConsultationOrchestrator
from models import (
    PatientInfo, 
    ConsultationState, 
    Severity, 
    Symptom,
    MedicalCondition,
    DrugInteraction,
    HealthcareProvider,
    Diagnosis,
    Recommendation
)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = EnhancedMedicalConsultationOrchestrator()
    st.session_state.consultation_state = None
    st.session_state.conversation = []
    st.session_state.api_status = "🟢 Connected"

st.set_page_config(
    page_title="Enhanced Medical Diagnostic Assistant",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .emergency-banner {
        background-color: #ff4444;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-weight: bold;
        text-align: center;
    }
    .api-status {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 5px 10px;
        background-color: #f0f0f0;
        border-radius: 5px;
        font-size: 12px;
    }
    .symptom-card {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #007bff;
    }
    .diagnosis-card {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #b8daff;
    }
    .provider-card {
        background-color: #f0f8ff;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# API Status indicator
st.markdown(f'<div class="api-status">UltraSafe API: {st.session_state.api_status}</div>', 
           unsafe_allow_html=True)

st.title("🏥 Enhanced Medical Diagnostic Assistant")
st.markdown("*Powered by UltraSafe Medical APIs*")

# Emergency Banner
st.markdown("""
<div class="emergency-banner">
    ⚠️ MEDICAL EMERGENCY? CALL 911 IMMEDIATELY ⚠️
</div>
""", unsafe_allow_html=True)

# Medical Disclaimer
with st.expander("📋 Important Medical Disclaimer", expanded=False):
    st.markdown("""
    This AI-powered medical information system:
    - ✅ Provides general medical information based on reported symptoms
    - ✅ Suggests possible conditions for discussion with healthcare providers
    - ✅ Checks for potential drug interactions
    - ✅ Helps find appropriate healthcare providers
    
    This system DOES NOT:
    - ❌ Replace professional medical advice
    - ❌ Provide definitive diagnoses
    - ❌ Prescribe medications or treatments
    - ❌ Handle medical emergencies
    
    **Always consult qualified healthcare providers for medical concerns.**
    """)

# Sidebar for patient information
with st.sidebar:
    st.header("👤 Patient Information")
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=1, max_value=120, value=30)
    with col2:
        gender = st.selectbox("Gender", ["male", "female", "other"])
    
    st.subheader("📍 Location & Insurance")
    location = st.text_input("City, State", placeholder="e.g., New York, NY")
    insurance = st.selectbox("Insurance Provider", 
                           ["None", "Blue Cross", "Aetna", "United Healthcare", 
                            "Cigna", "Kaiser", "Other"])
    
    st.subheader("🏥 Medical History")
    medical_history = st.multiselect(
        "Select any that apply:",
        ["Diabetes", "Hypertension", "Heart Disease", "Asthma", 
         "Arthritis", "Depression", "Anxiety", "None"]
    )
    
    st.subheader("💊 Current Medications")
    medications = st.text_area("List current medications (one per line)", 
                             help="Include dosage if known")
    
    st.subheader("🚫 Allergies")
    allergies = st.text_area("List known allergies (one per line)")
    
    if st.button("🚀 Start Consultation", type="primary", use_container_width=True):
        # Initialize consultation
        patient_info = PatientInfo(
            age=age,
            gender=gender,
            medical_history=medical_history if medical_history != ["None"] else [],
            current_medications=medications.split('\n') if medications else [],
            allergies=allergies.split('\n') if allergies else [],
            location=location if location else None,
            insurance=insurance if insurance != "None" else None
        )
        
        st.session_state.consultation_state = ConsultationState(
            session_id=str(uuid.uuid4()),
            patient_info=patient_info
        )
        
        # Run initial consultation step
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        st.session_state.consultation_state = loop.run_until_complete(
            st.session_state.orchestrator._start_consultation(st.session_state.consultation_state)
        )

# Main consultation area
if st.session_state.consultation_state:
    # Progress indicator
    progress_steps = {
        "interview": 0.2,
        "symptom_verification": 0.3,
        "knowledge_retrieval": 0.4,
        "interaction_check": 0.5,
        "diagnosis": 0.7,
        "recommendation": 0.85,
        "provider_search": 0.95,
        "completed": 1.0
    }
    
    current_progress = progress_steps.get(st.session_state.consultation_state.current_step, 0)
    st.progress(current_progress)
    st.caption(f"Current Step: {st.session_state.consultation_state.current_step.replace('_', ' ').title()}")
    
    # Display conversation
    st.subheader("💬 Consultation Chat")
    
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.consultation_state.conversation_history:
            if message['role'] == 'assistant':
                st.markdown(f"**🤖 Medical Assistant:** {message['content']}")
            else:
                st.markdown(f"**👤 You:** {message['content']}")
    
    # Input for symptoms
    if st.session_state.consultation_state.current_step == "interview":
        with st.form("symptom_form"):
            user_input = st.text_area("Describe your symptoms in detail:", 
                                    help="Include when they started, severity, and any triggers")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("Submit Response", type="primary", use_container_width=True)
            with col2:
                skip = st.form_submit_button("Skip to Analysis", use_container_width=True)
            
            if submitted and user_input:
                # Process user input asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                symptoms = loop.run_until_complete(
                    st.session_state.orchestrator.interview_agent.process_response(
                        user_input,
                        st.session_state.consultation_state
                    )
                )
                
                st.session_state.consultation_state.symptoms.extend(symptoms)
                st.session_state.consultation_state.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Display extracted symptoms
                if symptoms:
                    st.success(f"✅ Identified {len(symptoms)} symptom(s)")
                    for symptom in symptoms:
                        st.markdown(f'<div class="symptom-card">**{symptom.name}** - {symptom.severity}</div>', 
                                  unsafe_allow_html=True)
                
                # Continue workflow
                st.session_state.consultation_state = loop.run_until_complete(
                    st.session_state.orchestrator._conduct_interview(st.session_state.consultation_state)
                )
                
                st.rerun()
                
            elif skip:
                # Proceed to analysis if we have enough symptoms
                if len(st.session_state.consultation_state.symptoms) >= 1:
                    st.session_state.consultation_state.current_step = "verify_symptoms"
                    st.rerun()
                else:
                    st.error("Please describe at least one symptom before proceeding.")
    
    # Show current symptoms
    if st.session_state.consultation_state.symptoms:
        with st.expander(f"📋 Current Symptoms ({len(st.session_state.consultation_state.symptoms)})", expanded=True):
            for symptom in st.session_state.consultation_state.symptoms:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{symptom.name}**")
                    if symptom.description:
                        st.caption(symptom.description)
                with col2:
                    severity_colors = {
                        Severity.LOW: "🟢",
                        Severity.MODERATE: "🟡",
                        Severity.HIGH: "🟠",
                        Severity.CRITICAL: "🔴"
                    }
                    st.write(f"{severity_colors.get(symptom.severity, '⚪')} {symptom.severity}")
                with col3:
                    if symptom.duration:
                        st.caption(f"Duration: {symptom.duration}")
    
    # Show analysis progress
    if st.session_state.consultation_state.current_step in ["verify_symptoms", "knowledge_retrieval", 
                                                           "interaction_check", "diagnosis"]:
        with st.spinner(f"🔍 Analyzing your symptoms using UltraSafe medical database..."):
            # Run the analysis workflow
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Execute remaining workflow steps
            if st.session_state.consultation_state.current_step == "verify_symptoms":
                st.session_state.consultation_state = loop.run_until_complete(
                    st.session_state.orchestrator._verify_symptoms(st.session_state.consultation_state)
                )
                st.session_state.consultation_state.current_step = "knowledge_retrieval"
                
            if st.session_state.consultation_state.current_step == "knowledge_retrieval":
                st.session_state.consultation_state = loop.run_until_complete(
                    st.session_state.orchestrator._retrieve_knowledge(st.session_state.consultation_state)
                )
                st.session_state.consultation_state.current_step = "interaction_check"
                
            if st.session_state.consultation_state.current_step == "interaction_check":
                st.session_state.consultation_state = loop.run_until_complete(
                    st.session_state.orchestrator._check_interactions(st.session_state.consultation_state)
                )
                st.session_state.consultation_state.current_step = "diagnosis"
                
            if st.session_state.consultation_state.current_step == "diagnosis":
                st.session_state.consultation_state = loop.run_until_complete(
                    st.session_state.orchestrator._generate_diagnoses(st.session_state.consultation_state)
                )
                st.session_state.consultation_state.current_step = "recommendation"
                
            st.rerun()
    
    # Generate recommendations
    if st.session_state.consultation_state.current_step == "recommendation":
        with st.spinner("📝 Generating personalized recommendations..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            st.session_state.consultation_state = loop.run_until_complete(
                st.session_state.orchestrator._generate_recommendations(st.session_state.consultation_state)
            )
            st.session_state.consultation_state.current_step = "provider_search"
            st.rerun()
    
    # Find providers
    if st.session_state.consultation_state.current_step == "provider_search":
        with st.spinner("🔍 Finding healthcare providers in your area..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            st.session_state.consultation_state = loop.run_until_complete(
                st.session_state.orchestrator._find_providers(st.session_state.consultation_state)
            )
            st.session_state.consultation_state = loop.run_until_complete(
                st.session_state.orchestrator._end_consultation(st.session_state.consultation_state)
            )
            st.rerun()
    
    # Show results when consultation is complete
    if st.session_state.consultation_state.current_step == "completed":
        st.markdown("---")
        st.header("📊 Consultation Results")
        
        # Drug Interaction Warnings
        if st.session_state.consultation_state.drug_interactions:
            st.error("⚠️ **Drug Interaction Warnings Detected**")
            for interaction in st.session_state.consultation_state.drug_interactions:
                with st.expander(f"💊 {interaction.drug1} + {interaction.drug2} ({interaction.severity})", expanded=True):
                    st.write(f"**Description:** {interaction.description}")
                    st.write("**Recommendations:**")
                    for rec in interaction.recommendations:
                        st.write(f"- {rec}")
        
        # Display diagnoses
        if st.session_state.consultation_state.diagnoses:
            st.subheader("🔍 Possible Conditions")
            
            tabs = st.tabs([f"{d.condition.name}" for d in st.session_state.consultation_state.diagnoses[:3]])
            
            for i, (tab, diagnosis) in enumerate(zip(tabs, st.session_state.consultation_state.diagnoses[:3])):
                with tab:
                    # Confidence meter
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f'<div class="diagnosis-card">', unsafe_allow_html=True)
                        st.write(f"**Condition:** {diagnosis.condition.name}")
                        if diagnosis.condition.icd_code:
                            st.caption(f"ICD Code: {diagnosis.condition.icd_code}")
                        st.write(f"**Description:** {diagnosis.condition.description}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.metric("Confidence", f"{diagnosis.confidence:.0%}")
                        if diagnosis.condition.prevalence:
                            st.metric("Prevalence", f"{diagnosis.condition.prevalence:.1%}")
                    
                    # Detailed Analysis
                    with st.expander("📋 Detailed Analysis", expanded=True):
                        st.write(f"**Clinical Reasoning:** {diagnosis.reasoning}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**✅ Supporting Symptoms:**")
                            for symptom in diagnosis.supporting_symptoms:
                                st.write(f"- {symptom}")
                        
                        with col2:
                            st.write("**❓ Missing Symptoms:**")
                            for symptom in diagnosis.missing_symptoms[:3]:
                                st.write(f"- {symptom}")
                        
                        if diagnosis.recommended_tests:
                            st.write("**🔬 Recommended Diagnostic Tests:**")
                            for test in diagnosis.recommended_tests:
                                st.write(f"- {test}")
                        
                        if diagnosis.differential_diagnoses:
                            st.write("**🔄 Differential Diagnoses to Consider:**")
                            st.write(", ".join(diagnosis.differential_diagnoses))
                    
                    # Treatment Options
                    if diagnosis.condition.treatment_options:
                        with st.expander("💊 Treatment Options", expanded=False):
                            for treatment in diagnosis.condition.treatment_options:
                                st.write(f"- {treatment}")
        
        # Display recommendations
        st.subheader("💡 Recommendations")
        
        # Sort recommendations by urgency
        sorted_recs = sorted(st.session_state.consultation_state.recommendations, 
                           key=lambda x: [Severity.CRITICAL, Severity.HIGH, Severity.MODERATE, Severity.LOW].index(x.urgency))
        
        for rec in sorted_recs:
            urgency_colors = {
                Severity.LOW: ("🟢", "success"),
                Severity.MODERATE: ("🟡", "warning"),
                Severity.HIGH: ("🟠", "warning"),
                Severity.CRITICAL: ("🔴", "error")
            }
            
            emoji, alert_type = urgency_colors.get(rec.urgency, ("⚪", "info"))
            
            with st.expander(f"{emoji} {rec.action} (Urgency: {rec.urgency})", expanded=rec.urgency in [Severity.HIGH, Severity.CRITICAL]):
                st.write(f"**Why:** {rec.reasoning}")
                
                if rec.next_steps:
                    st.write("**What to do:**")
                    for i, step in enumerate(rec.next_steps, 1):
                        st.write(f"{i}. {step}")
                
                if rec.warnings:
                    for warning in rec.warnings:
                        st.warning(f"⚠️ {warning}")
                
                if rec.estimated_cost_range:
                    st.info(f"💰 Estimated Cost: {rec.estimated_cost_range}")
                
                # Healthcare Providers
                if rec.providers:
                    st.write("**🏥 Suggested Healthcare Providers:**")
                    for provider in rec.providers:
                        st.markdown(f'<div class="provider-card">', unsafe_allow_html=True)
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{provider.name}**")
                            st.caption(f"{provider.specialty} • {provider.location}")
                            if provider.accepts_insurance and st.session_state.consultation_state.patient_info.insurance in provider.accepts_insurance:
                                st.success(f"✅ Accepts {st.session_state.consultation_state.patient_info.insurance}")
                        with col2:
                            if provider.phone:
                                st.write(f"📞 {provider.phone}")
                            if provider.rating:
                                st.write(f"⭐ {provider.rating}/5.0")
                        st.markdown('</div>', unsafe_allow_html=True)
        
        # API Usage Statistics
        with st.expander("📊 Consultation Statistics", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("API Calls Made", len(st.session_state.consultation_state.api_calls_made))
            with col2:
                st.metric("Conditions Analyzed", len(st.session_state.consultation_state.metadata.get('retrieved_conditions', [])))
            with col3:
                st.metric("Symptoms Verified", len(st.session_state.consultation_state.symptoms))
            
            if st.session_state.consultation_state.api_calls_made:
                st.caption("API Call Details:")
                for call in st.session_state.consultation_state.api_calls_made:
                    st.caption(f"• {call}")
        
        # Export Options
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export consultation summary
            if st.button("📄 Export Full Report", type="primary", use_container_width=True):
                summary = {
                    "session_id": st.session_state.consultation_state.session_id,
                    "date": datetime.now().isoformat(),
                    "patient_info": st.session_state.consultation_state.patient_info.model_dump(),
                    "symptoms": [s.model_dump() for s in st.session_state.consultation_state.symptoms],
                    "diagnoses": [d.model_dump() for d in st.session_state.consultation_state.diagnoses],
                    "recommendations": [r.model_dump() for r in st.session_state.consultation_state.recommendations],
                    "drug_interactions": [i.model_dump() for i in st.session_state.consultation_state.drug_interactions],
                    "api_calls": st.session_state.consultation_state.api_calls_made
                }
                
                st.download_button(
                    label="💾 Download JSON Report",
                    data=json.dumps(summary, indent=2),
                    file_name=f"medical_consultation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            # Print-friendly version
            if st.button("🖨️ Print Summary", use_container_width=True):
                # Generate print-friendly HTML
                print_html = f"""
                <html>
                <head>
                    <title>Medical Consultation Summary</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        h1, h2, h3 {{ color: #333; }}
                        .disclaimer {{ background-color: #ffe6e6; padding: 10px; border: 1px solid #ff0000; }}
                    </style>
                </head>
                <body>
                    <h1>Medical Consultation Summary</h1>
                    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                    <p>Session ID: {st.session_state.consultation_state.session_id}</p>
                    
                    <div class="disclaimer">
                        <strong>IMPORTANT:</strong> This is for informational purposes only. 
                        Please consult with healthcare professionals for medical advice.
                    </div>
                    
                    {st.session_state.consultation_state.conversation_history[-1]['content']}
                </body>
                </html>
                """
                
                st.download_button(
                    label="💾 Download Printable Report",
                    data=print_html,
                    file_name=f"consultation_summary_{datetime.now().strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
        
        with col3:
            # New consultation button
            if st.button("🔄 Start New Consultation", use_container_width=True):
                # Reset state
                st.session_state.consultation_state = None
                st.session_state.conversation = []
                st.rerun()

else:
    # Welcome screen
    st.info("👈 Please fill in your information in the sidebar and click 'Start Consultation' to begin.")
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔍 Symptom Analysis
        - AI-powered symptom recognition
        - Verification against medical databases
        - Severity assessment
        """)
    
    with col2:
        st.markdown("""
        ### 💊 Drug Safety
        - Interaction checking
        - Medication warnings
        - Safety recommendations
        """)
    
    with col3:
        st.markdown("""
        ### 🏥 Provider Matching
        - Location-based search
        - Insurance compatibility
        - Specialty matching
        """)

# Footer
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("""
    <small>
    This system uses UltraSafe medical APIs and AI to provide medical information based on reported symptoms. 
    It does not replace professional medical judgment. In case of emergency, call emergency services immediately.
    </small>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <small>
    <a href="https://ultrasafeapi.com" target="_blank">Powered by UltraSafe API</a>
    </small>
    """, unsafe_allow_html=True)