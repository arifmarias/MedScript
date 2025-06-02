"""
MedScript Pro - Database Initialization and Sample Data
This file handles database initialization, creates sample data, and populates the system for demo purposes.
"""

import hashlib
import json
from datetime import datetime, date, timedelta
from config.database import execute_query, execute_transaction, check_database_exists
from config.settings import (
    DEFAULT_ADMIN, DEMO_USERS, VISIT_TYPES, GENDER_OPTIONS,
    DRUG_CLASSES, COMMON_CONDITIONS, COMMON_ALLERGIES
)
from database.models import create_all_tables, create_triggers
import streamlit as st

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_database():
    """
    Initialize the complete database with tables, triggers, and sample data
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        st.info("Initializing MedScript Pro database...")
        
        # Create all tables
        if not create_all_tables():
            return False
        
        # Create triggers
        if not create_triggers():
            st.warning("Some triggers could not be created, but continuing...")
        
        # Populate with sample data
        if not populate_sample_data():
            return False
        
        st.success("🎉 Database initialization completed successfully!")
        return True
        
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return False

def populate_sample_data():
    """Populate database with comprehensive sample data"""
    try:
        st.info("Populating database with sample data...")
        
        # Insert users
        if not insert_sample_users():
            return False
        
        # Insert medications
        if not insert_sample_medications():
            return False
        
        # Insert lab tests
        if not insert_sample_lab_tests():
            return False
        
        # Insert patients
        if not insert_sample_patients():
            return False
        
        # Insert patient visits
        if not insert_sample_visits():
            return False
        
        # Insert sample prescriptions
        if not insert_sample_prescriptions():
            return False
        
        # Insert sample templates
        if not insert_sample_templates():
            return False
        
        st.success("Sample data populated successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error populating sample data: {str(e)}")
        return False

def insert_sample_users():
    """Insert default admin and demo users"""
    try:
        users_data = []
        
        # Add default admin
        admin_data = DEFAULT_ADMIN.copy()
        admin_data['password_hash'] = hash_password(admin_data.pop('password'))
        users_data.append(admin_data)
        
        # Add demo users
        for demo_user in DEMO_USERS:
            user_data = demo_user.copy()
            user_data['password_hash'] = hash_password(user_data.pop('password'))
            users_data.append(user_data)
        
        # Insert users
        for user in users_data:
            query = """
            INSERT OR IGNORE INTO users (
                username, password_hash, full_name, user_type, medical_license,
                specialization, email, phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                user['username'], user['password_hash'], user['full_name'],
                user['user_type'], user.get('medical_license'), user.get('specialization'),
                user.get('email'), user.get('phone')
            )
            execute_query(query, params)
        
        st.success("✅ Sample users created successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample users: {str(e)}")
        return False

def insert_sample_medications():
    """Insert comprehensive medication database"""
    try:
        medications = [
            {
                'name': 'Amoxicillin',
                'generic_name': 'Amoxicillin',
                'brand_names': 'Amoxil, Trimox, Biomox',
                'drug_class': 'Antibiotics',
                'dosage_forms': 'Capsule, Tablet, Suspension',
                'strengths': '250mg, 500mg, 875mg',
                'indications': 'Bacterial infections, respiratory tract infections, urinary tract infections',
                'contraindications': 'Penicillin allergy, severe kidney disease',
                'side_effects': 'Nausea, diarrhea, stomach upset, allergic reactions',
                'interactions': 'Methotrexate, oral contraceptives, warfarin',
                'precautions': 'Take with food, complete full course',
                'dosage_guidelines': 'Adults: 250-500mg every 8 hours'
            },
            {
                'name': 'Metformin',
                'generic_name': 'Metformin HCl',
                'brand_names': 'Glucophage, Fortamet, Riomet',
                'drug_class': 'Antidiabetics',
                'dosage_forms': 'Tablet, Extended-release tablet',
                'strengths': '500mg, 750mg, 850mg, 1000mg',
                'indications': 'Type 2 diabetes mellitus, PCOS',
                'contraindications': 'Kidney disease, metabolic acidosis, heart failure',
                'side_effects': 'Nausea, diarrhea, metallic taste, vitamin B12 deficiency',
                'interactions': 'Alcohol, contrast dyes, diuretics',
                'precautions': 'Take with meals, monitor kidney function',
                'dosage_guidelines': 'Start 500mg twice daily, max 2000mg daily'
            },
            {
                'name': 'Lisinopril',
                'generic_name': 'Lisinopril',
                'brand_names': 'Prinivil, Zestril',
                'drug_class': 'Antihypertensives',
                'dosage_forms': 'Tablet',
                'strengths': '2.5mg, 5mg, 10mg, 20mg, 40mg',
                'indications': 'Hypertension, heart failure, post-MI',
                'contraindications': 'Pregnancy, angioedema history, bilateral renal artery stenosis',
                'side_effects': 'Dry cough, dizziness, hyperkalemia, angioedema',
                'interactions': 'NSAIDs, potassium supplements, lithium',
                'precautions': 'Monitor blood pressure and kidney function',
                'dosage_guidelines': 'Start 10mg daily, adjust based on response'
            },
            {
                'name': 'Atorvastatin',
                'generic_name': 'Atorvastatin Calcium',
                'brand_names': 'Lipitor',
                'drug_class': 'Cardiovascular',
                'dosage_forms': 'Tablet',
                'strengths': '10mg, 20mg, 40mg, 80mg',
                'indications': 'Hypercholesterolemia, cardiovascular disease prevention',
                'contraindications': 'Active liver disease, pregnancy, breastfeeding',
                'side_effects': 'Muscle pain, liver enzyme elevation, diabetes risk',
                'interactions': 'Warfarin, digoxin, cyclosporine, grapefruit juice',
                'precautions': 'Monitor liver function, check for muscle symptoms',
                'dosage_guidelines': 'Start 20mg daily, max 80mg daily'
            },
            {
                'name': 'Omeprazole',
                'generic_name': 'Omeprazole',
                'brand_names': 'Prilosec, Losec',
                'drug_class': 'Gastrointestinal',
                'dosage_forms': 'Capsule, Tablet',
                'strengths': '10mg, 20mg, 40mg',
                'indications': 'GERD, peptic ulcer disease, H. pylori eradication',
                'contraindications': 'Hypersensitivity to proton pump inhibitors',
                'side_effects': 'Headache, nausea, diarrhea, vitamin B12 deficiency',
                'interactions': 'Clopidogrel, warfarin, phenytoin, ketoconazole',
                'precautions': 'Risk of C. diff infection, fractures with long-term use',
                'dosage_guidelines': '20mg daily before breakfast'
            },
            {
                'name': 'Albuterol',
                'generic_name': 'Albuterol Sulfate',
                'brand_names': 'ProAir, Ventolin, Proventil',
                'drug_class': 'Bronchodilators',
                'dosage_forms': 'Inhaler, Nebulizer solution, Tablet',
                'strengths': '90mcg/actuation, 2.5mg/3ml, 2mg, 4mg',
                'indications': 'Asthma, COPD, exercise-induced bronchospasm',
                'contraindications': 'Hypersensitivity to sympathomimetics',
                'side_effects': 'Tremor, palpitations, headache, throat irritation',
                'interactions': 'Beta-blockers, MAO inhibitors, tricyclic antidepressants',
                'precautions': 'Monitor heart rate, proper inhaler technique',
                'dosage_guidelines': '1-2 puffs every 4-6 hours as needed'
            },
            {
                'name': 'Ibuprofen',
                'generic_name': 'Ibuprofen',
                'brand_names': 'Advil, Motrin, Nuprin',
                'drug_class': 'Anti-inflammatory',
                'dosage_forms': 'Tablet, Capsule, Suspension, Injection',
                'strengths': '200mg, 400mg, 600mg, 800mg',
                'indications': 'Pain, inflammation, fever, arthritis',
                'contraindications': 'Aspirin allergy, severe heart failure, active GI bleeding',
                'side_effects': 'GI upset, bleeding, kidney problems, cardiovascular risks',
                'interactions': 'Warfarin, ACE inhibitors, lithium, methotrexate',
                'precautions': 'Take with food, avoid in pregnancy third trimester',
                'dosage_guidelines': '400-800mg every 6-8 hours, max 3200mg daily'
            },
            {
                'name': 'Prednisone',
                'generic_name': 'Prednisone',
                'brand_names': 'Deltasone, Rayos',
                'drug_class': 'Corticosteroids',
                'dosage_forms': 'Tablet, Solution',
                'strengths': '1mg, 2.5mg, 5mg, 10mg, 20mg, 50mg',
                'indications': 'Inflammation, autoimmune conditions, allergic reactions',
                'contraindications': 'Systemic fungal infections, live vaccines',
                'side_effects': 'Weight gain, mood changes, increased infection risk, osteoporosis',
                'interactions': 'NSAIDs, warfarin, insulin, vaccines',
                'precautions': 'Taper gradually, monitor blood sugar and blood pressure',
                'dosage_guidelines': 'Variable dosing based on condition and severity'
            },
            {
                'name': 'Amlodipine',
                'generic_name': 'Amlodipine Besylate',
                'brand_names': 'Norvasc',
                'drug_class': 'Antihypertensives',
                'dosage_forms': 'Tablet',
                'strengths': '2.5mg, 5mg, 10mg',
                'indications': 'Hypertension, angina',
                'contraindications': 'Severe aortic stenosis, cardiogenic shock',
                'side_effects': 'Ankle swelling, dizziness, flushing, palpitations',
                'interactions': 'Simvastatin, cyclosporine, tacrolimus',
                'precautions': 'Monitor blood pressure, check for edema',
                'dosage_guidelines': 'Start 5mg daily, max 10mg daily'
            },
            {
                'name': 'Sertraline',
                'generic_name': 'Sertraline HCl',
                'brand_names': 'Zoloft',
                'drug_class': 'Antidepressants',
                'dosage_forms': 'Tablet, Oral concentrate',
                'strengths': '25mg, 50mg, 100mg',
                'indications': 'Depression, anxiety disorders, PTSD, OCD',
                'contraindications': 'MAO inhibitor use, pimozide use',
                'side_effects': 'Nausea, insomnia, sexual dysfunction, weight changes',
                'interactions': 'MAO inhibitors, warfarin, NSAIDs, other antidepressants',
                'precautions': 'Monitor for suicidal thoughts, taper when discontinuing',
                'dosage_guidelines': 'Start 50mg daily, adjust weekly by 25-50mg'
            }
        ]
        
        # Add more medications to reach 50+
        additional_medications = [
            ('Acetaminophen', 'Acetaminophen', 'Tylenol', 'Analgesics', 'Tablet, Suspension', '325mg, 500mg, 650mg'),
            ('Aspirin', 'Acetylsalicylic Acid', 'Bayer, Bufferin', 'Analgesics', 'Tablet', '81mg, 325mg'),
            ('Losartan', 'Losartan Potassium', 'Cozaar', 'Antihypertensives', 'Tablet', '25mg, 50mg, 100mg'),
            ('Simvastatin', 'Simvastatin', 'Zocor', 'Cardiovascular', 'Tablet', '5mg, 10mg, 20mg, 40mg'),
            ('Levothyroxine', 'Levothyroxine Sodium', 'Synthroid', 'Hormones', 'Tablet', '25mcg, 50mcg, 75mcg, 100mcg'),
            ('Warfarin', 'Warfarin Sodium', 'Coumadin', 'Cardiovascular', 'Tablet', '1mg, 2mg, 2.5mg, 5mg, 10mg'),
            ('Furosemide', 'Furosemide', 'Lasix', 'Diuretics', 'Tablet, Injection', '20mg, 40mg, 80mg'),
            ('Insulin Glargine', 'Insulin Glargine', 'Lantus', 'Antidiabetics', 'Injection', '100 units/ml'),
            ('Clopidogrel', 'Clopidogrel Bisulfate', 'Plavix', 'Cardiovascular', 'Tablet', '75mg'),
            ('Pantoprazole', 'Pantoprazole Sodium', 'Protonix', 'Gastrointestinal', 'Tablet', '20mg, 40mg'),
            ('Hydrochlorothiazide', 'Hydrochlorothiazide', 'Microzide', 'Diuretics', 'Tablet', '12.5mg, 25mg, 50mg'),
            ('Gabapentin', 'Gabapentin', 'Neurontin', 'Neurological', 'Capsule', '100mg, 300mg, 400mg'),
            ('Tramadol', 'Tramadol HCl', 'Ultram', 'Analgesics', 'Tablet', '50mg, 100mg'),
            ('Ciprofloxacin', 'Ciprofloxacin', 'Cipro', 'Antibiotics', 'Tablet', '250mg, 500mg, 750mg'),
            ('Doxycycline', 'Doxycycline', 'Vibramycin', 'Antibiotics', 'Tablet, Capsule', '50mg, 100mg'),
            ('Fluticasone', 'Fluticasone Propionate', 'Flonase', 'Corticosteroids', 'Nasal spray', '50mcg/spray'),
            ('Montelukast', 'Montelukast Sodium', 'Singulair', 'Bronchodilators', 'Tablet', '4mg, 5mg, 10mg'),
            ('Escitalopram', 'Escitalopram Oxalate', 'Lexapro', 'Antidepressants', 'Tablet', '5mg, 10mg, 20mg'),
            ('Trazodone', 'Trazodone HCl', 'Desyrel', 'Antidepressants', 'Tablet', '50mg, 100mg, 150mg'),
            ('Lorazepam', 'Lorazepam', 'Ativan', 'Neurological', 'Tablet', '0.5mg, 1mg, 2mg'),
            ('Alprazolam', 'Alprazolam', 'Xanax', 'Neurological', 'Tablet', '0.25mg, 0.5mg, 1mg, 2mg'),
            ('Clonazepam', 'Clonazepam', 'Klonopin', 'Neurological', 'Tablet', '0.5mg, 1mg, 2mg'),
            ('Metoprolol', 'Metoprolol Tartrate', 'Lopressor', 'Cardiovascular', 'Tablet', '25mg, 50mg, 100mg'),
            ('Carvedilol', 'Carvedilol', 'Coreg', 'Cardiovascular', 'Tablet', '3.125mg, 6.25mg, 12.5mg, 25mg'),
            ('Digoxin', 'Digoxin', 'Lanoxin', 'Cardiovascular', 'Tablet', '0.125mg, 0.25mg'),
            ('Spironolactone', 'Spironolactone', 'Aldactone', 'Diuretics', 'Tablet', '25mg, 50mg, 100mg'),
            ('Allopurinol', 'Allopurinol', 'Zyloprim', 'Anti-inflammatory', 'Tablet', '100mg, 300mg'),
            ('Colchicine', 'Colchicine', 'Colcrys', 'Anti-inflammatory', 'Tablet', '0.6mg'),
            ('Azithromycin', 'Azithromycin', 'Zithromax', 'Antibiotics', 'Tablet, Suspension', '250mg, 500mg'),
            ('Cephalexin', 'Cephalexin', 'Keflex', 'Antibiotics', 'Capsule', '250mg, 500mg'),
            ('Clindamycin', 'Clindamycin', 'Cleocin', 'Antibiotics', 'Capsule', '150mg, 300mg'),
            ('Fluconazole', 'Fluconazole', 'Diflucan', 'Antifungals', 'Tablet', '50mg, 100mg, 150mg, 200mg'),
            ('Ranitidine', 'Ranitidine HCl', 'Zantac', 'Gastrointestinal', 'Tablet', '75mg, 150mg, 300mg'),
            ('Famotidine', 'Famotidine', 'Pepcid', 'Gastrointestinal', 'Tablet', '10mg, 20mg, 40mg'),
            ('Ondansetron', 'Ondansetron', 'Zofran', 'Gastrointestinal', 'Tablet', '4mg, 8mg'),
            ('Meclizine', 'Meclizine HCl', 'Antivert', 'Gastrointestinal', 'Tablet', '12.5mg, 25mg'),
            ('Diphenhydramine', 'Diphenhydramine HCl', 'Benadryl', 'Antihistamines', 'Capsule', '25mg, 50mg'),
            ('Cetirizine', 'Cetirizine HCl', 'Zyrtec', 'Antihistamines', 'Tablet', '5mg, 10mg'),
            ('Loratadine', 'Loratadine', 'Claritin', 'Antihistamines', 'Tablet', '10mg'),
            ('Fexofenadine', 'Fexofenadine HCl', 'Allegra', 'Antihistamines', 'Tablet', '30mg, 60mg, 180mg'),
            ('Vitamin D3', 'Cholecalciferol', 'Various', 'Vitamins & Supplements', 'Tablet, Capsule', '1000 IU, 2000 IU, 5000 IU'),
            ('Vitamin B12', 'Cyanocobalamin', 'Various', 'Vitamins & Supplements', 'Tablet', '100mcg, 500mcg, 1000mcg'),
            ('Folic Acid', 'Folic Acid', 'Various', 'Vitamins & Supplements', 'Tablet', '400mcg, 800mcg, 1mg'),
            ('Iron Sulfate', 'Ferrous Sulfate', 'Various', 'Vitamins & Supplements', 'Tablet', '65mg'),
            ('Calcium Carbonate', 'Calcium Carbonate', 'Tums, Os-Cal', 'Vitamins & Supplements', 'Tablet', '500mg, 600mg'),
            ('Multivitamin', 'Multivitamin', 'Centrum, One-A-Day', 'Vitamins & Supplements', 'Tablet', 'Daily formula'),
            ('Probiotic', 'Lactobacillus', 'Various', 'Gastrointestinal', 'Capsule', 'Multi-strain formula'),
            ('Omega-3', 'Fish Oil', 'Various', 'Vitamins & Supplements', 'Softgel', '1000mg'),
            ('Melatonin', 'Melatonin', 'Various', 'Neurological', 'Tablet', '1mg, 3mg, 5mg, 10mg'),
            ('Glucosamine', 'Glucosamine Sulfate', 'Various', 'Vitamins & Supplements', 'Tablet', '500mg, 750mg')
        ]
        
        # Insert basic medications
        for med in medications:
            query = """
            INSERT OR IGNORE INTO medications (
                name, generic_name, brand_names, drug_class, dosage_forms, strengths,
                indications, contraindications, side_effects, interactions, precautions, dosage_guidelines
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                med['name'], med['generic_name'], med['brand_names'], med['drug_class'],
                med['dosage_forms'], med['strengths'], med['indications'], med['contraindications'],
                med['side_effects'], med['interactions'], med['precautions'], med['dosage_guidelines']
            )
            execute_query(query, params)
        
        # Insert additional medications
        for med in additional_medications:
            query = """
            INSERT OR IGNORE INTO medications (
                name, generic_name, brand_names, drug_class, dosage_forms, strengths
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            execute_query(query, med)
        
        st.success("✅ Sample medications inserted successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample medications: {str(e)}")
        return False

def insert_sample_lab_tests():
    """Insert comprehensive lab test database"""
    try:
        lab_tests = [
            # Hematology
            ('Complete Blood Count (CBC)', 'CBC001', 'Hematology', 'WBC: 4.5-11.0 K/uL, RBC: 4.2-5.4 M/uL', 'K/uL, M/uL', 'Comprehensive blood cell analysis', 'Fasting not required', 'Blood'),
            ('Hemoglobin', 'HGB001', 'Hematology', 'Male: 14-18 g/dL, Female: 12-16 g/dL', 'g/dL', 'Oxygen-carrying protein in red blood cells', 'None required', 'Blood'),
            ('Hematocrit', 'HCT001', 'Hematology', 'Male: 42-52%, Female: 37-47%', '%', 'Percentage of blood volume occupied by red blood cells', 'None required', 'Blood'),
            ('Platelet Count', 'PLT001', 'Hematology', '150-450 K/uL', 'K/uL', 'Blood clotting cell count', 'None required', 'Blood'),
            ('ESR (Erythrocyte Sedimentation Rate)', 'ESR001', 'Hematology', 'Male: 0-15 mm/hr, Female: 0-20 mm/hr', 'mm/hr', 'Inflammation marker', 'None required', 'Blood'),
            
            # Clinical Chemistry
            ('Comprehensive Metabolic Panel (CMP)', 'CMP001', 'Clinical Chemistry', 'Multiple parameters', 'Various', 'Complete metabolic assessment', '8-12 hours fasting', 'Blood'),
            ('Basic Metabolic Panel (BMP)', 'BMP001', 'Clinical Chemistry', 'Multiple parameters', 'Various', 'Basic metabolic assessment', '8-12 hours fasting', 'Blood'),
            ('Glucose (Fasting)', 'GLU001', 'Clinical Chemistry', '70-100 mg/dL', 'mg/dL', 'Blood sugar level', '8-12 hours fasting required', 'Blood'),
            ('HbA1c (Glycated Hemoglobin)', 'HBA1C001', 'Clinical Chemistry', '<5.7% (normal)', '%', 'Average blood sugar over 2-3 months', 'No fasting required', 'Blood'),
            ('Creatinine', 'CREAT001', 'Clinical Chemistry', 'Male: 0.7-1.3 mg/dL, Female: 0.6-1.1 mg/dL', 'mg/dL', 'Kidney function marker', 'None required', 'Blood'),
            ('Blood Urea Nitrogen (BUN)', 'BUN001', 'Clinical Chemistry', '7-20 mg/dL', 'mg/dL', 'Kidney function and protein metabolism', 'None required', 'Blood'),
            ('Total Cholesterol', 'CHOL001', 'Clinical Chemistry', '<200 mg/dL (desirable)', 'mg/dL', 'Cardiovascular risk assessment', '9-12 hours fasting', 'Blood'),
            ('LDL Cholesterol', 'LDL001', 'Clinical Chemistry', '<100 mg/dL (optimal)', 'mg/dL', 'Bad cholesterol', '9-12 hours fasting', 'Blood'),
            ('HDL Cholesterol', 'HDL001', 'Clinical Chemistry', 'Male: >40 mg/dL, Female: >50 mg/dL', 'mg/dL', 'Good cholesterol', '9-12 hours fasting', 'Blood'),
            ('Triglycerides', 'TRIG001', 'Clinical Chemistry', '<150 mg/dL', 'mg/dL', 'Blood fat levels', '9-12 hours fasting', 'Blood'),
            
            # Endocrinology
            ('TSH (Thyroid Stimulating Hormone)', 'TSH001', 'Endocrinology', '0.4-4.0 mIU/L', 'mIU/L', 'Thyroid function assessment', 'None required', 'Blood'),
            ('T3 (Triiodothyronine)', 'T3001', 'Endocrinology', '80-200 ng/dL', 'ng/dL', 'Active thyroid hormone', 'None required', 'Blood'),
            ('T4 (Thyroxine)', 'T4001', 'Endocrinology', '5.0-12.0 μg/dL', 'μg/dL', 'Thyroid hormone', 'None required', 'Blood'),
            ('Insulin', 'INS001', 'Endocrinology', '2.6-24.9 μIU/mL', 'μIU/mL', 'Blood sugar regulation hormone', '8-12 hours fasting', 'Blood'),
            ('Cortisol', 'CORT001', 'Endocrinology', '6-23 μg/dL (morning)', 'μg/dL', 'Stress hormone', 'Morning collection preferred', 'Blood'),
            
            # Immunology
            ('C-Reactive Protein (CRP)', 'CRP001', 'Immunology', '<3.0 mg/L', 'mg/L', 'Inflammation and infection marker', 'None required', 'Blood'),
            ('Rheumatoid Factor (RF)', 'RF001', 'Immunology', '<14 IU/mL', 'IU/mL', 'Autoimmune disorder marker', 'None required', 'Blood'),
            ('ANA (Antinuclear Antibodies)', 'ANA001', 'Immunology', 'Negative', 'Titer', 'Autoimmune screening', 'None required', 'Blood'),
            
            # Microbiology
            ('Urine Culture', 'UCULT001', 'Microbiology', 'No growth', 'CFU/mL', 'Urinary tract infection detection', 'Clean catch specimen', 'Urine'),
            ('Blood Culture', 'BCULT001', 'Microbiology', 'No growth', 'Qualitative', 'Bloodstream infection detection', 'Before antibiotic therapy', 'Blood'),
            ('Stool Culture', 'SCULT001', 'Microbiology', 'Normal flora', 'Qualitative', 'Gastrointestinal infection detection', 'Fresh specimen preferred', 'Stool'),
            
            # Pathology
            ('Pap Smear', 'PAP001', 'Pathology', 'Normal', 'Qualitative', 'Cervical cancer screening', 'Avoid during menstruation', 'Cervical cells'),
            ('Biopsy', 'BX001', 'Pathology', 'Benign', 'Qualitative', 'Tissue examination for cancer/disease', 'Local anesthesia may be required', 'Tissue'),
            
            # Cardiology
            ('Troponin I', 'TROP001', 'Cardiology', '<0.04 ng/mL', 'ng/mL', 'Heart attack marker', 'None required', 'Blood'),
            ('BNP (B-type Natriuretic Peptide)', 'BNP001', 'Cardiology', '<100 pg/mL', 'pg/mL', 'Heart failure marker', 'None required', 'Blood'),
            ('CK-MB (Creatine Kinase-MB)', 'CKMB001', 'Cardiology', '0-6.3 ng/mL', 'ng/mL', 'Heart muscle damage marker', 'None required', 'Blood'),
            
            # Additional Common Tests
            ('Urinalysis', 'URINE001', 'Clinical Chemistry', 'Multiple parameters normal', 'Various', 'Comprehensive urine analysis', 'Clean catch midstream', 'Urine'),
            ('Liver Function Tests (LFT)', 'LFT001', 'Clinical Chemistry', 'ALT: 7-56 U/L, AST: 10-40 U/L', 'U/L', 'Liver health assessment', 'None required', 'Blood'),
            ('Vitamin D, 25-Hydroxy', 'VITD001', 'Endocrinology', '30-100 ng/mL', 'ng/mL', 'Vitamin D status', 'None required', 'Blood'),
            ('Vitamin B12', 'VITB12001', 'Clinical Chemistry', '200-900 pg/mL', 'pg/mL', 'B12 deficiency screening', 'None required', 'Blood'),
            ('Folate', 'FOLATE001', 'Clinical Chemistry', '2.7-17.0 ng/mL', 'ng/mL', 'Folate deficiency screening', 'None required', 'Blood'),
            ('Iron Studies', 'IRON001', 'Hematology', 'Multiple parameters', 'Various', 'Iron deficiency assessment', 'Morning fasting preferred', 'Blood'),
            ('PSA (Prostate Specific Antigen)', 'PSA001', 'Endocrinology', '<4.0 ng/mL', 'ng/mL', 'Prostate cancer screening', 'None required', 'Blood')
        ]
        
        # Insert lab tests
        for test in lab_tests:
            query = """
            INSERT OR IGNORE INTO lab_tests (
                test_name, test_code, test_category, normal_range, units,
                description, preparation_required, sample_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            execute_query(query, test)
        
        st.success("✅ Sample lab tests inserted successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample lab tests: {str(e)}")
        return False

def insert_sample_patients():
    """Insert sample patients with comprehensive information"""
    try:
        patients = [
            {
                'patient_id': 'PT-20240101-000001',
                'first_name': 'John',
                'last_name': 'Smith',
                'date_of_birth': '1985-05-15',
                'gender': 'Male',
                'phone': '+1234567893',
                'email': 'john.smith@email.com',
                'address': '123 Main Street, Springfield, IL 62701',
                'allergies': 'Penicillin, Shellfish',
                'medical_conditions': 'Hypertension, Type 2 Diabetes',
                'emergency_contact': 'Jane Smith (Wife)',
                'emergency_phone': '+1234567894',
                'insurance_info': 'Blue Cross Blue Shield - Policy #12345',
                'blood_group': 'O+',
                'weight': 180.5,
                'height': 70.0,
                'notes': 'Patient prefers morning appointments. Has history of good medication compliance.'
            },
            {
                'patient_id': 'PT-20240101-000002',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'date_of_birth': '1992-08-22',
                'gender': 'Female',
                'phone': '+1234567895',
                'email': 'sarah.johnson@email.com',
                'address': '456 Oak Avenue, Springfield, IL 62702',
                'allergies': 'Latex, NSAIDs',
                'medical_conditions': 'Asthma, Seasonal Allergies',
                'emergency_contact': 'Mike Johnson (Husband)',
                'emergency_phone': '+1234567896',
                'insurance_info': 'Aetna - Policy #67890',
                'blood_group': 'A+',
                'weight': 135.0,
                'height': 64.0,
                'notes': 'Pregnant - Due date April 2024. Regular prenatal care needed.'
            },
            {
                'patient_id': 'PT-20240101-000003',
                'first_name': 'Robert',
                'last_name': 'Williams',
                'date_of_birth': '1978-12-03',
                'gender': 'Male',
                'phone': '+1234567897',
                'email': 'robert.williams@email.com',
                'address': '789 Pine Road, Springfield, IL 62703',
                'allergies': 'Sulfa drugs, Codeine',
                'medical_conditions': 'Heart Disease, High Cholesterol, COPD',
                'emergency_contact': 'Linda Williams (Wife)',
                'emergency_phone': '+1234567898',
                'insurance_info': 'Medicare - ID #ABC123456',
                'blood_group': 'B+',
                'weight': 220.0,
                'height': 72.0,
                'notes': 'Former smoker (quit 2020). Requires cardiac monitoring.'
            },
            {
                'patient_id': 'PT-20240101-000004',
                'first_name': 'Maria',
                'last_name': 'Garcia',
                'date_of_birth': '1995-03-10',
                'gender': 'Female',
                'phone': '+1234567899',
                'email': 'maria.garcia@email.com',
                'address': '321 Elm Street, Springfield, IL 62704',
                'allergies': 'None known',
                'medical_conditions': 'Migraine, Anxiety',
                'emergency_contact': 'Carlos Garcia (Brother)',
                'emergency_phone': '+1234567800',
                'insurance_info': 'United Healthcare - Policy #XYZ789',
                'blood_group': 'AB+',
                'weight': 128.0,
                'height': 62.0,
                'notes': 'College student. Stress-related symptoms. Regular exercise routine.'
            },
            {
                'patient_id': 'PT-20240101-000005',
                'first_name': 'James',
                'last_name': 'Brown',
                'date_of_birth': '1960-11-18',
                'gender': 'Male',
                'phone': '+1234567801',
                'email': 'james.brown@email.com',
                'address': '654 Maple Drive, Springfield, IL 62705',
                'allergies': 'Aspirin, Iodine',
                'medical_conditions': 'Arthritis, Kidney Disease, Depression',
                'emergency_contact': 'Patricia Brown (Daughter)',
                'emergency_phone': '+1234567802',
                'insurance_info': 'Medicaid - ID #DEF456789',
                'blood_group': 'O-',
                'weight': 165.0,
                'height': 68.0,
                'notes': 'Retired teacher. Lives alone. Needs medication reminders.'
            }
        ]
        
        # Get created_by user ID (assistant1)
        created_by_query = "SELECT id FROM users WHERE username = 'assistant1'"
        user_result = execute_query(created_by_query, fetch='one')
        created_by = user_result['id'] if user_result else 1
        
        # Insert patients
        for patient in patients:
            query = """
            INSERT OR IGNORE INTO patients (
                patient_id, first_name, last_name, date_of_birth, gender, phone, email,
                address, allergies, medical_conditions, emergency_contact, emergency_phone,
                insurance_info, blood_group, weight, height, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                patient['patient_id'], patient['first_name'], patient['last_name'],
                patient['date_of_birth'], patient['gender'], patient['phone'], patient['email'],
                patient['address'], patient['allergies'], patient['medical_conditions'],
                patient['emergency_contact'], patient['emergency_phone'], patient['insurance_info'],
                patient['blood_group'], patient['weight'], patient['height'], patient['notes'], created_by
            )
            execute_query(query, params)
        
        st.success("✅ Sample patients inserted successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample patients: {str(e)}")
        return False

def insert_sample_visits():
    """Insert sample patient visits for today's workflow testing"""
    try:
        today = date.today()
        
        visits = [
            {
                'patient_id': 1,  # John Smith
                'visit_date': today,
                'visit_time': '09:00:00',
                'visit_type': 'Follow-up',
                'current_problems': 'Blood pressure check, diabetes monitoring',
                'is_followup': True,
                'vital_signs': 'Stable vitals',
                'blood_pressure': '140/90',
                'temperature': 98.6,
                'pulse_rate': 78,
                'respiratory_rate': 16,
                'oxygen_saturation': 98.0,
                'notes': 'Patient reports good medication compliance. Some dietary concerns.',
                'consultation_completed': False
            },
            {
                'patient_id': 2,  # Sarah Johnson
                'visit_date': today,
                'visit_time': '10:30:00',
                'visit_type': 'Routine Check-up',
                'current_problems': 'Prenatal checkup, asthma management',
                'is_followup': False,
                'vital_signs': 'Normal pregnancy vitals',
                'blood_pressure': '115/75',
                'temperature': 98.4,
                'pulse_rate': 85,
                'respiratory_rate': 18,
                'oxygen_saturation': 99.0,
                'notes': 'Prenatal visit at 20 weeks. Baby developing normally.',
                'consultation_completed': False
            },
            {
                'patient_id': 3,  # Robert Williams
                'visit_date': today,
                'visit_time': '14:00:00',
                'visit_type': 'Emergency',
                'current_problems': 'Chest discomfort, shortness of breath',
                'is_followup': False,
                'vital_signs': 'Elevated BP, tachycardia',
                'blood_pressure': '165/105',
                'temperature': 98.8,
                'pulse_rate': 102,
                'respiratory_rate': 22,
                'oxygen_saturation': 94.0,
                'notes': 'Urgent evaluation needed. Possible cardiac event.',
                'consultation_completed': False
            },
            {
                'patient_id': 4,  # Maria Garcia
                'visit_date': today,
                'visit_time': '15:30:00',
                'visit_type': 'Initial Consultation',
                'current_problems': 'Severe headaches, stress management',
                'is_followup': False,
                'vital_signs': 'Normal vitals',
                'blood_pressure': '118/78',
                'temperature': 98.5,
                'pulse_rate': 72,
                'respiratory_rate': 16,
                'oxygen_saturation': 98.5,
                'notes': 'New patient. Student stress and migraine evaluation.',
                'consultation_completed': False
            },
            {
                'patient_id': 5,  # James Brown
                'visit_date': today,
                'visit_time': '16:45:00',
                'visit_type': 'Follow-up',
                'current_problems': 'Arthritis pain management, mood assessment',
                'is_followup': True,
                'vital_signs': 'Stable',
                'blood_pressure': '128/82',
                'temperature': 98.3,
                'pulse_rate': 68,
                'respiratory_rate': 14,
                'oxygen_saturation': 97.0,
                'notes': 'Regular follow-up. Arthritis worsening, mood stable.',
                'consultation_completed': False
            }
        ]
        
        # Get created_by user ID (assistant1)
        created_by_query = "SELECT id FROM users WHERE username = 'assistant1'"
        user_result = execute_query(created_by_query, fetch='one')
        created_by = user_result['id'] if user_result else 1
        
        # Insert visits
        for visit in visits:
            query = """
            INSERT OR IGNORE INTO patient_visits (
                patient_id, visit_date, visit_time, visit_type, current_problems,
                is_followup, vital_signs, blood_pressure, temperature, pulse_rate,
                respiratory_rate, oxygen_saturation, notes, created_by, consultation_completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                visit['patient_id'], visit['visit_date'], visit['visit_time'], visit['visit_type'],
                visit['current_problems'], visit['is_followup'], visit['vital_signs'],
                visit['blood_pressure'], visit['temperature'], visit['pulse_rate'],
                visit['respiratory_rate'], visit['oxygen_saturation'], visit['notes'],
                created_by, visit['consultation_completed']
            )
            execute_query(query, params)
        
        st.success("✅ Sample patient visits inserted successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample visits: {str(e)}")
        return False

def insert_sample_prescriptions():
    """Insert sample prescriptions for demonstration"""
    try:
        # Get doctor and patient IDs
        doctor_query = "SELECT id FROM users WHERE username = 'doctor1'"
        doctor_result = execute_query(doctor_query, fetch='one')
        doctor_id = doctor_result['id'] if doctor_result else 1
        
        prescriptions = [
            {
                'prescription_id': 'RX-20240101-000001',
                'doctor_id': doctor_id,
                'patient_id': 1,  # John Smith
                'diagnosis': 'Hypertension, Type 2 Diabetes Mellitus',
                'chief_complaint': 'Blood pressure monitoring and diabetes management',
                'notes': 'Continue current medications. Monitor blood glucose levels.',
                'status': 'Active',
                'follow_up_date': (datetime.now() + timedelta(days=30)).date(),
                'follow_up_instructions': 'Return in 4 weeks for BP and glucose check'
            }
        ]
        
        # Insert prescriptions
        for prescription in prescriptions:
            query = """
            INSERT OR IGNORE INTO prescriptions (
                prescription_id, doctor_id, patient_id, diagnosis, chief_complaint,
                notes, status, follow_up_date, follow_up_instructions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                prescription['prescription_id'], prescription['doctor_id'], prescription['patient_id'],
                prescription['diagnosis'], prescription['chief_complaint'], prescription['notes'],
                prescription['status'], prescription['follow_up_date'], prescription['follow_up_instructions']
            )
            prescription_id = execute_query(query, params)
            
            # Insert prescription items (medications)
            if prescription_id:
                # Get medication IDs
                med_queries = [
                    ("SELECT id FROM medications WHERE name = 'Lisinopril'", ('Lisinopril 10mg', 'Once daily', '30 days', '30 tablets', 'Take in the morning')),
                    ("SELECT id FROM medications WHERE name = 'Metformin'", ('Metformin 500mg', 'Twice daily', '30 days', '60 tablets', 'Take with meals'))
                ]
                
                for med_query, med_info in med_queries:
                    med_result = execute_query(med_query, fetch='one')
                    if med_result:
                        item_query = """
                        INSERT INTO prescription_items (
                            prescription_id, medication_id, dosage, frequency, duration, quantity, instructions
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
                        item_params = (prescription_id, med_result['id']) + med_info
                        execute_query(item_query, item_params)
                
                # Insert lab tests
                lab_test_queries = [
                    ("SELECT id FROM lab_tests WHERE test_name = 'HbA1c (Glycated Hemoglobin)'", 'Monitor diabetes control', 'Routine'),
                    ("SELECT id FROM lab_tests WHERE test_name = 'Comprehensive Metabolic Panel (CMP)'", 'Monitor kidney function and electrolytes', 'Routine')
                ]
                
                for lab_query, instructions, urgency in lab_test_queries:
                    lab_result = execute_query(lab_query, fetch='one')
                    if lab_result:
                        lab_item_query = """
                        INSERT INTO prescription_lab_tests (
                            prescription_id, lab_test_id, instructions, urgency
                        ) VALUES (?, ?, ?, ?)
                        """
                        lab_params = (prescription_id, lab_result['id'], instructions, urgency)
                        execute_query(lab_item_query, lab_params)
        
        st.success("✅ Sample prescriptions inserted successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample prescriptions: {str(e)}")
        return False

def insert_sample_templates():
    """Insert sample prescription templates for doctors"""
    try:
        # Get doctor ID
        doctor_query = "SELECT id FROM users WHERE username = 'doctor1'"
        doctor_result = execute_query(doctor_query, fetch='one')
        doctor_id = doctor_result['id'] if doctor_result else 1
        
        templates = [
            {
                'doctor_id': doctor_id,
                'name': 'Hypertension Management',
                'category': 'Cardiology',
                'description': 'Standard hypertension treatment protocol',
                'template_data': json.dumps({
                    'diagnosis': 'Essential Hypertension',
                    'medications': [
                        {'name': 'Lisinopril', 'dosage': '10mg', 'frequency': 'Once daily'},
                        {'name': 'Amlodipine', 'dosage': '5mg', 'frequency': 'Once daily'}
                    ],
                    'lab_tests': [
                        {'name': 'Comprehensive Metabolic Panel (CMP)', 'urgency': 'Routine'},
                        {'name': 'Lipid Panel', 'urgency': 'Routine'}
                    ]
                }),
                'diagnosis_template': 'Essential Hypertension',
                'instructions_template': 'Monitor blood pressure daily. Return in 4 weeks.'
            },
            {
                'doctor_id': doctor_id,
                'name': 'Diabetes Type 2 Management',
                'category': 'Endocrinology',
                'description': 'Type 2 diabetes treatment protocol',
                'template_data': json.dumps({
                    'diagnosis': 'Type 2 Diabetes Mellitus',
                    'medications': [
                        {'name': 'Metformin', 'dosage': '500mg', 'frequency': 'Twice daily'},
                        {'name': 'Glimepiride', 'dosage': '2mg', 'frequency': 'Once daily'}
                    ],
                    'lab_tests': [
                        {'name': 'HbA1c (Glycated Hemoglobin)', 'urgency': 'Routine'},
                        {'name': 'Glucose (Fasting)', 'urgency': 'Routine'}
                    ]
                }),
                'diagnosis_template': 'Type 2 Diabetes Mellitus',
                'instructions_template': 'Monitor blood glucose. Diet and exercise counseling.'
            },
            {
                'doctor_id': doctor_id,
                'name': 'Upper Respiratory Infection',
                'category': 'General Medicine',
                'description': 'Common cold and URI treatment',
                'template_data': json.dumps({
                    'diagnosis': 'Upper Respiratory Tract Infection',
                    'medications': [
                        {'name': 'Acetaminophen', 'dosage': '500mg', 'frequency': 'Every 6 hours as needed'},
                        {'name': 'Dextromethorphan', 'dosage': '15mg', 'frequency': 'Every 4 hours as needed'}
                    ],
                    'lab_tests': []
                }),
                'diagnosis_template': 'Upper Respiratory Tract Infection',
                'instructions_template': 'Rest, fluids, return if symptoms worsen or persist >7 days.'
            }
        ]
        
        # Insert templates
        for template in templates:
            query = """
            INSERT OR IGNORE INTO templates (
                doctor_id, name, category, description, template_data,
                diagnosis_template, instructions_template
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                template['doctor_id'], template['name'], template['category'],
                template['description'], template['template_data'],
                template['diagnosis_template'], template['instructions_template']
            )
            execute_query(query, params)
        
        st.success("✅ Sample templates inserted successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error inserting sample templates: {str(e)}")
        return False

def check_and_initialize_database():
    """
    Check if database exists and is properly initialized, initialize if needed
    
    Returns:
        bool: True if database is ready, False otherwise
    """
    try:
        if not check_database_exists():
            st.info("Database not found. Initializing new database...")
            return initialize_database()
        else:
            # Check if tables exist
            tables_query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            result = execute_query(tables_query, fetch='one')
            
            if not result or result['count'] < 10:  # Less than expected number of tables
                st.info("Database incomplete. Reinitializing...")
                return initialize_database()
            else:
                st.success("Database found and ready!")
                return True
                
    except Exception as e:
        st.error(f"Error checking database: {str(e)}")
        return False

def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        from database.models import drop_all_tables
        
        st.warning("Resetting database - all data will be lost!")
        
        # Drop all tables
        if not drop_all_tables():
            return False
        
        # Reinitialize
        return initialize_database()
        
    except Exception as e:
        st.error(f"Error resetting database: {str(e)}")
        return False

def get_initialization_status():
    """Get detailed database initialization status"""
    try:
        status = {
            'database_exists': check_database_exists(),
            'tables_created': False,
            'sample_data_loaded': False,
            'total_tables': 0,
            'total_records': 0
        }
        
        if status['database_exists']:
            # Count tables
            tables_query = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            result = execute_query(tables_query, fetch='one')
            status['total_tables'] = result['count'] if result else 0
            status['tables_created'] = status['total_tables'] >= 10
            
            # Count total records across all tables
            if status['tables_created']:
                table_names = ['users', 'patients', 'medications', 'lab_tests', 'patient_visits']
                total_records = 0
                
                for table in table_names:
                    try:
                        count_query = f"SELECT COUNT(*) as count FROM {table}"
                        result = execute_query(count_query, fetch='one')
                        total_records += result['count'] if result else 0
                    except:
                        pass
                
                status['total_records'] = total_records
                status['sample_data_loaded'] = total_records > 0
        
        return status
        
    except Exception as e:
        st.error(f"Error getting initialization status: {str(e)}")
        return {
            'database_exists': False,
            'tables_created': False,
            'sample_data_loaded': False,
            'total_tables': 0,
            'total_records': 0
        }