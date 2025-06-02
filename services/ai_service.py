"""
MedScript Pro - AI Service for Drug Interaction Analysis
This file handles OpenRouter API integration for intelligent drug interaction checking.
"""

import json
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import streamlit as st
from config.settings import OPENROUTER_CONFIG, AI_ANALYSIS_CONFIG, FEATURE_FLAGS

class AIAnalysisService:
    """Service for AI-powered drug interaction analysis"""
    
    def __init__(self):
        self.base_url = OPENROUTER_CONFIG['BASE_URL']
        self.model = OPENROUTER_CONFIG['MODEL']
        self.max_tokens = OPENROUTER_CONFIG['MAX_TOKENS']
        self.temperature = OPENROUTER_CONFIG['TEMPERATURE']
        self.timeout = OPENROUTER_CONFIG['TIMEOUT']
        self.rate_limit_delay = OPENROUTER_CONFIG['RATE_LIMIT_DELAY']
        
        self.max_retries = AI_ANALYSIS_CONFIG['MAX_RETRIES']
        self.retry_delay = AI_ANALYSIS_CONFIG['RETRY_DELAY']
        self.fallback_enabled = AI_ANALYSIS_CONFIG['FALLBACK_ENABLED']
        
        # Get API key from secrets or environment
        self.api_key = self._get_api_key()
        
        # Track API usage
        self.last_request_time = 0
        
    def _get_api_key(self) -> Optional[str]:
        """Get OpenRouter API key from Streamlit secrets or environment"""
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'OPENROUTER_API_KEY' in st.secrets:
                return st.secrets['OPENROUTER_API_KEY']
            
            # Try environment variable
            import os
            return os.getenv('OPENROUTER_API_KEY')
        
        except Exception:
            return None
    
    def _rate_limit_check(self):
        """Implement rate limiting to respect API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _build_analysis_prompt(self, medications: List[Dict[str, Any]], 
                             patient_context: Dict[str, Any]) -> str:
        """
        Build comprehensive prompt for drug interaction analysis
        
        Args:
            medications (List[Dict[str, Any]]): List of medications
            patient_context (Dict[str, Any]): Patient information
        
        Returns:
            str: Formatted prompt for AI analysis
        """
        # Build medication list
        med_list = []
        for med in medications:
            med_info = f"- {med.get('name', 'Unknown')} ({med.get('generic_name', 'N/A')})"
            if med.get('dosage'):
                med_info += f" - {med.get('dosage')}"
            if med.get('frequency'):
                med_info += f" {med.get('frequency')}"
            med_list.append(med_info)
        
        medications_text = "\n".join(med_list)
        
        # Build patient context
        age = patient_context.get('age', 'Unknown')
        gender = patient_context.get('gender', 'Unknown')
        allergies = patient_context.get('allergies', 'None known')
        conditions = patient_context.get('medical_conditions', 'None reported')
        
        prompt = f"""
You are a clinical pharmacist AI assistant. Analyze the following prescription for potential drug interactions, contraindications, and safety concerns.

PATIENT INFORMATION:
- Age: {age}
- Gender: {gender}
- Known Allergies: {allergies}
- Medical Conditions: {conditions}

PRESCRIBED MEDICATIONS:
{medications_text}

Please provide a comprehensive analysis in the following JSON format:

{{
    "interactions": [
        {{
            "drugs": ["Drug A", "Drug B"],
            "severity": "major|moderate|minor",
            "description": "Description of the interaction",
            "recommendation": "Clinical recommendation"
        }}
    ],
    "allergies": [
        {{
            "drug": "Drug name",
            "allergy": "Known allergy",
            "risk": "Risk assessment"
        }}
    ],
    "contraindications": [
        {{
            "drug": "Drug name",
            "condition": "Medical condition",
            "risk": "Risk level and explanation"
        }}
    ],
    "alternatives": [
        {{
            "instead_of": "Current drug",
            "suggested": "Alternative drug",
            "reason": "Reason for alternative"
        }}
    ],
    "monitoring": [
        {{
            "parameter": "What to monitor",
            "frequency": "How often",
            "reason": "Why monitoring is needed"
        }}
    ],
    "overall_risk": "low|moderate|high",
    "summary": "Brief overall assessment"
}}

Focus on clinically significant interactions and provide actionable recommendations. If no significant issues are found, indicate that in your response.
"""
        return prompt
    
    def _make_api_request(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Make request to OpenRouter API
        
        Args:
            prompt (str): Analysis prompt
        
        Returns:
            Optional[Dict[str, Any]]: API response or None if failed
        """
        if not self.api_key:
            raise Exception("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://medscript-pro.app",
            "X-Title": "MedScript Pro"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a clinical pharmacist AI assistant specializing in drug interaction analysis. Always respond with valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            # Rate limiting
            self._rate_limit_check()
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Extract content from response
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                # Try to parse JSON from content
                try:
                    # Clean up content - remove markdown formatting if present
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()
                    
                    return json.loads(content)
                
                except json.JSONDecodeError:
                    # If JSON parsing fails, return raw content
                    return {"raw_content": content, "parsing_error": True}
            
            return None
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
    
    def analyze_drug_interactions(self, medications: List[Dict[str, Any]], 
                                patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze drug interactions using AI
        
        Args:
            medications (List[Dict[str, Any]]): List of medications
            patient_context (Dict[str, Any]): Patient context information
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not FEATURE_FLAGS['ENABLE_AI_ANALYSIS']:
            return self._get_fallback_analysis(medications, patient_context)
        
        if not medications:
            return {
                "status": "success",
                "analysis": {
                    "interactions": [],
                    "allergies": [],
                    "contraindications": [],
                    "alternatives": [],
                    "monitoring": [],
                    "overall_risk": "low",
                    "summary": "No medications to analyze."
                },
                "source": "system",
                "timestamp": datetime.now().isoformat()
            }
        
        # Try AI analysis with retries
        for attempt in range(self.max_retries):
            try:
                st.info(f"🤖 Analyzing drug interactions... (Attempt {attempt + 1})")
                
                prompt = self._build_analysis_prompt(medications, patient_context)
                ai_result = self._make_api_request(prompt)
                
                if ai_result:
                    # Validate and process AI result
                    processed_result = self._process_ai_result(ai_result)
                    
                    if processed_result:
                        st.success("✅ AI analysis completed successfully!")
                        return {
                            "status": "success",
                            "analysis": processed_result,
                            "source": "ai",
                            "timestamp": datetime.now().isoformat()
                        }
                
                # If we get here, the attempt failed
                if attempt < self.max_retries - 1:
                    st.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                error_msg = str(e)
                st.warning(f"AI analysis attempt {attempt + 1} failed: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    # Last attempt failed
                    if self.fallback_enabled:
                        st.info("🔄 AI analysis unavailable, using fallback analysis...")
                        return self._get_fallback_analysis(medications, patient_context)
                    else:
                        return {
                            "status": "error",
                            "error": error_msg,
                            "analysis": None,
                            "source": "error",
                            "timestamp": datetime.now().isoformat()
                        }
        
        # If all retries failed
        if self.fallback_enabled:
            st.info("🔄 AI analysis unavailable, using fallback analysis...")
            return self._get_fallback_analysis(medications, patient_context)
        else:
            return {
                "status": "error",
                "error": "AI analysis failed after all retries",
                "analysis": None,
                "source": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_ai_result(self, ai_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and validate AI result
        
        Args:
            ai_result (Dict[str, Any]): Raw AI result
        
        Returns:
            Optional[Dict[str, Any]]: Processed result or None if invalid
        """
        try:
            # If there was a parsing error, try to extract useful info
            if ai_result.get('parsing_error'):
                return self._extract_fallback_from_text(ai_result.get('raw_content', ''))
            
            # Validate required fields
            required_fields = ['interactions', 'allergies', 'contraindications', 
                             'alternatives', 'monitoring', 'overall_risk', 'summary']
            
            for field in required_fields:
                if field not in ai_result:
                    ai_result[field] = [] if field != 'overall_risk' and field != 'summary' else ''
            
            # Validate data types
            if not isinstance(ai_result['interactions'], list):
                ai_result['interactions'] = []
            
            if not isinstance(ai_result['allergies'], list):
                ai_result['allergies'] = []
            
            if not isinstance(ai_result['contraindications'], list):
                ai_result['contraindications'] = []
            
            if not isinstance(ai_result['alternatives'], list):
                ai_result['alternatives'] = []
            
            if not isinstance(ai_result['monitoring'], list):
                ai_result['monitoring'] = []
            
            # Ensure overall_risk is valid
            valid_risks = ['low', 'moderate', 'high']
            if ai_result.get('overall_risk') not in valid_risks:
                ai_result['overall_risk'] = 'moderate'
            
            # Ensure summary exists
            if not ai_result.get('summary'):
                ai_result['summary'] = 'Analysis completed. Review individual sections for details.'
            
            return ai_result
        
        except Exception:
            return None
    
    def _extract_fallback_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract analysis info from unstructured text response
        
        Args:
            text (str): Raw text response
        
        Returns:
            Dict[str, Any]: Extracted analysis
        """
        # Simple text analysis fallback
        interactions = []
        monitoring = []
        overall_risk = "moderate"
        
        text_lower = text.lower()
        
        # Look for interaction keywords
        if any(word in text_lower for word in ['interaction', 'interact', 'contraindicated']):
            interactions.append({
                "drugs": ["Multiple medications"],
                "severity": "moderate",
                "description": "Potential interactions detected in AI analysis",
                "recommendation": "Review full AI response for details"
            })
        
        # Look for monitoring keywords
        if any(word in text_lower for word in ['monitor', 'check', 'follow', 'watch']):
            monitoring.append({
                "parameter": "General monitoring",
                "frequency": "As clinically indicated",
                "reason": "Based on AI analysis recommendations"
            })
        
        # Determine risk level
        if any(word in text_lower for word in ['high risk', 'dangerous', 'severe', 'major']):
            overall_risk = "high"
        elif any(word in text_lower for word in ['low risk', 'safe', 'minor']):
            overall_risk = "low"
        
        return {
            "interactions": interactions,
            "allergies": [],
            "contraindications": [],
            "alternatives": [],
            "monitoring": monitoring,
            "overall_risk": overall_risk,
            "summary": f"AI analysis completed. Review original response: {text[:200]}..."
        }
    
    def _get_fallback_analysis(self, medications: List[Dict[str, Any]], 
                             patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide fallback analysis when AI is unavailable
        
        Args:
            medications (List[Dict[str, Any]]): List of medications
            patient_context (Dict[str, Any]): Patient context
        
        Returns:
            Dict[str, Any]: Fallback analysis results
        """
        interactions = []
        allergies = []
        contraindications = []
        monitoring = []
        
        # Basic interaction checking
        interactions.extend(self._check_basic_interactions(medications))
        
        # Check against patient allergies
        allergies.extend(self._check_patient_allergies(medications, patient_context))
        
        # Check contraindications
        contraindications.extend(self._check_basic_contraindications(medications, patient_context))
        
        # Basic monitoring recommendations
        monitoring.extend(self._get_basic_monitoring(medications))
        
        # Determine overall risk
        overall_risk = "low"
        if interactions or contraindications:
            overall_risk = "moderate"
        if any(interaction.get('severity') == 'major' for interaction in interactions):
            overall_risk = "high"
        
        summary = f"Basic analysis completed for {len(medications)} medication(s). "
        if interactions:
            summary += f"Found {len(interactions)} potential interaction(s). "
        if allergies:
            summary += f"Found {len(allergies)} allergy concern(s). "
        summary += "AI analysis was unavailable - this is a basic safety check only."
        
        return {
            "status": "success",
            "analysis": {
                "interactions": interactions,
                "allergies": allergies,
                "contraindications": contraindications,
                "alternatives": [],
                "monitoring": monitoring,
                "overall_risk": overall_risk,
                "summary": summary
            },
            "source": "fallback",
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_basic_interactions(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for basic known drug interactions"""
        interactions = []
        
        # Common interaction patterns
        interaction_patterns = [
            {
                "drugs": ["warfarin", "aspirin"],
                "severity": "major",
                "description": "Increased bleeding risk",
                "recommendation": "Monitor INR closely, consider alternative"
            },
            {
                "drugs": ["metformin", "contrast"],
                "severity": "major",
                "description": "Risk of lactic acidosis",
                "recommendation": "Hold metformin before and after contrast procedures"
            },
            {
                "drugs": ["ace inhibitor", "potassium"],
                "severity": "moderate",
                "description": "Risk of hyperkalemia",
                "recommendation": "Monitor serum potassium levels"
            },
            {
                "drugs": ["nsaid", "ace inhibitor"],
                "severity": "moderate",
                "description": "Reduced antihypertensive effect, kidney function risk",
                "recommendation": "Monitor blood pressure and kidney function"
            }
        ]
        
        med_names = [med.get('name', '').lower() for med in medications]
        med_generics = [med.get('generic_name', '').lower() for med in medications]
        all_med_names = med_names + med_generics
        
        for pattern in interaction_patterns:
            pattern_drugs = [drug.lower() for drug in pattern["drugs"]]
            if any(any(pattern_drug in med_name for med_name in all_med_names) 
                   for pattern_drug in pattern_drugs):
                if len([drug for drug in pattern_drugs 
                       if any(drug in med_name for med_name in all_med_names)]) >= 2:
                    interactions.append(pattern)
        
        return interactions
    
    def _check_patient_allergies(self, medications: List[Dict[str, Any]], 
                               patient_context: Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check medications against patient allergies"""
        allergies = []
        
        patient_allergies = patient_context.get('allergies', '').lower()
        if not patient_allergies or patient_allergies in ['none', 'none known', 'nka']:
            return allergies
        
        allergy_list = [allergy.strip() for allergy in patient_allergies.split(',')]
        
        for med in medications:
            med_name = med.get('name', '').lower()
            med_generic = med.get('generic_name', '').lower()
            
            for allergy in allergy_list:
                if allergy in med_name or allergy in med_generic:
                    allergies.append({
                        "drug": med.get('name', 'Unknown'),
                        "allergy": allergy.title(),
                        "risk": "Patient has documented allergy to this medication"
                    })
        
        return allergies
    
    def _check_basic_contraindications(self, medications: List[Dict[str, Any]], 
                                     patient_context: Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for basic contraindications"""
        contraindications = []
        
        conditions = patient_context.get('medical_conditions', '').lower()
        if not conditions:
            return contraindications
        
        # Basic contraindication patterns
        contraindication_patterns = [
            {
                "drug_pattern": "nsaid",
                "condition_pattern": "kidney disease",
                "risk": "NSAIDs can worsen kidney function"
            },
            {
                "drug_pattern": "metformin",
                "condition_pattern": "kidney disease",
                "risk": "Risk of lactic acidosis with reduced kidney function"
            },
            {
                "drug_pattern": "beta blocker",
                "condition_pattern": "asthma",
                "risk": "Beta blockers can trigger bronchospasm in asthma patients"
            }
        ]
        
        for med in medications:
            med_name = med.get('name', '').lower()
            med_generic = med.get('generic_name', '').lower()
            
            for pattern in contraindication_patterns:
                if (pattern["drug_pattern"] in med_name or 
                    pattern["drug_pattern"] in med_generic):
                    if pattern["condition_pattern"] in conditions:
                        contraindications.append({
                            "drug": med.get('name', 'Unknown'),
                            "condition": pattern["condition_pattern"].title(),
                            "risk": pattern["risk"]
                        })
        
        return contraindications
    
    def _get_basic_monitoring(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get basic monitoring recommendations"""
        monitoring = []
        
        # Basic monitoring patterns
        monitoring_patterns = [
            {
                "drug_pattern": "warfarin",
                "parameter": "INR",
                "frequency": "Weekly initially, then monthly when stable",
                "reason": "Monitor anticoagulation effect"
            },
            {
                "drug_pattern": "ace inhibitor",
                "parameter": "Kidney function and potassium",
                "frequency": "2-4 weeks after initiation, then every 6 months",
                "reason": "Monitor for kidney effects and hyperkalemia"
            },
            {
                "drug_pattern": "statin",
                "parameter": "Liver function",
                "frequency": "6-12 weeks after initiation, then annually",
                "reason": "Monitor for liver toxicity"
            },
            {
                "drug_pattern": "metformin",
                "parameter": "Kidney function and vitamin B12",
                "frequency": "Every 6-12 months",
                "reason": "Monitor for kidney effects and B12 deficiency"
            }
        ]
        
        for med in medications:
            med_name = med.get('name', '').lower()
            med_generic = med.get('generic_name', '').lower()
            
            for pattern in monitoring_patterns:
                if (pattern["drug_pattern"] in med_name or 
                    pattern["drug_pattern"] in med_generic):
                    monitoring.append({
                        "parameter": pattern["parameter"],
                        "frequency": pattern["frequency"],
                        "reason": pattern["reason"]
                    })
        
        return monitoring

# Convenience functions for easy access
def analyze_prescription_safety(medications: List[Dict[str, Any]], 
                              patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze prescription safety using AI service
    
    Args:
        medications (List[Dict[str, Any]]): List of prescribed medications
        patient_data (Dict[str, Any]): Patient information
    
    Returns:
        Dict[str, Any]: Safety analysis results
    """
    ai_service = AIAnalysisService()
    
    # Prepare patient context
    patient_context = {
        'age': patient_data.get('age', 'Unknown'),
        'gender': patient_data.get('gender', 'Unknown'),
        'allergies': patient_data.get('allergies', 'None known'),
        'medical_conditions': patient_data.get('medical_conditions', 'None reported')
    }
    
    return ai_service.analyze_drug_interactions(medications, patient_context)

def is_ai_available() -> bool:
    """
    Check if AI analysis is available
    
    Returns:
        bool: True if AI service is configured and available
    """
    if not FEATURE_FLAGS['ENABLE_AI_ANALYSIS']:
        return False
    
    ai_service = AIAnalysisService()
    return ai_service.api_key is not None

def get_ai_service_status() -> Dict[str, Any]:
    """
    Get AI service status information
    
    Returns:
        Dict[str, Any]: Service status information
    """
    ai_service = AIAnalysisService()
    
    return {
        'enabled': FEATURE_FLAGS['ENABLE_AI_ANALYSIS'],
        'api_configured': ai_service.api_key is not None,
        'fallback_enabled': ai_service.fallback_enabled,
        'model': ai_service.model,
        'max_retries': ai_service.max_retries
    }