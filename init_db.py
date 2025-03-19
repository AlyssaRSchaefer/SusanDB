import sqlite3
import random

DB_NAME = "students_local.db"  # Store database inside the Flask instance folder

from faker import Faker
fake = Faker()

def insert_fake_students(n=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for _ in range(n):
        cursor.execute('''
            INSERT INTO students (
                last_name, first_name, student_id, address, city, state, country, zip_code, 
                telephone, email, dob, gender, ethnicity, msn_school, bsn_school, bsn_gpa, 
                msn_gpa, semester_admitted, expected_grad, reason_for_program_withdraw, gpa
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fake.last_name(),
            fake.first_name(),
            fake.uuid4()[:8],  # Generate short unique student ID
            fake.address(),
            fake.city(),
            fake.state_abbr(),
            "USA",
            fake.zipcode(),
            fake.phone_number(),
            fake.email(),
            fake.date_of_birth(minimum_age=18, maximum_age=35).strftime("%Y-%m-%d"),
            random.choice(["Male", "Female", "Non-Binary"]),
            random.choice(["White", "Black", "Asian", "Hispanic", "Other"]),
            fake.company(),  # Random MSN School
            fake.company(),  # Random BSN School
            str(round(random.uniform(2.5, 4.0), 2)),  # Random GPA
            str(round(random.uniform(2.5, 4.0), 2)),  # Random GPA
            f"Fall {random.randint(2018, 2024)}",
            f"Spring {random.randint(2025, 2028)}",
            random.choice(["Personal reasons", "Financial issues", "Academic difficulty", "N/A"]),
            str(round(random.uniform(2.5, 4.0), 2))  # GPA
        ))

    conn.commit()
    conn.close()
    print(f"{n} fake students inserted successfully!")

def create_db():
    conn = sqlite3.connect("students_local.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id TEXT PRIMARY KEY,
            color_scheme TEXT DEFAULT 'default'
        )
    """)

    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT,
            first_name TEXT,
            student_id TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            country TEXT,
            zip_code TEXT,
            telephone TEXT,
            email TEXT,
            dob TEXT,
            gender TEXT,
            ethnicity TEXT,
            msn_school TEXT,
            bsn_school TEXT,
            bsn_gpa TEXT,
            msn_gpa TEXT,
            semester_admitted TEXT,
            expected_grad TEXT,
            reason_for_program_withdraw TEXT,
            gpa TEXT,
            "funding_15/16" TEXT,
            "phd_hrs/grad_hrs" TEXT,
            incompletes TEXT,
            intent_to_enroll TEXT,
            safe_practice_signed TEXT,
            code_of_conduct TEXT,
            phenomenon_of_interest TEXT,
            student_release_signed TEXT,
            hippa TEXT,
            area_of_study TEXT,
            certificate_or_minor TEXT,
            verbal TEXT,
            quant TEXT,
            analyt_writing TEXT,
            analyt TEXT,
            toefl TEXT,
            toefl_test_type TEXT,
            grad_school_app_received TEXT,
            transcripts TEXT,
            son_app_received TEXT,
            gre_date TEXT,
            reference_1 TEXT,
            reference_2 TEXT,
            reference_3 TEXT,
            hep_b TEXT,
            rn_license_exp TEXT,
            mmr TEXT,
            varicella TEXT,
            tb TEXT,
            tdap TEXT,
            cpr_cert_exp TEXT,
            influenza TEXT,
            d1_form TEXT,
            d2_form TEXT,
            d3_form TEXT,
            d4_form TEXT,
            polio TEXT,
            personal_statement TEXT,
            curriculum_vitae TEXT,
            proposal_approval TEXT,
            title_of_dissertation TEXT,
            advisor TEXT,
            chair TEXT,
            reason_for_loa TEXT,
            semester_applied TEXT,
            sp15_hours TEXT,
            last_updated TEXT,
            "7170_or_7020" TEXT, 
            grad_stats TEXT,
            "5697B" TEXT,
            program_status TEXT,
            committee TEXT,
            cit1_training_completed TEXT,
            pos_submitted TEXT,
            "8830" TEXT,
            "9330" TEXT,
            "9410" TEXT,
            "9420" TEXT,
            "9440" TEXT,
            "9450" TEXT,
            "9460" TEXT,
            "9470" TEXT,
            "9540" TEXT,
            "9550" TEXT,
            "9560" TEXT,
            "9710" TEXT,
            "8300" TEXT,
            "7120" TEXT,
            "8425" TEXT,
            "8840" TEXT,
            "8860" TEXT,
            "8002" TEXT,
            "8820" TEXT,
            "7087" TEXT,
            "7001" TEXT,
            "7100" TEXT,
            "7110" TEXT,
            "7150" TEXT,
            "7750" TEXT,
            "7751" TEXT,
            "8001" TEXT,
            "8010" TEXT,
            "8020" TEXT,
            "8030" TEXT,
            "8085" TEXT,
            "8100" TEXT,
            "8720" TEXT,
            "8310" TEXT,
            "8854" TEXT,
            "8864" TEXT,
            "8900" TEXT,
            "8920" TEXT,
            "8940" TEXT,
            "8950" TEXT,
            "8954" TEXT,
            "8964" TEXT,
            "9090" TEXT,
            "9120" TEXT,
            "9131" TEXT,
            "9132" TEXT,
            "9340" TEXT,
            "9100" TEXT,
            sigma_theta TEXT,
            sp19 TEXT,
            advisor_comments TEXT,
            phd_director_comments TEXT,
            ss16 TEXT,
            comps TEXT,
            program_option TEXT,
            background_ck TEXT,
            "ft/pt" TEXT,
            drug_test_completed TEXT,
            ielts TEXT,
            social_media_policy TEXT,
            ielts_date TEXT,
            last_enrolled TEXT,
            immunizations_complete TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    insert_fake_students()