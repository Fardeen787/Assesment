# orchestrator.py
from langgraph.graph import StateGraph, END
from typing import Dict, Any, List, Optional
import uuid
import asyncio
from datetime import datetime
from models import *
from agents import *
from knowledge_base import EnhancedMedicalKnowledgeBase
from ultrasafe_client import UltraSafeAPIClient
from config import logger, MAX_CONSULTATION_LENGTH

class EnhancedMedicalConsultationOrchestrator:
    def __init__(self):
        self.kb = EnhancedMedicalKnowledgeBase()
        self.interview_agent = EnhancedPatientInterviewAgent()
        self.knowledge_agent = EnhancedMedicalKnowledgeAgent(self.kb)
        self.diagnosis_agent = EnhancedDifferentialDiagnosisAgent()
        self.recommendation_agent = EnhancedRecommendationAgent()
        self.ultrasafe_client = UltraSafeAPIClient()
        
        self.workflow = self._build_workflow()
        
    def _build_workflow(self):
        """Build the enhanced LangGraph workflow"""
        # Create a new graph with ConsultationState
        workflow = StateGraph(ConsultationState)
        
        # Add nodes
        workflow.add_node("start", self._start_consultation)
        workflow.add_node("interview", self._conduct_interview)
        workflow.add_node("verify_symptoms", self._verify_symptoms)
        workflow.add_node("retrieve_knowledge", self._retrieve_knowledge)
        workflow.add_node("check_interactions", self._check_interactions)
        workflow.add_node("diagnose", self._generate_diagnoses)
        workflow.add_node("recommend", self._generate_recommendations)
        workflow.add_node("find_providers", self._find_providers)
        workflow.add_node("end", self._end_consultation)
        
        # Add edges
        workflow.add_edge("start", "interview")
        workflow.add_conditional_edges(
            "interview",
            self._should_continue_interview,
            {
                "continue": "interview",
                "proceed": "verify_symptoms"
            }
        )
        workflow.add_edge("verify_symptoms", "retrieve_knowledge")
        workflow.add_edge("retrieve_knowledge", "check_interactions")
        workflow.add_edge("check_interactions", "diagnose")
        workflow.add_edge("diagnose", "recommend")
        workflow.add_edge("recommend", "find_providers")
        workflow.add_edge("find_providers", "end")
        workflow.add_edge("end", END)
        
        # Set entry point
        workflow.set_entry_point("start")
        
        return workflow.compile()
    
    async def _start_consultation(self, state: ConsultationState) -> ConsultationState:
        """Initialize consultation with enhanced tracking"""
        state.session_id = str(uuid.uuid4())
        state.metadata['start_time'] = datetime.now().isoformat()
        state.metadata['api_version'] = "ultrasafe_v1"
        state.current_step = "interview"
        
        # Add initial disclaimer
        state.conversation_history.append({
            "role": "assistant",
            "content": """Welcome to the Enhanced Medical Information Assistant powered by UltraSafe APIs. 
            
🏥 IMPORTANT MEDICAL DISCLAIMER:
This system provides general medical information only and is NOT a substitute 
for professional medical advice, diagnosis, or treatment. Always consult with 
qualified healthcare providers for medical concerns.

⚡ EMERGENCY: If you're experiencing a medical emergency, call 911 immediately.

Let's begin by gathering some information about your symptoms. 
Please describe what you're experiencing in detail."""
        })
        
        state.api_calls_made.append("session_initialized")
        return state
    
    async def _conduct_interview(self, state: ConsultationState) -> ConsultationState:
        """Conduct enhanced patient interview"""
        # Generate next question
        question = await self.interview_agent.generate_question(state)
        state.conversation_history.append({
            "role": "assistant",
            "content": question
        })
        
        state.current_step = "interview"
        return state
    
    def _should_continue_interview(self, state: ConsultationState) -> str:
        """Determine if interview should continue"""
        # Enhanced logic considering symptom severity
        has_critical_symptoms = any(s.severity == Severity.CRITICAL for s in state.symptoms)
        
        if has_critical_symptoms and len(state.symptoms) >= 2:
            return "proceed"  # Fast-track critical cases
        elif len(state.symptoms) >= 3 or len(state.conversation_history) > MAX_CONSULTATION_LENGTH:
            return "proceed"
        return "continue"
    
    async def _verify_symptoms(self, state: ConsultationState) -> ConsultationState:
        """Verify symptoms using UltraSafe API"""
        state.current_step = "symptom_verification"
        
        # Verify each symptom
        verified_symptoms = await self.kb.verify_symptoms(state.symptoms)
        state.symptoms = verified_symptoms
        
        state.api_calls_made.append(f"verify_symptoms:{len(state.symptoms)}")
        return state
    
    async def _retrieve_knowledge(self, state: ConsultationState) -> ConsultationState:
        """Retrieve relevant medical knowledge using hybrid search"""
        state.current_step = "knowledge_retrieval"
        
        conditions = await self.knowledge_agent.retrieve_relevant_conditions(state)
        state.metadata['retrieved_conditions'] = [c.model_dump() for c in conditions]
        
        state.api_calls_made.append(f"search_conditions:{len(conditions)}")
        return state
    
    async def _check_interactions(self, state: ConsultationState) -> ConsultationState:
        """Check for drug interactions if applicable"""
        state.current_step = "interaction_check"
        
        if state.patient_info and len(state.patient_info.current_medications) >= 2:
            # Interactions are checked in retrieve_knowledge step
            state.api_calls_made.append("check_interactions")
            
        return state
    
    async def _generate_diagnoses(self, state: ConsultationState) -> ConsultationState:
        """Generate differential diagnoses with enhanced analysis"""
        state.current_step = "diagnosis"
        
        conditions = [MedicalCondition(**c) for c in state.metadata.get('retrieved_conditions', [])]
        diagnoses = await self.diagnosis_agent.generate_diagnoses(state, conditions)
        state.diagnoses = diagnoses
        
        # Get additional details for top diagnoses
        for diagnosis in state.diagnoses[:3]:
            if diagnosis.condition.ultrasafe_id:
                state.api_calls_made.append(f"condition_details:{diagnosis.condition.ultrasafe_id}")
                
        return state
    
    async def _generate_recommendations(self, state: ConsultationState) -> ConsultationState:
        """Generate comprehensive recommendations"""
        state.current_step = "recommendation"
        
        recommendations = await self.recommendation_agent.generate_recommendations(state)
        state.recommendations = recommendations
        
        return state
    
    async def _find_providers(self, state: ConsultationState) -> ConsultationState:
        """Find healthcare providers if not already included"""
        state.current_step = "provider_search"
        
        # Check if providers already found
        has_providers = any(r.providers for r in state.recommendations)
        
        if not has_providers and state.diagnoses and state.patient_info:
            # Find providers for top diagnosis
            top_condition = state.diagnoses[0].condition.name
            providers = await self.ultrasafe_client.find_healthcare_providers(
                specialty=self._determine_specialty(top_condition),
                location=state.patient_info.location,
                insurance=state.patient_info.insurance
            )
            
            if providers:
                state.metadata['suggested_providers'] = providers[:5]
                state.api_calls_made.append(f"find_providers:{len(providers)}")
                
        return state
    
    def _determine_specialty(self, condition_name: str) -> str:
        """Determine appropriate medical specialty"""
        condition_lower = condition_name.lower()
        
        specialties = {
            "heart": "cardiologist",
            "lung": "pulmonologist",
            "stomach": "gastroenterologist",
            "brain": "neurologist",
            "skin": "dermatologist",
            "joint": "rheumatologist",
            "kidney": "nephrologist",
            "liver": "hepatologist"
        }
        
        for keyword, specialty in specialties.items():
            if keyword in condition_lower:
                return specialty
                
        return "general practitioner"
    
    async def _end_consultation(self, state: ConsultationState) -> ConsultationState:
        """End consultation with comprehensive summary"""
        state.metadata['end_time'] = datetime.now().isoformat()
        state.current_step = "completed"
        
        # Generate enhanced summary
        summary = self._generate_enhanced_summary(state)
        state.conversation_history.append({
            "role": "assistant",
            "content": summary
        })
        
        # Log API usage
        logger.info(f"Consultation {state.session_id} completed. API calls: {len(state.api_calls_made)}")
        
        return state
    
    def _generate_enhanced_summary(self, state: ConsultationState) -> str:
        """Generate comprehensive consultation summary"""
        summary = "## 📋 Enhanced Consultation Summary\n\n"
        
        # Patient Information
        if state.patient_info:
            summary += "### 👤 Patient Information:\n"
            summary += f"- Age: {state.patient_info.age}, Gender: {state.patient_info.gender}\n"
            if state.patient_info.medical_history:
                summary += f"- Medical History: {', '.join(state.patient_info.medical_history)}\n"
            if state.patient_info.current_medications:
                summary += f"- Current Medications: {', '.join(state.patient_info.current_medications)}\n"
        
        # Symptoms summary
        summary += "\n### 🩺 Reported Symptoms:\n"
        for symptom in state.symptoms:
            summary += f"- **{symptom.name}** ({symptom.severity})\n"
            if symptom.description:
                summary += f"  - {symptom.description}\n"
            if symptom.duration:
                summary += f"  - Duration: {symptom.duration}\n"
        
        # Drug Interactions
        if state.drug_interactions:
            summary += "\n### ⚠️ Drug Interaction Warnings:\n"
            for interaction in state.drug_interactions:
                summary += f"- **{interaction.drug1} + {interaction.drug2}** "
                summary += f"(Severity: {interaction.severity})\n"
                summary += f"  - {interaction.description}\n"
        
        # Top diagnoses
        if state.diagnoses:
            summary += "\n### 🔍 Possible Conditions (for discussion with your doctor):\n"
            for i, diagnosis in enumerate(state.diagnoses[:3]):
                summary += f"\n**{i+1}. {diagnosis.condition.name}** "
                summary += f"(Confidence: {diagnosis.confidence:.0%})\n"
                summary += f"- *Reasoning:* {diagnosis.reasoning}\n"
                if diagnosis.recommended_tests:
                    summary += f"- *Recommended Tests:* {', '.join(diagnosis.recommended_tests[:3])}\n"
                if diagnosis.differential_diagnoses:
                    summary += f"- *Also Consider:* {', '.join(diagnosis.differential_diagnoses[:2])}\n"
        
        # Recommendations
        summary += "\n### 💡 Recommendations:\n"
        for i, rec in enumerate(state.recommendations):
            urgency_emoji = {
                Severity.LOW: "🟢",
                Severity.MODERATE: "🟡",
                Severity.HIGH: "🟠",
                Severity.CRITICAL: "🔴"
            }
            
            summary += f"\n{urgency_emoji.get(rec.urgency, '⚪')} **{rec.action}**\n"
            summary += f"*{rec.reasoning}*\n"
            
            if rec.next_steps:
                summary += "**Next Steps:**\n"
                for step in rec.next_steps:
                    summary += f"- {step}\n"
                    
            if rec.providers:
                summary += "**Suggested Providers:**\n"
                for provider in rec.providers[:2]:
                    summary += f"- {provider.name} ({provider.specialty})"
                    if provider.phone:
                        summary += f" - 📞 {provider.phone}"
                    summary += "\n"
        
        # API Usage Summary
        summary += f"\n### 📊 Consultation Metrics:\n"
        summary += f"- UltraSafe API calls made: {len(state.api_calls_made)}\n"
        summary += f"- Conditions evaluated: {len(state.metadata.get('retrieved_conditions', []))}\n"
        summary += f"- Session ID: {state.session_id}\n"
        
        # Final Disclaimer
        summary += """\n### ⚠️ Important Reminder:
This information is powered by UltraSafe medical APIs for educational purposes only. 
Please consult with healthcare professionals for proper medical evaluation and treatment.

**In case of emergency, call 911 immediately.**"""
        
        return summary
    
    async def run_consultation(self, initial_input: Dict[str, Any]) -> ConsultationState:
        """Run a complete consultation asynchronously"""
        initial_state = ConsultationState(**initial_input)
        
        # For synchronous execution in Streamlit
        final_state = await self._run_workflow_async(initial_state)
        
        return final_state
    
    async def _run_workflow_async(self, state: ConsultationState) -> ConsultationState:
        """Execute workflow steps manually since we can't use the compiled workflow directly"""
        # This is a simplified version that executes the workflow steps in sequence
        state = await self._start_consultation(state)
        
        # Interview loop
        while self._should_continue_interview(state) == "continue" and len(state.conversation_history) < MAX_CONSULTATION_LENGTH:
            state = await self._conduct_interview(state)
            # In a real implementation, we would wait for user input here
            # For now, we'll break after one iteration
            break
        
        # Continue with the rest of the workflow
        if len(state.symptoms) > 0:
            state = await self._verify_symptoms(state)
            state = await self._retrieve_knowledge(state)
            state = await self._check_interactions(state)
            state = await self._generate_diagnoses(state)
            state = await self._generate_recommendations(state)
            state = await self._find_providers(state)
            state = await self._end_consultation(state)
        
        return state