"""
MedScript Pro - UI Card Components
This file contains reusable card components for displaying data throughout the application.
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional, Callable
import streamlit as st
from utils.formatters import (
    format_patient_name, format_user_name, format_date_display,
    format_phone_number, format_medication_dosage, format_age_from_birth_date,
    format_medical_conditions, format_allergies, format_relative_date,
    format_currency, format_percentage
)
from utils.helpers import calculate_age, get_time_ago

class BaseCard:
    """Base class for all card components"""
    
    def __init__(self, title: str = "", subtitle: str = "", 
                 card_style: str = "default", show_border: bool = True):
        self.title = title
        self.subtitle = subtitle
        self.card_style = card_style
        self.show_border = show_border
    
    def render_header(self):
        """Render card header"""
        if self.title:
            if self.subtitle:
                st.markdown(f"**{self.title}**")
                st.caption(self.subtitle)
            else:
                st.subheader(self.title)
    
    def render(self):
        """Render the card"""
        raise NotImplementedError("Subclasses must implement render method")

class MetricCard(BaseCard):
    """Card for displaying metrics and KPIs"""
    
    def __init__(self, title: str, value: str, delta: str = None, 
                 delta_color: str = "normal", icon: str = None, **kwargs):
        super().__init__(title, **kwargs)
        self.value = value
        self.delta = delta
        self.delta_color = delta_color
        self.icon = icon
    
    def render(self):
        """Render metric card"""
        # Use Streamlit's metric component
        st.metric(
            label=f"{self.icon} {self.title}" if self.icon else self.title,
            value=self.value,
            delta=self.delta,
            delta_color=self.delta_color
        )

class PatientCard(BaseCard):
    """Card for displaying patient information"""
    
    def __init__(self, patient_data: Dict[str, Any], 
                 show_actions: bool = True, 
                 action_callbacks: Dict[str, Callable] = None,
                 consultation_status: str = None, **kwargs):
        patient_name = format_patient_name(
            patient_data.get('first_name', ''), 
            patient_data.get('last_name', '')
        )
        super().__init__(patient_name, **kwargs)
        self.patient_data = patient_data
        self.show_actions = show_actions
        self.action_callbacks = action_callbacks or {}
        self.consultation_status = consultation_status
    
    def render(self):
        """Render patient card"""
        # Determine card style based on consultation status
        card_class = ""
        if self.consultation_status == "completed":
            card_class = "patient-completed"
        elif self.consultation_status == "waiting":
            card_class = "patient-waiting"
        elif self.consultation_status == "emergency":
            card_class = "patient-card emergency"
        
        # Card container with custom CSS class
        with st.container():
            if card_class:
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            # Patient header
            col_info, col_status = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**{self.title}**")
                
                # Basic info
                age = calculate_age(self.patient_data.get('date_of_birth', ''))
                gender = self.patient_data.get('gender', 'Unknown')
                patient_id = self.patient_data.get('patient_id', 'Unknown')
                
                st.caption(f"ID: {patient_id} | {age} years, {gender}")
                
                # Contact info
                if self.patient_data.get('phone'):
                    phone = format_phone_number(self.patient_data['phone'])
                    st.caption(f"📞 {phone}")
            
            with col_status:
                if self.consultation_status:
                    if self.consultation_status == "completed":
                        st.success("✅ Completed")
                    elif self.consultation_status == "waiting":
                        st.warning("⏳ Waiting")
                    elif self.consultation_status == "emergency":
                        st.error("🚨 Emergency")
            
            # Medical information
            allergies = self.patient_data.get('allergies', '')
            if allergies and allergies.lower() not in ['none', 'none known', 'nka']:
                st.markdown(f"**⚠️ Allergies:** {format_allergies(allergies)}")
            
            conditions = self.patient_data.get('medical_conditions', '')
            if conditions and conditions.lower() != 'none':
                st.markdown(f"**🏥 Conditions:** {format_medical_conditions(conditions)}")
            
            # Visit information (if available)
            if hasattr(self, 'visit_info') and self.visit_info:
                visit_info = self.visit_info
                st.markdown(f"**📅 Visit:** {visit_info.get('visit_type', 'N/A')}")
                
                if visit_info.get('current_problems'):
                    st.markdown(f"**Problems:** {visit_info['current_problems'][:100]}...")
                
                # Vital signs
                vital_signs = []
                if visit_info.get('blood_pressure'):
                    vital_signs.append(f"BP: {visit_info['blood_pressure']}")
                if visit_info.get('temperature'):
                    vital_signs.append(f"Temp: {visit_info['temperature']}°F")
                if visit_info.get('pulse_rate'):
                    vital_signs.append(f"HR: {visit_info['pulse_rate']}")
                
                if vital_signs:
                    st.caption(f"Vitals: {' | '.join(vital_signs)}")
            
            # Action buttons
            if self.show_actions:
                action_cols = st.columns(len(self.action_callbacks) if self.action_callbacks else 3)
                
                for i, (action_name, callback) in enumerate(self.action_callbacks.items()):
                    with action_cols[i]:
                        if st.button(action_name, key=f"{action_name}_{self.patient_data.get('id', 'unknown')}", 
                                   use_container_width=True):
                            if callback:
                                callback(self.patient_data)
            
            if card_class:
                st.markdown('</div>', unsafe_allow_html=True)

class PrescriptionCard(BaseCard):
    """Card for displaying prescription information"""
    
    def __init__(self, prescription_data: Dict[str, Any], 
                 show_actions: bool = True,
                 action_callbacks: Dict[str, Callable] = None, **kwargs):
        prescription_id = prescription_data.get('prescription_id', 'Unknown')
        super().__init__(f"Prescription {prescription_id}", **kwargs)
        self.prescription_data = prescription_data
        self.show_actions = show_actions
        self.action_callbacks = action_callbacks or {}
    
    def render(self):
        """Render prescription card"""
        with st.container():
            # Prescription header
            col_info, col_status = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**{self.title}**")
                
                # Patient info
                patient_name = format_patient_name(
                    self.prescription_data.get('first_name', ''),
                    self.prescription_data.get('last_name', '')
                )
                st.caption(f"Patient: {patient_name}")
                
                # Doctor info
                doctor_name = self.prescription_data.get('doctor_name', 'Unknown')
                st.caption(f"Doctor: {doctor_name}")
                
                # Date
                created_date = self.prescription_data.get('created_at', '')
                if created_date:
                    relative_date = get_time_ago(created_date)
                    st.caption(f"Created: {relative_date}")
            
            with col_status:
                status = self.prescription_data.get('status', 'Unknown')
                if status == 'Active':
                    st.success("🟢 Active")
                elif status == 'Completed':
                    st.info("✅ Completed")
                elif status == 'Cancelled':
                    st.error("❌ Cancelled")
            
            # Diagnosis
            diagnosis = self.prescription_data.get('diagnosis', '')
            if diagnosis:
                st.markdown(f"**Diagnosis:** {diagnosis}")
            
            # Medication count
            medication_count = self.prescription_data.get('total_medications', 0)
            lab_test_count = self.prescription_data.get('total_lab_tests', 0)
            
            if medication_count > 0 or lab_test_count > 0:
                items = []
                if medication_count > 0:
                    items.append(f"{medication_count} medication{'s' if medication_count != 1 else ''}")
                if lab_test_count > 0:
                    items.append(f"{lab_test_count} lab test{'s' if lab_test_count != 1 else ''}")
                st.caption(f"Contains: {', '.join(items)}")
            
            # Action buttons
            if self.show_actions and self.action_callbacks:
                action_cols = st.columns(len(self.action_callbacks))
                
                for i, (action_name, callback) in enumerate(self.action_callbacks.items()):
                    with action_cols[i]:
                        if st.button(action_name, 
                                   key=f"{action_name}_{self.prescription_data.get('id', 'unknown')}", 
                                   use_container_width=True):
                            if callback:
                                callback(self.prescription_data)

class MedicationCard(BaseCard):
    """Card for displaying medication information"""
    
    def __init__(self, medication_data: Dict[str, Any], 
                 show_details: bool = True,
                 show_actions: bool = True,
                 action_callbacks: Dict[str, Callable] = None, **kwargs):
        medication_name = medication_data.get('name', 'Unknown Medication')
        super().__init__(medication_name, **kwargs)
        self.medication_data = medication_data
        self.show_details = show_details
        self.show_actions = show_actions
        self.action_callbacks = action_callbacks or {}
    
    def render(self):
        """Render medication card"""
        with st.container():
            # Medication header
            col_info, col_favorite = st.columns([4, 1])
            
            with col_info:
                st.markdown(f"**{self.title}**")
                
                # Generic name
                generic_name = self.medication_data.get('generic_name', '')
                if generic_name and generic_name.lower() != self.title.lower():
                    st.caption(f"Generic: {generic_name}")
                
                # Drug class
                drug_class = self.medication_data.get('drug_class', '')
                if drug_class:
                    st.caption(f"Class: {drug_class}")
            
            with col_favorite:
                if self.medication_data.get('is_favorite'):
                    st.markdown("⭐")
                
                if self.medication_data.get('is_controlled'):
                    st.markdown("🔒")
            
            if self.show_details:
                # Dosage forms and strengths
                dosage_forms = self.medication_data.get('dosage_forms', '')
                strengths = self.medication_data.get('strengths', '')
                
                if dosage_forms:
                    st.markdown(f"**Forms:** {dosage_forms}")
                
                if strengths:
                    st.markdown(f"**Strengths:** {strengths}")
                
                # Indications (truncated)
                indications = self.medication_data.get('indications', '')
                if indications:
                    truncated_indications = indications[:100] + "..." if len(indications) > 100 else indications
                    st.markdown(f"**Indications:** {truncated_indications}")
                
                # Brand names
                brand_names = self.medication_data.get('brand_names', '')
                if brand_names:
                    st.caption(f"Brands: {brand_names}")
            
            # Action buttons
            if self.show_actions and self.action_callbacks:
                action_cols = st.columns(len(self.action_callbacks))
                
                for i, (action_name, callback) in enumerate(self.action_callbacks.items()):
                    with action_cols[i]:
                        if st.button(action_name, 
                                   key=f"{action_name}_{self.medication_data.get('id', 'unknown')}", 
                                   use_container_width=True):
                            if callback:
                                callback(self.medication_data)

class LabTestCard(BaseCard):
    """Card for displaying lab test information"""
    
    def __init__(self, lab_test_data: Dict[str, Any], 
                 show_details: bool = True,
                 show_actions: bool = True,
                 action_callbacks: Dict[str, Callable] = None, **kwargs):
        test_name = lab_test_data.get('test_name', 'Unknown Test')
        super().__init__(test_name, **kwargs)
        self.lab_test_data = lab_test_data
        self.show_details = show_details
        self.show_actions = show_actions
        self.action_callbacks = action_callbacks or {}
    
    def render(self):
        """Render lab test card"""
        with st.container():
            # Test header
            st.markdown(f"**{self.title}**")
            
            # Category
            category = self.lab_test_data.get('test_category', '')
            if category:
                st.caption(f"Category: {category}")
            
            # Test code
            test_code = self.lab_test_data.get('test_code', '')
            if test_code:
                st.caption(f"Code: {test_code}")
            
            if self.show_details:
                # Normal range
                normal_range = self.lab_test_data.get('normal_range', '')
                units = self.lab_test_data.get('units', '')
                
                if normal_range:
                    range_text = f"{normal_range}"
                    if units:
                        range_text += f" {units}"
                    st.markdown(f"**Normal Range:** {range_text}")
                
                # Description (truncated)
                description = self.lab_test_data.get('description', '')
                if description:
                    truncated_desc = description[:100] + "..." if len(description) > 100 else description
                    st.markdown(f"**Description:** {truncated_desc}")
                
                # Preparation requirements
                preparation = self.lab_test_data.get('preparation_required', '')
                if preparation:
                    st.caption(f"Preparation: {preparation}")
                
                # Sample type
                sample_type = self.lab_test_data.get('sample_type', '')
                if sample_type:
                    st.caption(f"Sample: {sample_type}")
            
            # Action buttons
            if self.show_actions and self.action_callbacks:
                action_cols = st.columns(len(self.action_callbacks))
                
                for i, (action_name, callback) in enumerate(self.action_callbacks.items()):
                    with action_cols[i]:
                        if st.button(action_name, 
                                   key=f"{action_name}_{self.lab_test_data.get('id', 'unknown')}", 
                                   use_container_width=True):
                            if callback:
                                callback(self.lab_test_data)

class TemplateCard(BaseCard):
    """Card for displaying prescription template information"""
    
    def __init__(self, template_data: Dict[str, Any], 
                 show_actions: bool = True,
                 action_callbacks: Dict[str, Callable] = None, **kwargs):
        template_name = template_data.get('name', 'Unknown Template')
        super().__init__(template_name, **kwargs)
        self.template_data = template_data
        self.show_actions = show_actions
        self.action_callbacks = action_callbacks or {}
    
    def render(self):
        """Render template card"""
        with st.container():
            # Template header
            col_info, col_usage = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**{self.title}**")
                
                # Category
                category = self.template_data.get('category', '')
                if category:
                    st.caption(f"Category: {category}")
                
                # Description
                description = self.template_data.get('description', '')
                if description:
                    truncated_desc = description[:80] + "..." if len(description) > 80 else description
                    st.caption(description)
            
            with col_usage:
                usage_count = self.template_data.get('usage_count', 0)
                st.metric("Uses", usage_count)
            
            # Template contents
            medications = self.template_data.get('medications', [])
            lab_tests = self.template_data.get('lab_tests', [])
            
            if medications or lab_tests:
                contents = []
                if medications:
                    contents.append(f"{len(medications)} medication{'s' if len(medications) != 1 else ''}")
                if lab_tests:
                    contents.append(f"{len(lab_tests)} lab test{'s' if len(lab_tests) != 1 else ''}")
                
                st.markdown(f"**Contains:** {', '.join(contents)}")
            
            # Diagnosis template
            diagnosis = self.template_data.get('diagnosis_template', '')
            if diagnosis:
                truncated_diagnosis = diagnosis[:60] + "..." if len(diagnosis) > 60 else diagnosis
                st.markdown(f"**Diagnosis:** {truncated_diagnosis}")
            
            # Last updated
            updated_at = self.template_data.get('updated_at', '')
            if updated_at:
                relative_date = get_time_ago(updated_at)
                st.caption(f"Updated: {relative_date}")
            
            # Action buttons
            if self.show_actions and self.action_callbacks:
                action_cols = st.columns(len(self.action_callbacks))
                
                for i, (action_name, callback) in enumerate(self.action_callbacks.items()):
                    with action_cols[i]:
                        if st.button(action_name, 
                                   key=f"{action_name}_{self.template_data.get('id', 'unknown')}", 
                                   use_container_width=True):
                            if callback:
                                callback(self.template_data)

class UserCard(BaseCard):
    """Card for displaying user information"""
    
    def __init__(self, user_data: Dict[str, Any], 
                 show_actions: bool = True,
                 action_callbacks: Dict[str, Callable] = None, **kwargs):
        user_name = format_user_name(user_data.get('full_name', ''), user_data.get('user_type'))
        super().__init__(user_name, **kwargs)
        self.user_data = user_data
        self.show_actions = show_actions
        self.action_callbacks = action_callbacks or {}
    
    def render(self):
        """Render user card"""
        with st.container():
            # User header
            col_info, col_status = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**{self.title}**")
                
                # Username and role
                username = self.user_data.get('username', '')
                user_type = self.user_data.get('user_type', '').replace('_', ' ').title()
                st.caption(f"@{username} | {user_type}")
                
                # Medical license for doctors
                if self.user_data.get('user_type') == 'doctor':
                    license_num = self.user_data.get('medical_license', '')
                    specialization = self.user_data.get('specialization', '')
                    
                    if license_num:
                        st.caption(f"License: {license_num}")
                    if specialization:
                        st.caption(f"Specialization: {specialization}")
            
            with col_status:
                if self.user_data.get('is_active', True):
                    st.success("Active")
                else:
                    st.error("Inactive")
            
            # Contact information
            email = self.user_data.get('email', '')
            phone = self.user_data.get('phone', '')
            
            if email:
                st.markdown(f"📧 {email}")
            
            if phone:
                formatted_phone = format_phone_number(phone)
                st.markdown(f"📞 {formatted_phone}")
            
            # Last login
            last_login = self.user_data.get('last_login', '')
            if last_login:
                relative_time = get_time_ago(last_login)
                st.caption(f"Last login: {relative_time}")
            
            # Action buttons
            if self.show_actions and self.action_callbacks:
                action_cols = st.columns(len(self.action_callbacks))
                
                for i, (action_name, callback) in enumerate(self.action_callbacks.items()):
                    with action_cols[i]:
                        if st.button(action_name, 
                                   key=f"{action_name}_{self.user_data.get('id', 'unknown')}", 
                                   use_container_width=True):
                            if callback:
                                callback(self.user_data)

class AnalyticsCard(BaseCard):
    """Card for displaying analytics and statistics"""
    
    def __init__(self, title: str, metrics: Dict[str, Any], 
                 chart_data: Dict[str, Any] = None,
                 insights: List[str] = None, **kwargs):
        super().__init__(title, **kwargs)
        self.metrics = metrics
        self.chart_data = chart_data
        self.insights = insights or []
    
    def render(self):
        """Render analytics card"""
        with st.container():
            st.markdown(f"**{self.title}**")
            
            # Key metrics
            if self.metrics:
                metric_cols = st.columns(len(self.metrics))
                
                for i, (metric_name, metric_value) in enumerate(self.metrics.items()):
                    with metric_cols[i]:
                        # Format metric value
                        if isinstance(metric_value, dict):
                            value = metric_value.get('value', 0)
                            delta = metric_value.get('delta')
                            st.metric(metric_name, value, delta)
                        else:
                            st.metric(metric_name, metric_value)
            
            # Chart data (if provided)
            if self.chart_data:
                chart_type = self.chart_data.get('type', 'line')
                data = self.chart_data.get('data', [])
                
                if chart_type == 'line' and data:
                    st.line_chart(data)
                elif chart_type == 'bar' and data:
                    st.bar_chart(data)
                elif chart_type == 'area' and data:
                    st.area_chart(data)
            
            # Insights
            if self.insights:
                st.markdown("**Key Insights:**")
                for insight in self.insights:
                    st.markdown(f"• {insight}")

class ActivityCard(BaseCard):
    """Card for displaying recent activity"""
    
    def __init__(self, activities: List[Dict[str, Any]], 
                 max_items: int = 5, **kwargs):
        super().__init__("Recent Activity", **kwargs)
        self.activities = activities
        self.max_items = max_items
    
    def render(self):
        """Render activity card"""
        with st.container():
            st.markdown(f"**{self.title}**")
            
            if not self.activities:
                st.info("No recent activity")
                return
            
            # Display activities
            for activity in self.activities[:self.max_items]:
                col_info, col_time = st.columns([3, 1])
                
                with col_info:
                    action_type = activity.get('action_type', '').replace('_', ' ').title()
                    user_name = activity.get('user_name', 'Unknown')
                    entity_type = activity.get('entity_type', '')
                    
                    activity_text = f"{user_name} {action_type.lower()}"
                    if entity_type:
                        activity_text += f" {entity_type}"
                    
                    st.markdown(activity_text)
                
                with col_time:
                    timestamp = activity.get('timestamp', '')
                    if timestamp:
                        relative_time = get_time_ago(timestamp)
                        st.caption(relative_time)
                
                # Success/failure indicator
                success = activity.get('success', True)
                if not success:
                    st.caption("❌ Failed")

# Utility functions for card components
def render_card_grid(cards: List[BaseCard], columns: int = 3):
    """Render multiple cards in a grid layout"""
    if not cards:
        return
    
    card_cols = st.columns(columns)
    
    for i, card in enumerate(cards):
        with card_cols[i % columns]:
            card.render()

def render_patient_cards(patients: List[Dict[str, Any]], 
                        consultation_status_map: Dict[int, str] = None,
                        action_callbacks: Dict[str, Callable] = None):
    """Render multiple patient cards"""
    if not patients:
        st.info("No patients found")
        return
    
    for patient in patients:
        patient_id = patient.get('id')
        consultation_status = None
        
        if consultation_status_map and patient_id in consultation_status_map:
            consultation_status = consultation_status_map[patient_id]
        
        card = PatientCard(
            patient_data=patient,
            consultation_status=consultation_status,
            action_callbacks=action_callbacks
        )
        card.render()
        st.divider()

def render_prescription_cards(prescriptions: List[Dict[str, Any]], 
                            action_callbacks: Dict[str, Callable] = None):
    """Render multiple prescription cards"""
    if not prescriptions:
        st.info("No prescriptions found")
        return
    
    for prescription in prescriptions:
        card = PrescriptionCard(
            prescription_data=prescription,
            action_callbacks=action_callbacks
        )
        card.render()
        st.divider()

def render_medication_cards(medications: List[Dict[str, Any]], 
                          action_callbacks: Dict[str, Callable] = None,
                          show_details: bool = True):
    """Render multiple medication cards"""
    if not medications:
        st.info("No medications found")
        return
    
    for medication in medications:
        card = MedicationCard(
            medication_data=medication,
            action_callbacks=action_callbacks,
            show_details=show_details
        )
        card.render()
        st.divider()

def render_template_cards(templates: List[Dict[str, Any]], 
                        action_callbacks: Dict[str, Callable] = None):
    """Render multiple template cards"""
    if not templates:
        st.info("No templates found")
        return
    
    for template in templates:
        card = TemplateCard(
            template_data=template,
            action_callbacks=action_callbacks
        )
        card.render()
        st.divider()

def create_dashboard_metrics(metrics_data: Dict[str, Any]) -> List[MetricCard]:
    """Create metric cards for dashboard"""
    metric_cards = []
    
    for metric_name, metric_info in metrics_data.items():
        if isinstance(metric_info, dict):
            card = MetricCard(
                title=metric_info.get('title', metric_name),
                value=str(metric_info.get('value', 0)),
                delta=metric_info.get('delta'),
                delta_color=metric_info.get('delta_color', 'normal'),
                icon=metric_info.get('icon')
            )
        else:
            card = MetricCard(
                title=metric_name.replace('_', ' ').title(),
                value=str(metric_info)
            )
        
        metric_cards.append(card)
    
    return metric_cards