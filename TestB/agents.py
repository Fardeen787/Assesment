# agents.py
from langchain_openai import ChatOpenAI  # Updated import
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any, Optional
import json
import asyncio
from models import *
from config import LLM_MODEL, logger, GROQ_API_KEY, GROQ_BASE_URL

class EnhancedPatientInterviewAgent:
    def __init__(self, llm_model: str = LLM_MODEL):
        # Use Groq if GROQ_API_KEY is set, otherwise use OpenAI
        if GROQ_API_KEY:
            self.llm = ChatGroq(model=llm_model, temperature=0.3, groq_api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
        else:
            self.llm = ChatOpenAI(model=llm_model, temperature=0.3)
        self.system_prompt = """You are a compassionate medical interview assistant. 
        Your role is to gather comprehensive symptom information from patients.
        
        Guidelines:
        1. Ask one clear question at a time
        2. Be empathetic and professional
        3. Gather details about: symptom onset, duration, severity, location, and triggers
        4. Ask about medical history, medications, and allergies when appropriate
        5. Verify symptoms against medical databases for accuracy
        6. Never provide medical diagnoses or treatment advice
        
        Always maintain patient comfort and dignity."""
        
    async def generate_question(self, state: ConsultationState) -> str:
        """Generate the next interview question based on current state"""
        context = self._build_context(state)
        
        # Get last few messages from conversation history
        recent_messages = state.conversation_history[-4:] if state.conversation_history else []
        recent_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        # If we already have symptoms, ask follow-up questions
        if state.symptoms:
            symptom_names = [s.name for s in state.symptoms]
            
            # Check what information we already have
            has_duration = any(s.duration for s in state.symptoms)
            has_severity = any(s.severity != Severity.MODERATE for s in state.symptoms)
            
            focus_areas = []
            if not has_duration:
                focus_areas.append("Duration - How long have you had these symptoms?")
            if not has_severity:
                focus_areas.append("Severity - On a scale of 1-10, how severe is the pain/discomfort?")
            if len(state.symptoms) < 3:
                focus_areas.append("Associated symptoms - Do you have any other symptoms like fever, nausea, or fatigue?")
            focus_areas.append("Triggers - What makes the symptoms better or worse?")
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
                Patient has reported: {', '.join(symptom_names)}
                
                Recent conversation:
                {recent_text}
                
                Generate ONE specific follow-up question. Priority areas to explore:
                {chr(10).join(focus_areas)}
                
                IMPORTANT: Do NOT repeat questions. The patient has already told us they have {', '.join(symptom_names)}.
                """)
            ]
        else:
            # Initial question if no symptoms collected yet
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
                Recent conversation:
                {recent_text}
                
                The patient hasn't reported specific symptoms yet. 
                Ask a direct question to understand what symptoms they're experiencing.
                Avoid repeating previous questions.
                """)
            ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    async def process_response(self, response: str, state: ConsultationState) -> List[Symptom]:
        """Extract and verify symptoms from patient response"""
        # Skip processing if response is too short or doesn't contain symptom info
        if len(response.strip()) < 3 or response.lower().strip() in ["na", "no", "none", "yesterday", "today", "yes"]:
            return []
            
        # Extract symptoms using LLM
        messages = [
            SystemMessage(content="You are a medical symptom extractor. Extract all medical symptoms from the patient's response and format them as JSON."),
            HumanMessage(content=f"""
            Patient response: {response}
            
            Extract all symptoms mentioned. Common symptoms include: pain, ache, fever, cough, cold, nausea, vomiting, dizziness, etc.
            
            For example:
            - "pain in my stomach" -> extract "stomach pain"
            - "I have a headache" -> extract "headache"
            - "feeling dizzy" -> extract "dizziness"
            
            Return a JSON array with this exact format:
            [
                {{
                    "name": "symptom name",
                    "description": "brief description",
                    "severity": "low/moderate/high/critical",
                    "duration": "if mentioned, otherwise null",
                    "location": "body part if applicable, otherwise null",
                    "onset": "when it started if mentioned, otherwise null"
                }}
            ]
            
            Return ONLY the JSON array, no other text. If no symptoms found, return empty array [].
            """)
        ]
        
        result = self.llm.invoke(messages)
        try:
            # Clean the response to ensure it's valid JSON
            content = result.content.strip()
            # Remove any markdown formatting if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            symptoms_data = json.loads(content)
            symptoms = []
            
            for s in symptoms_data:
                # Ensure required fields have default values
                symptom_dict = {
                    "name": s.get("name", "unspecified"),
                    "description": s.get("description", ""),
                    "severity": s.get("severity", "moderate"),
                    "duration": s.get("duration"),
                    "location": s.get("location"),
                    "onset": s.get("onset")
                }
                symptoms.append(Symptom(**symptom_dict))
            
            logger.info(f"Extracted {len(symptoms)} symptoms: {[s.name for s in symptoms]}")
            return symptoms
        except Exception as e:
            logger.error(f"Error processing symptoms: {e}")
            logger.error(f"Raw response: {result.content}")
            
            # Fallback: Try to extract symptoms manually from common patterns
            symptoms = []
            response_lower = response.lower()
            
            # Pain-related symptoms
            if "pain" in response_lower or "ache" in response_lower or "hurt" in response_lower:
                if "stomach" in response_lower or "abdomen" in response_lower or "belly" in response_lower:
                    symptoms.append(Symptom(
                        name="stomach pain",
                        description="Patient reports stomach/abdominal pain",
                        severity=Severity.MODERATE,
                        location="stomach/abdomen"
                    ))
                elif "head" in response_lower:
                    symptoms.append(Symptom(
                        name="headache",
                        description="Patient reports headache",
                        severity=Severity.MODERATE,
                        location="head"
                    ))
                elif "chest" in response_lower:
                    symptoms.append(Symptom(
                        name="chest pain",
                        description="Patient reports chest pain",
                        severity=Severity.HIGH,
                        location="chest"
                    ))
                else:
                    symptoms.append(Symptom(
                        name="pain",
                        description=f"Patient reports: {response}",
                        severity=Severity.MODERATE
                    ))
            
            if "cough" in response_lower:
                symptoms.append(Symptom(
                    name="cough",
                    description="Patient reports cough",
                    severity=Severity.MODERATE
                ))
            
            if "cold" in response_lower or "runny nose" in response_lower:
                symptoms.append(Symptom(
                    name="cold symptoms",
                    description="Patient reports cold symptoms",
                    severity=Severity.MODERATE
                ))
                
            if "fever" in response_lower:
                symptoms.append(Symptom(
                    name="fever",
                    description="Patient reports fever",
                    severity=Severity.HIGH
                ))
                
            if "nausea" in response_lower or "vomit" in response_lower:
                symptoms.append(Symptom(
                    name="nausea/vomiting",
                    description="Patient reports nausea or vomiting",
                    severity=Severity.MODERATE
                ))
                
            if symptoms:
                logger.info(f"Fallback extraction found {len(symptoms)} symptoms: {[s.name for s in symptoms]}")
                
            return symptoms
    
    async def _identify_missing_information(self, state: ConsultationState) -> Optional[str]:
        """Identify what information is still needed"""
        # Check for common missing elements
        if not any(s.duration for s in state.symptoms):
            return "duration"
        if not any(s.onset for s in state.symptoms):
            return "onset"
        if not any(s.triggers for s in state.symptoms):
            return "triggers"
        return None
    
    def _generate_targeted_question(self, missing_info: str) -> str:
        """Generate specific follow-up questions"""
        questions = {
            "duration": "How long have you been experiencing these symptoms?",
            "onset": "When did these symptoms first start? Was it sudden or gradual?",
            "triggers": "Have you noticed anything that makes the symptoms better or worse?"
        }
        return questions.get(missing_info, "Can you tell me more about your symptoms?")
    
    def _build_context(self, state: ConsultationState) -> Dict[str, Any]:
        return {
            'patient_info': state.patient_info.model_dump() if state.patient_info else None,
            'symptoms': [s.model_dump() for s in state.symptoms],
            'conversation_length': len(state.conversation_history)
        }

class EnhancedMedicalKnowledgeAgent:
    def __init__(self, knowledge_base, llm_model: str = LLM_MODEL):
        self.kb = knowledge_base
        # Use Groq if GROQ_API_KEY is set, otherwise use OpenAI
        if GROQ_API_KEY:
            self.llm = ChatGroq(model=llm_model, temperature=0.1, groq_api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
        else:
            self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        
    async def retrieve_relevant_conditions(self, state: ConsultationState) -> List[MedicalCondition]:
        """Retrieve potential medical conditions using hybrid search"""
        # Get conditions from knowledge base
        conditions = await self.kb.search_conditions_hybrid(
            [s.name for s in state.symptoms],
            state.patient_info
        )
        
        # Check for drug interactions if patient has medications
        if state.patient_info and state.patient_info.current_medications:
            interactions = await self._check_medication_interactions(state)
            state.drug_interactions = interactions
            
        return conditions
    
    async def _check_medication_interactions(self, state: ConsultationState) -> List[DrugInteraction]:
        """Check for drug interactions with current medications"""
        if len(state.patient_info.current_medications) < 2:
            return []
        
        # Simulate drug interaction check
        # In real implementation, this would call UltraSafe API
        interactions = []
        
        # Example: Check for common dangerous interactions
        meds = [m.lower() for m in state.patient_info.current_medications]
        
        if "warfarin" in meds and "aspirin" in meds:
            interactions.append(DrugInteraction(
                drug1="warfarin",
                drug2="aspirin",
                severity=Severity.HIGH,
                description="Increased risk of bleeding",
                recommendations=["Monitor closely", "Consult physician about dosage adjustment"]
            ))
            
        return interactions

class EnhancedDifferentialDiagnosisAgent:
    def __init__(self, llm_model: str = LLM_MODEL):
        # Use Groq if GROQ_API_KEY is set, otherwise use OpenAI
        if GROQ_API_KEY:
            self.llm = ChatGroq(model=llm_model, temperature=0.2, groq_api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
        else:
            self.llm = ChatOpenAI(model=llm_model, temperature=0.2)
        self.system_prompt = """You are an expert diagnostic reasoning system.
        Analyze symptoms and medical conditions to create differential diagnoses.
        
        Consider:
        1. Symptom matching and pattern recognition
        2. Patient demographics and risk factors
        3. Symptom severity and duration
        4. Epidemiological factors
        5. Drug interactions and current medications
        6. Occam's razor - prefer simpler explanations
        7. Red flags that require immediate attention
        
        Always provide confidence scores and clear reasoning."""
        
    async def generate_diagnoses(self, state: ConsultationState, 
                               conditions: List[MedicalCondition]) -> List[Diagnosis]:
        """Generate differential diagnoses with enhanced analysis"""
        diagnoses = []
        
        for condition in conditions:
            diagnosis = await self._evaluate_condition(state, condition)
            if diagnosis and diagnosis.confidence >= 0.3:
                diagnoses.append(diagnosis)
                
        # Sort by confidence
        diagnoses.sort(key=lambda d: d.confidence, reverse=True)
        
        # Add differential diagnoses
        if diagnoses:
            for i, diagnosis in enumerate(diagnoses[:5]):
                diagnosis.differential_diagnoses = [
                    d.condition.name for j, d in enumerate(diagnoses[:5]) if j != i
                ]
                
        return diagnoses[:5]
    
    async def _evaluate_condition(self, state: ConsultationState, 
                                condition: MedicalCondition) -> Optional[Diagnosis]:
        """Enhanced condition evaluation with more factors"""
        patient_symptoms = [s.name for s in state.symptoms]
        
        # Consider drug interactions
        interaction_risk = "none"
        if state.drug_interactions:
            interaction_risk = "high" if any(i.severity in [Severity.HIGH, Severity.CRITICAL] 
                                           for i in state.drug_interactions) else "moderate"
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient symptoms: {json.dumps(patient_symptoms)}
            Patient info: {json.dumps(state.patient_info.model_dump() if state.patient_info else {})}
            Drug interaction risk: {interaction_risk}
            
            Condition: {condition.name}
            Condition symptoms: {json.dumps(condition.symptoms)}
            Treatment options: {json.dumps(condition.treatment_options)}
            Prevalence: {condition.prevalence}
            
            Evaluate the match and return JSON with:
            - confidence: 0.0 to 1.0
            - reasoning: detailed explanation
            - supporting_symptoms: symptoms that match
            - missing_symptoms: expected symptoms not present
            - recommended_tests: diagnostic tests to confirm
            """)
        ]
        
        result = self.llm.invoke(messages)
        try:
            data = json.loads(result.content)
            return Diagnosis(
                condition=condition,
                confidence=data['confidence'],
                reasoning=data['reasoning'],
                supporting_symptoms=data['supporting_symptoms'],
                missing_symptoms=data['missing_symptoms'],
                recommended_tests=data.get('recommended_tests', [])
            )
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return None

class EnhancedRecommendationAgent:
    def __init__(self, llm_model: str = LLM_MODEL):
        # Use Groq if GROQ_API_KEY is set, otherwise use OpenAI
        if GROQ_API_KEY:
            self.llm = ChatGroq(model=llm_model, temperature=0.1, groq_api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
        else:
            self.llm = ChatOpenAI(model=llm_model, temperature=0.1)
        self.system_prompt = """You are a medical recommendation system providing safe, 
        evidence-based guidance.
        
        CRITICAL RULES:
        1. ALWAYS recommend consulting healthcare professionals for diagnoses
        2. Identify red flags requiring immediate medical attention
        3. Provide general wellness and symptom management advice only
        4. Never prescribe medications or specific treatments
        5. Include appropriate disclaimers and warnings
        6. Consider drug interactions when making recommendations
        7. Suggest appropriate healthcare providers when possible
        
        Focus on patient safety above all else."""
        
    async def generate_recommendations(self, state: ConsultationState) -> List[Recommendation]:
        """Generate comprehensive recommendations with provider suggestions"""
        recommendations = []
        
        # Check for emergency symptoms
        emergency_rec = self._check_emergency_symptoms(state)
        if emergency_rec:
            recommendations.append(emergency_rec)
            
        # Check for drug interaction warnings
        if state.drug_interactions:
            interaction_rec = self._generate_interaction_recommendations(state)
            recommendations.extend(interaction_rec)
            
        # General recommendations based on diagnoses
        if state.diagnoses:
            general_rec = await self._generate_general_recommendations(state)
            recommendations.extend(general_rec)
            
        # Always include professional consultation
        recommendations.append(self._create_consultation_recommendation(state))
        
        return recommendations
    
    def _check_emergency_symptoms(self, state: ConsultationState) -> Optional[Recommendation]:
        """Enhanced emergency detection"""
        emergency_patterns = {
            'chest pain': ['heart attack', 'cardiac emergency'],
            'difficulty breathing': ['respiratory distress', 'asthma attack'],
            'severe bleeding': ['hemorrhage', 'trauma'],
            'loss of consciousness': ['syncope', 'stroke'],
            'severe headache': ['meningitis', 'aneurysm'],
            'stroke symptoms': ['stroke', 'TIA']
        }
        
        symptom_texts = [s.description.lower() for s in state.symptoms]
        
        for pattern, conditions in emergency_patterns.items():
            if any(pattern in text for text in symptom_texts):
                return Recommendation(
                    action="Seek immediate emergency medical care",
                    urgency=Severity.CRITICAL,
                    reasoning=f"Symptoms suggest possible {conditions[0]}",
                    next_steps=[
                        "Call emergency services (911) immediately",
                        "Do not drive yourself to the hospital",
                        "Have someone stay with you",
                        f"Inform emergency responders about: {pattern}"
                    ],
                    warnings=[f"This could be a life-threatening condition: {', '.join(conditions)}"]
                )
        
        return None
    
    def _generate_interaction_recommendations(self, state: ConsultationState) -> List[Recommendation]:
        """Generate recommendations for drug interactions"""
        recommendations = []
        
        critical_interactions = [i for i in state.drug_interactions 
                               if i.severity in [Severity.HIGH, Severity.CRITICAL]]
        
        if critical_interactions:
            rec = Recommendation(
                action="Consult with pharmacist or doctor about medication interactions",
                urgency=Severity.HIGH,
                reasoning="Potentially serious drug interactions detected",
                next_steps=[
                    "Contact your prescribing physician immediately",
                    "Do not stop medications without medical guidance",
                    "Bring all medications to your appointment"
                ],
                warnings=[f"{i.drug1} and {i.drug2}: {i.description}" 
                         for i in critical_interactions[:3]]
            )
            recommendations.append(rec)
            
        return recommendations
    
    async def _generate_general_recommendations(self, state: ConsultationState) -> List[Recommendation]:
        """Generate enhanced general care recommendations"""
        top_diagnosis = state.diagnoses[0] if state.diagnoses else None
        
        if not top_diagnosis:
            return []
            
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Top diagnosis: {top_diagnosis.condition.name} (confidence: {top_diagnosis.confidence})
            Symptoms: {json.dumps([s.model_dump() for s in state.symptoms])}
            Treatment options: {json.dumps(top_diagnosis.condition.treatment_options)}
            Recommended tests: {json.dumps(top_diagnosis.recommended_tests)}
            
            Generate 2-3 safe, general care recommendations.
            Include estimated cost ranges if applicable.
            Return as JSON array with: action, urgency, reasoning, next_steps, warnings, estimated_cost_range
            """)
        ]
        
        result = self.llm.invoke(messages)
        try:
            recs_data = json.loads(result.content)
            return [Recommendation(**r) for r in recs_data]
        except:
            return []
    
    def _create_consultation_recommendation(self, state: ConsultationState) -> Recommendation:
        """Enhanced consultation recommendation"""
        urgency = Severity.MODERATE
        
        if state.diagnoses and state.diagnoses[0].confidence > 0.8:
            urgency = Severity.HIGH
            
        next_steps = [
            "Document all symptoms to share with your doctor",
            "Bring list of current medications and medical history",
            "Prepare questions about your symptoms and concerns"
        ]
        
        # Add test recommendations if available
        if state.diagnoses and state.diagnoses[0].recommended_tests:
            next_steps.append(f"Ask about these tests: {', '.join(state.diagnoses[0].recommended_tests[:3])}")
            
        return Recommendation(
            action="Schedule appointment with healthcare provider",
            urgency=urgency,
            reasoning="Professional medical evaluation needed for accurate diagnosis and treatment",
            next_steps=next_steps,
            warnings=["This system provides information only and cannot replace professional medical advice"]
        )