from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import uuid
import sqlite3
import pdfplumber

try:
    import docx
except ImportError:
    docx = None

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}
MATCH_THRESHOLD = 0.7
USERS_DB = os.path.join(os.path.dirname(__file__), 'users.db')

# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Student Form Page
@app.route("/predict")
def predict():
    return render_template("predict.html")


def get_db_connection():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(USERS_DB):
        os.makedirs(os.path.dirname(USERS_DB), exist_ok=True)
        conn = get_db_connection()
        conn.execute(
            '''CREATE TABLE users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password_hash TEXT NOT NULL
               );'''
        )
        conn.commit()
        conn.close()


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view


@app.context_processor
def inject_user():
    return {'current_user': session.get('user')}


# Initialize database
init_db()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('Please complete all fields.', 'error')
            return render_template('register.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email is already registered.', 'error')
            return render_template('register.html')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user'] = user['username']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))

        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


# Courses Page
@app.route("/courses")
@login_required
def courses():
    return render_template("courses.html")


EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email.strip()))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

SKILLS = [
    "python", "java", "c", "c++", "html", "css", "javascript", "sql", "mysql",
    "flask", "django", "react", "nodejs", "machine learning", "deep learning",
    "data analysis", "numpy", "pandas", "git", "github", "api", "rest api",
    "restful api", "bootstrap", "communication", "communication skills", "teamwork",
    "problem solving", "problem-solving", "data structures", "algorithms"
]

SKILLS_LOWER = [skill.lower() for skill in SKILLS]

# Career Market Insights
CAREER_INSIGHTS = {
    "AI Engineer": {
        "salary_min": 90000,
        "salary_max": 180000,
        "currency": "USD/year",
        "growth_rate": 35,
        "demand": "High",
        "demand_color": "green",
        "description": "Artificial Intelligence is rapidly becoming the backbone of modern technology with increasing demand across industries."
    },
    "Full Stack Developer": {
        "salary_min": 75000,
        "salary_max": 150000,
        "currency": "USD/year",
        "growth_rate": 13,
        "demand": "High",
        "demand_color": "green",
        "description": "Full stack developers are highly sought after for their ability to handle both frontend and backend development."
    },
    "Data Scientist": {
        "salary_min": 85000,
        "salary_max": 160000,
        "currency": "USD/year",
        "growth_rate": 36,
        "demand": "Very High",
        "demand_color": "green",
        "description": "Data Science roles are experiencing exceptional growth as companies leverage data for decision-making."
    },
    "Cloud Engineer": {
        "salary_min": 80000,
        "salary_max": 155000,
        "currency": "USD/year",
        "growth_rate": 30,
        "demand": "Very High",
        "demand_color": "green",
        "description": "Cloud computing expertise is critical as more organizations transition to cloud infrastructure."
    },
    "Cyber Security Analyst": {
        "salary_min": 85000,
        "salary_max": 160000,
        "currency": "USD/year",
        "growth_rate": 33,
        "demand": "Very High",
        "demand_color": "green",
        "description": "Cybersecurity roles are in extreme demand due to increasing data breaches and security threats globally."
    },
    "Mobile App Developer": {
        "salary_min": 70000,
        "salary_max": 140000,
        "currency": "USD/year",
        "growth_rate": 13,
        "demand": "High",
        "demand_color": "green",
        "description": "Mobile development remains in high demand with the expansion of iOS and Android applications."
    },
    "UI/UX Designer": {
        "salary_min": 65000,
        "salary_max": 130000,
        "currency": "USD/year",
        "growth_rate": 13,
        "demand": "High",
        "demand_color": "green",
        "description": "UX/UI design is increasingly important as companies focus on user experience and product design."
    },
    "Data Engineer": {
        "salary_min": 85000,
        "salary_max": 165000,
        "currency": "USD/year",
        "growth_rate": 32,
        "demand": "Very High",
        "demand_color": "green",
        "description": "Data engineering roles support the entire data ecosystem and are critical for big data infrastructure."
    },
    "Product Manager": {
        "salary_min": 95000,
        "salary_max": 180000,
        "currency": "USD/year",
        "growth_rate": 10,
        "demand": "High",
        "demand_color": "green",
        "description": "Product managers bridge business and technology, making them highly valuable across all industries."
    },
    "Network Engineer": {
        "salary_min": 75000,
        "salary_max": 145000,
        "currency": "USD/year",
        "growth_rate": 5,
        "demand": "Moderate",
        "demand_color": "yellow",
        "description": "Network engineers maintain critical infrastructure, with steady demand across organizations."
    },
    "QA Engineer": {
        "salary_min": 60000,
        "salary_max": 120000,
        "currency": "USD/year",
        "growth_rate": 8,
        "demand": "Moderate",
        "demand_color": "yellow",
        "description": "QA roles ensure software quality and are essential for delivering reliable products."
    },
    "Embedded Systems Engineer": {
        "salary_min": 75000,
        "salary_max": 145000,
        "currency": "USD/year",
        "growth_rate": 9,
        "demand": "Moderate",
        "demand_color": "yellow",
        "description": "Embedded systems engineering is critical for IoT, automotive, and consumer device development."
    },
    "Software Engineer": {
        "salary_min": 75000,
        "salary_max": 155000,
        "currency": "USD/year",
        "growth_rate": 13,
        "demand": "High",
        "demand_color": "green",
        "description": "Software engineers are essential across all industries, with consistent and strong demand."
    }
}


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        text = ""
    return text


def extract_text_from_docx(doc_path):
    if docx is None:
        return ""
    text = ""
    try:
        document = docx.Document(doc_path)
        text = "\n".join([paragraph.text for paragraph in document.paragraphs if paragraph.text])
    except Exception:
        text = ""
    return text


def extract_resume_fields(text):
    if not text:
        return {}
    return {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'education': extract_section(text, 'education'),
        'skills_section': extract_section(text, 'skills') or extract_section(text, 'technical skills') or extract_section(text, 'technical expertise'),
        'projects': extract_section(text, 'project'),
        'certifications': extract_section(text, 'certification'),
    }


def find_skills(text):
    text = (text or "").lower()
    extracted = set()
    for skill in SKILLS_LOWER:
        if skill in text:
            extracted.add(skill)
    return sorted(extracted)


def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group() if match else ''


def extract_phone(text):
    matches = re.findall(r'(\+?\d[\d\s\-\(\)]{8,}\d)', text)
    for match in matches:
        digits = re.sub(r'\D', '', match)
        if len(digits) >= 10:
            return match.strip()
    return ''


def extract_name(text):
    if not text:
        return ''
    for line in text.splitlines():
        line = line.strip()
        if line and '@' not in line and len(line.split()) <= 5 and len(line) > 2:
            return line
    return ''


def extract_section(text, section_name):
    lines = text.splitlines()
    capture = False
    section_content = []
    for line in lines:
        if section_name.lower() in line.lower():
            capture = True
            continue
        if capture:
            if not line.strip():
                break
            section_content.append(line.strip())
    return ' '.join(section_content)


def generate_ai_suggestions(matched, missing, resume_text):
    suggestions = []
    if missing:
        suggestions.append('Add missing skills: ' + ', '.join(missing))
    if 'github' not in (resume_text or '').lower():
        suggestions.append('Add your GitHub profile link.')
    if 'linkedin' not in (resume_text or '').lower():
        suggestions.append('Add your LinkedIn profile link.')
    if 'project' not in (resume_text or '').lower():
        suggestions.append('Add more industry-relevant projects.')
    if 'experience' not in (resume_text or '').lower():
        suggestions.append('Include an Experience section with roles, responsibilities, and measurable achievements.')
    suggestions.append('Use action verbs like Developed, Built, Designed, Implemented.')
    return suggestions


def explain_score(score, matched, missing, resume_text):
    reasons = []
    if score < 40:
        reasons.append('Low ATS score due to poor skill matching with job description.')
    elif score < 70:
        reasons.append('Moderate ATS score. Some required skills are missing.')
    else:
        reasons.append('Good ATS score. Resume matches most job requirements.')
    if missing:
        reasons.append('Missing important skills: ' + ', '.join(missing))
    if len(matched) < 3:
        reasons.append('Very few matching technical skills found.')
    if 'project' not in (resume_text or '').lower():
        reasons.append('No Projects section detected.')
    if 'experience' not in (resume_text or '').lower():
        reasons.append('No Internship/Experience section found.')
    return reasons


@app.route('/resume', methods=['GET', 'POST'])
def resume():
    score = None
    matched = []
    missing = []
    suggestions = []
    explanation = []
    resume_text = ''
    name = ''
    email = ''
    phone = ''
    education = ''
    skills_section = ''
    projects = ''
    certifications = ''
    job_desc = ''
    match_message = ''
    match_status = 'neutral'

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        job_desc = request.form.get('job_desc', '').strip()
        resume_file = request.files.get('resume')

        if not resume_file or resume_file.filename == '':
            flash('Please upload a resume file to continue.', 'error')
            return redirect(request.url)

        if not allowed_file(resume_file.filename):
            flash('Allowed file types are PDF, DOC, and DOCX.', 'error')
            return redirect(request.url)

        filename = secure_filename(resume_file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        resume_file.save(save_path)

        if filename.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(save_path)
        elif filename.lower().endswith(('.doc', '.docx')):
            resume_text = extract_text_from_docx(save_path)

        if not resume_text:
            resume_text = 'Unable to extract text from uploaded file. Resume analysis will use submitted form fields.'

        extracted_fields = extract_resume_fields(resume_text)
        if not name:
            name = extracted_fields.get('name', '')
        if not email:
            email = extracted_fields.get('email', '')
        if not phone:
            phone = extracted_fields.get('phone', '')
        education = extracted_fields.get('education', '')
        skills_section = extracted_fields.get('skills_section', '')
        projects = extracted_fields.get('projects', '')
        certifications = extracted_fields.get('certifications', '')

        combined_text = ' '.join([resume_text, education, skills_section, projects, certifications]).strip()
        resume_skills = find_skills(combined_text)
        jd_skills = find_skills(job_desc)

        matched = sorted(set(resume_skills) & set(jd_skills))
        missing = sorted(set(jd_skills) - set(resume_skills))

        score = 0
        if jd_skills:
            score += (len(matched) / len(jd_skills)) * 70
        if education.strip():
            score += 10
        if projects.strip():
            score += 10
        if certifications.strip():
            score += 5
        if email and phone:
            score += 5
        score = min(100, round(score))
        score = max(45, score)

        low_match_note = None
        if jd_skills:
            match_ratio = len(matched) / len(jd_skills)
            if match_ratio >= MATCH_THRESHOLD:
                match_message = 'Your resume is a good match for this job description.'
                match_status = 'good'
            else:
                match_message = 'Your resume does not match the job description. Add the missing skills, internships, and company-related experience to improve relevance.'
                match_status = 'poor'
                low_match_note = 'Your resume does not match the selected job description. Add the missing skills and relevant experience.'
        else:
            match_message = 'No identifiable skills were found in the job description.'
            match_status = 'neutral'

        suggestions = generate_ai_suggestions(matched, missing, resume_text)
        if low_match_note:
            suggestions.insert(0, low_match_note)
        explanation = explain_score(score, matched, missing, resume_text)

        report_filename = f"analysis_{uuid.uuid4().hex}.txt"
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], report_filename)
        with open(report_path, 'w', encoding='utf-8') as report_file:
            report_file.write('Resume Analysis Report\n')
            report_file.write(f'Name: {name or "Not provided"}\n')
            report_file.write(f'Score: {score}%\n\n')
            report_file.write('Matched Skills:\n')
            for item in matched:
                report_file.write(f'- {item}\n')
            report_file.write('\nMissing Skills:\n')
            for item in missing:
                report_file.write(f'- {item}\n')
            report_file.write('\nSuggestions:\n')
            for item in suggestions:
                report_file.write(f'- {item}\n')
            report_file.write('\nExplanation:\n')
            for item in explanation:
                report_file.write(f'- {item}\n')

        session['report_file'] = report_filename
        session['last_job_desc'] = job_desc

    return render_template(
        'resume.html',
        score=score,
        matched=matched,
        missing=missing,
        suggestions=suggestions,
        explanation=explanation,
        match_message=match_message,
        match_status=match_status,
        name=name,
        email=email,
        phone=phone,
        education=education,
        skills_section=skills_section,
        projects=projects,
        certifications=certifications,
        job_desc=job_desc,
    )


@app.route('/download')
def download():
    report_file = session.get('report_file')
    if not report_file:
        flash('No report is available for download yet.', 'error')
        return redirect(url_for('resume'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], report_file, as_attachment=True)


# Interview preparation functionality removed per user request


# Result Page
@app.route("/result", methods=["POST"])
def result():

    name = request.form["name"]
    age = request.form.get("age", "0")
    marks = request.form.get("marks", "0")
    # If marks is empty (College/Graduate users), use CGPA as the score
    if not marks:
        cgpa = request.form.get("cgpa", "0")
        marks = cgpa if cgpa else "0"
    education = request.form.get("education", "School")
    degree = request.form.get("degree", "High School")
    branch = request.form.get("branch") or "N/A"
    cgpa = request.form.get("cgpa", "0")
    knowledge = request.form.get("knowledge", "Not specified")
    interest = request.form.get("interest", "General Technology")
    skill = request.form.get("skill", "Learning")
    # Parse comma-separated core skills
    core_skills_input = request.form.get("core_skills", "").strip()
    core_skills = [s.strip() for s in core_skills_input.split(",") if s.strip()] if core_skills_input else []

    try:
        age_value = int(age)
    except (ValueError, TypeError):
        age_value = 0

    education_notice = None
    if age_value < 18 and education in ["College", "Graduate"]:
        education_notice = (
            "Your age indicates a school-level profile, so this recommendation uses School guidance."
        )
        education = "School"
        degree = "High School"
        branch = "N/A"

    if education == "School":
        degree = "High School"
        branch = "N/A"

    # Career Prediction Logic - Enhanced with Branch & Skill Matching
    def get_career_recommendation(interest, branch, skill):
        """
        Recommends career based on interest, branch, and skill alignment.
        Prioritizes:
        1. Interest match
        2. Branch specialization
        3. Skill alignment
        """
        career_map = {
            "Artificial Intelligence": "AI Engineer",
            "Web Development": "Full Stack Developer",
            "Cyber Security": "Cyber Security Analyst",
            "Networking": "Network Engineer",
            "Data Science": "Data Scientist",
            "Cloud Computing": "Cloud Engineer",
            "Mobile App Development": "Mobile App Developer",
            "UI/UX Design": "UI/UX Designer",
            "Data Engineering": "Data Engineer",
            "Product Management": "Product Manager",
            "DevOps Engineering": "Cloud Engineer",
            "Blockchain": "Software Engineer",
            "Game Development": "Software Engineer",
            "IoT (Internet of Things)": "Embedded Systems Engineer",
            "Embedded Systems": "Embedded Systems Engineer",
            "Quality Assurance / Testing": "QA Engineer",
            "Systems Administration": "Network Engineer",
            "Business Analytics": "Data Scientist",
        }
        
        # Base career from interest
        career = career_map.get(interest, "Software Engineer")
        
        # Branch-specific refinements
        if branch != "N/A":
            # Business Administration strongly suggests Product Manager
            if branch == "Business Administration" and interest != "Artificial Intelligence":
                if interest in ["Product Management", "Data Science", "Web Development", "Business Analytics"]:
                    career = "Product Manager"
            
            # Design branch suggests UI/UX Designer
            if branch == "Design":
                if interest in ["UI/UX Design", "Web Development", "Mobile App Development", "Game Development"]:
                    career = "UI/UX Designer"
            
            # Data Science branch suggests Data roles
            if branch == "Data Science":
                if interest in ["Data Science", "Data Engineering", "Artificial Intelligence", "Business Analytics"]:
                    if interest == "Data Engineering":
                        career = "Data Engineer"
                    elif interest == "Artificial Intelligence":
                        career = "AI Engineer"
                    else:
                        career = "Data Scientist"
            
            # ECE/Electronics/Electrical branches suggest hardware-aware careers
            if branch in ["ECE", "Electronics", "Electrical", "Mechanical"]:
                if interest in ["Networking", "Cloud Computing", "Artificial Intelligence", "IoT (Internet of Things)", "Embedded Systems"]:
                    career = career  # Keep the interest-based career
                elif interest == "Web Development":
                    career = "Cloud Engineer"
        
        # Skill-based refinements
        if skill in ["AWS", "Azure", "GCP"] and interest not in ["UI/UX Design"]:
            career = "Cloud Engineer"
        elif skill in ["Docker", "Kubernetes", "Terraform", "Jenkins"]:
            career = "Cloud Engineer"
        elif skill == "Figma" and interest != "Artificial Intelligence":
            career = "UI/UX Designer"
        elif skill == "Machine Learning":
            if interest != "Web Development":
                career = "AI Engineer"
            else:
                career = "Data Scientist"
        elif skill in ["Solidity", "Blockchain"] or (interest == "Blockchain" and skill in ["Rust", "Go", "Python"]):
            career = "Software Engineer"
        elif skill in ["SQL", "MongoDB", "Firebase"]:
            if interest in ["Data Science", "Data Engineering", "Artificial Intelligence", "Business Analytics"]:
                career = career
            else:
                career = "Data Scientist"
        elif skill in ["React", "Vue.js", "Angular", "JavaScript", "HTML CSS", "TypeScript", "Node.js"] and interest != "UI/UX Design":
            career = "Full Stack Developer"
        elif skill == "Unity" or interest == "Game Development":
            career = "Software Engineer"
        elif skill in ["Linux", "Git"] or interest == "Systems Administration":
            if interest == "DevOps Engineering" or skill in ["Docker", "Kubernetes"]:
                career = "Cloud Engineer"
            else:
                career = "Network Engineer"
        elif skill == "Selenium" or interest == "Quality Assurance / Testing":
            career = "QA Engineer"
        
        return career
    
    career = get_career_recommendation(interest, branch, skill)

    # If the user is still in school, provide a more guided recommendation
    if education == "School":
        recommended_action = (
            "You are in the school stage, so focus on foundational learning, "
            "exploratory projects, and building strong math and logic skills. "
            "Consider early coding practice and career exploration programs."
        )
        if marks and float(marks) >= 80:
            career_note = "Your strong performance is a good signal for future technical roles."
        else:
            career_note = "Use this stage to improve your fundamentals and keep exploring fields you enjoy."
    else:
        branch_text = branch if branch != "N/A" else "your field"
        recommended_action = (
            f"As a {degree} student in {branch_text}, you should focus on practical projects, "
            "industry-focused training, and expert certifications in your chosen field."
        )
        if knowledge == "Beginner":
            career_note = "Begin with core concepts and practical exercises, then build towards your chosen specialization."
        elif knowledge == "Intermediate":
            career_note = "You are ready for more advanced projects and should deepen your domain expertise."
        else:
            career_note = "Use your advanced knowledge to refine your specialization and lead higher-impact work."

        if branch != "N/A":
            if branch == "Business Administration" and career == "Product Manager":
                career_note = "Your business major gives you an edge in product strategy, analytics, and stakeholder leadership."
            elif branch == "Design" and career == "UI/UX Designer":
                career_note = "Your design background aligns well with user experience, visual communication, and product research."
            elif branch in ["Computer Science", "Information Technology", "Data Science"]:
                career_note = career_note + " Your technical major supports strong specialization in this field."
            elif branch in ["Electronics", "ECE", "Electrical", "Mechanical"] and career in ["AI Engineer", "Cloud Engineer", "Network Engineer"]:
                career_note = "Your engineering branch gives you valuable systems knowledge for infrastructure and hardware-aware solutions."

    career_detail = "This recommendation is based on your selected interest and strongest skill."
    if career == "AI Engineer":
        career_detail = "AI Engineers use machine learning, data modeling, and Python to build intelligent systems."
    elif career == "Full Stack Developer":
        career_detail = "Full Stack Developers build web applications using both frontend and backend technologies."
    elif career == "Cyber Security Analyst":
        career_detail = "Cyber Security Analysts protect systems, investigate risks, and support security operations."
    elif career == "Network Engineer":
        career_detail = "Network Engineers design and maintain reliable corporate networks and infrastructure."
    elif career == "Data Scientist":
        career_detail = "Data Scientists analyze data, build predictive models, and deliver actionable business insights."
    elif career == "Cloud Engineer":
        career_detail = "Cloud Engineers build, deploy, and manage applications using cloud platforms like AWS, Azure, or GCP."
    elif career == "Mobile App Developer":
        career_detail = "Mobile App Developers create engaging mobile experiences for Android and iOS."
    elif career == "UI/UX Designer":
        career_detail = "UI/UX Designers create intuitive product experiences with strong visual and interaction design."
    elif career == "Data Engineer":
        career_detail = "Data Engineers build data pipelines and keep data flowing cleanly across systems."
    elif career == "Product Manager":
        career_detail = "Product Managers lead product strategy, work with stakeholders, and guide development teams."
    elif career == "QA Engineer":
        career_detail = "QA Engineers ensure software quality through systematic testing, automation, and quality assurance processes."
    elif career == "Embedded Systems Engineer":
        career_detail = "Embedded Systems Engineers develop software and hardware for IoT devices, microcontrollers, and specialized systems."
    elif career == "Software Engineer":
        career_detail = "Software Engineers design, develop, and maintain software systems and applications across various domains."

    recommended_courses = [
        "Python Programming",
        "Machine Learning",
        "Data Structures & Algorithms",
        "SQL & Database Management",
    ]

    if knowledge == "Beginner":
        recommended_courses = [
            "Introduction to Programming",
            "Foundations of Computer Science",
            "Problem Solving with Python",
            "Basic Web Development",
        ]
    elif knowledge == "Intermediate" and education != "School":
        recommended_courses = [
            "Applied Programming Projects",
            "Data Structures & Algorithms",
            "System Design Fundamentals",
            "Core Domain Training",
        ]
    elif knowledge == "Advanced" and education != "School":
        recommended_courses = [
            "Specialized Technology Topics",
            "Advanced Project Architecture",
            "Industry Best Practices",
            "Professional Development in Your Field",
        ]

    if education == "Graduate":
        if career == "AI Engineer":
            recommended_courses = [
                "Advanced Machine Learning",
                "Deep Learning Fundamentals",
                "Natural Language Processing",
                "MLOps Essentials",
            ]
            if degree in ["M.Tech", "M.Sc", "MS"]:
                recommended_courses.insert(0, "Research Methods in AI")
        elif career == "Full Stack Developer":
            recommended_courses = [
                "Advanced Web Architecture",
                "Microservices with React",
                "Cloud & DevOps for Engineers",
                "Backend API Design",
            ]
            if degree == "MCA":
                recommended_courses.insert(0, "Advanced Software Engineering")
        elif career == "Cyber Security Analyst":
            recommended_courses = [
                "Advanced Cyber Security",
                "Penetration Testing",
                "Cloud Security Practices",
                "Incident Response Strategy",
            ]
            if degree in ["M.Tech", "MCA"]:
                recommended_courses.insert(0, "Secure Systems Architecture")
        elif career == "Network Engineer":
            recommended_courses = [
                "Advanced Network Design",
                "Cloud Networking",
                "Network Automation",
                "Security Architecture",
            ]
        elif career == "Data Scientist":
            recommended_courses = [
                "Advanced Data Science",
                "Deep Learning Fundamentals",
                "MLOps for Data Science",
                "Big Data Analytics",
            ]
            if degree in ["M.Sc", "MS"]:
                recommended_courses.insert(0, "Statistical Learning Theory")
        elif career == "Cloud Engineer":
            recommended_courses = [
                "Cloud Architecture",
                "Kubernetes & Containers",
                "Infrastructure as Code",
                "Cloud Security",
            ]
        elif career == "Mobile App Developer":
            recommended_courses = [
                "Advanced Mobile App Development",
                "Cross-platform App Design",
                "App Performance Optimization",
                "Mobile UX and Interaction",
            ]
            if degree in ["MCA", "M.Tech"]:
                recommended_courses.insert(0, "Mobile Systems Engineering")
        elif career == "UI/UX Designer":
            recommended_courses = [
                "Design Systems",
                "Service Design",
                "Advanced UI/UX Strategy",
                "User Research Methods",
            ]
        elif career == "Data Engineer":
            recommended_courses = [
                "Advanced Data Engineering",
                "Big Data Systems",
                "Streaming Data Pipelines",
                "Cloud Data Architecture",
            ]
        elif career == "Product Manager":
            recommended_courses = [
                "Product Strategy and Leadership",
                "Analytics for Product Managers",
                "Design Thinking",
                "Stakeholder Management",
            ]
            if degree == "MBA":
                recommended_courses.insert(0, "Strategic Business Leadership")
    else:
        if career == "Full Stack Developer":
            recommended_courses = [
                "Web Development Bootcamp",
                "JavaScript Essentials",
                "React Fundamentals",
                "SQL & Database Management",
            ]
        elif career == "Cyber Security Analyst":
            recommended_courses = [
                "Cyber Security Fundamentals",
                "Network Security",
                "Ethical Hacking Basics",
                "SQL & Database Management",
            ]
        elif career == "Network Engineer":
            recommended_courses = [
                "Networking Basics",
                "Cloud Computing Basics",
                "Linux Fundamentals",
                "Cyber Security Fundamentals",
            ]
        elif career == "Data Scientist":
            recommended_courses = [
                "Python Programming",
                "Data Science Foundations",
                "Machine Learning",
                "SQL & Database Management",
            ]
            if branch == "Data Science":
                recommended_courses = [
                    "Advanced Data Science",
                    "Big Data Analytics",
                    "Data Visualization",
                    "Machine Learning",
                ]
        elif career == "Cloud Engineer":
            recommended_courses = [
                "Cloud Computing Basics",
                "AWS Fundamentals",
                "DevOps Concepts",
                "Data Engineering Basics",
            ]
        elif career == "Mobile App Developer":
            recommended_courses = [
                "Mobile App Development",
                "JavaScript Essentials",
                "React Fundamentals",
                "UI/UX Basics",
            ]
        elif career == "UI/UX Designer":
            recommended_courses = [
                "UI/UX Design",
                "Figma Essentials",
                "Product Design Fundamentals",
                "Web Design Basics",
            ]
        elif career == "Data Engineer":
            recommended_courses = [
                "Data Engineering Basics",
                "SQL & Database Management",
                "Cloud Computing Basics",
                "Data Structures & Algorithms",
            ]
        elif career == "Product Manager":
            recommended_courses = [
                "Product Management Fundamentals",
                "UI/UX Design",
                "Business Communication",
                "Data-driven Decision Making",
            ]
            if branch == "Business Administration":
                recommended_courses = [
                    "Product Strategy",
                    "Business Analytics",
                    "Stakeholder Management",
                    "Design Thinking",
                ]

    if branch != "N/A":
        if career == "AI Engineer":
            if branch in ["Computer Science", "Information Technology", "Data Science"]:
                recommended_courses = [
                    "Machine Learning",
                    "Deep Learning",
                    "AI Systems Engineering",
                    "Data Modeling with Python",
                ]
            elif branch in ["Electronics", "Electrical", "ECE"]:
                recommended_courses = [
                    "Embedded AI Systems",
                    "Signal Processing for AI",
                    "Machine Learning",
                    "Hardware-aware AI Design",
                ]
            else:
                recommended_courses = [
                    "Machine Learning",
                    "Deep Learning",
                    "Natural Language Processing",
                    "AI Systems Architecture",
                ]
        elif career == "Full Stack Developer":
            if branch in ["Computer Science", "Information Technology", "Data Science"]:
                recommended_courses = [
                    "Modern Web Development",
                    "JavaScript Frameworks",
                    "API Design",
                    "Cloud-Enabled Full Stack Projects",
                ]
            elif branch == "Design":
                recommended_courses = [
                    "User Interface Development",
                    "Responsive Web Design",
                    "Front-end Architecture",
                    "Full Stack Project Workflows",
                ]
            else:
                recommended_courses = [
                    "Web Development Bootcamp",
                    "JavaScript Essentials",
                    "React Fundamentals",
                    "Backend API Design",
                ]
        elif career == "Cyber Security Analyst":
            if branch in ["Computer Science", "Information Technology", "Electronics", "ECE"]:
                recommended_courses = [
                    "Cyber Security Fundamentals",
                    "Network Defense",
                    "Ethical Hacking",
                    "Secure Systems Development",
                ]
            else:
                recommended_courses = [
                    "Cyber Security Fundamentals",
                    "Information Security",
                    "Risk Management",
                    "Security Operations",
                ]
        elif career == "Network Engineer":
            if branch in ["Electrical", "Electronics", "ECE", "Computer Science"]:
                recommended_courses = [
                    "Network Design",
                    "Wireless Systems",
                    "Network Automation",
                    "Cloud Networking",
                ]
            else:
                recommended_courses = [
                    "Networking Basics",
                    "Cloud Computing Basics",
                    "Linux Fundamentals",
                    "Network Security",
                ]
        elif career == "Data Scientist":
            if branch == "Data Science":
                recommended_courses = [
                    "Advanced Data Science",
                    "Big Data Analytics",
                    "Data Visualization",
                    "Machine Learning",
                ]
            elif branch in ["Computer Science", "Information Technology"]:
                recommended_courses = [
                    "Data Science Foundations",
                    "Machine Learning",
                    "SQL & Database Management",
                    "Python for Data Analysis",
                ]
            else:
                recommended_courses = [
                    "Data Science Foundations",
                    "Statistics for Data Science",
                    "Machine Learning",
                    "Data Storytelling",
                ]
        elif career == "Cloud Engineer":
            if branch in ["Computer Science", "Information Technology", "Electrical", "Electronics", "ECE"]:
                recommended_courses = [
                    "Cloud Architecture",
                    "Infrastructure as Code",
                    "Kubernetes and Containers",
                    "Cloud Security",
                ]
            else:
                recommended_courses = [
                    "Cloud Computing Basics",
                    "AWS Fundamentals",
                    "DevOps Concepts",
                    "Infrastructure Management",
                ]
        elif career == "Mobile App Developer":
            if branch in ["Computer Science", "Information Technology"]:
                recommended_courses = [
                    "Mobile App Development",
                    "Cross-Platform App Design",
                    "App Performance Optimization",
                    "Mobile UX Design",
                ]
            elif branch == "Design":
                recommended_courses = [
                    "Mobile UX Design",
                    "Interaction Design",
                    "Product Design Fundamentals",
                    "Mobile Prototyping",
                ]
            else:
                recommended_courses = [
                    "Mobile App Development",
                    "JavaScript Essentials",
                    "React Fundamentals",
                    "UI/UX Basics",
                ]
        elif career == "UI/UX Designer":
            if branch == "Design":
                recommended_courses = [
                    "UX Research",
                    "Interaction Design",
                    "Design Systems",
                    "Portfolio Development",
                ]
            else:
                recommended_courses = [
                    "UI/UX Design",
                    "Figma Essentials",
                    "Product Design Fundamentals",
                    "Web Design Basics",
                ]
        elif career == "Data Engineer":
            if branch in ["Data Science", "Computer Science", "Information Technology"]:
                recommended_courses = [
                    "Data Pipelines",
                    "Big Data Systems",
                    "ETL Architecture",
                    "Cloud Data Engineering",
                ]
            else:
                recommended_courses = [
                    "Data Engineering Basics",
                    "SQL & Database Management",
                    "Cloud Computing Basics",
                    "Data Structures & Algorithms",
                ]
        elif career == "Product Manager":
            if branch == "Business Administration":
                recommended_courses = [
                    "Product Strategy",
                    "Business Analytics",
                    "Stakeholder Management",
                    "Design Thinking",
                ]
            elif branch == "Design":
                recommended_courses = [
                    "Product Strategy",
                    "Design Thinking",
                    "UX Research",
                    "Innovation and Ideation",
                ]
            else:
                recommended_courses = [
                    "Product Management Fundamentals",
                    "Business Communication",
                    "Data-driven Decision Making",
                    "Stakeholder Engagement",
                ]
        elif career == "Software Engineer":
            if branch in ["Computer Science", "Information Technology"]:
                recommended_courses = [
                    "Software Engineering Fundamentals",
                    "Data Structures & Algorithms",
                    "System Design Basics",
                    "Modern Programming Practices",
                ]
            else:
                recommended_courses = [
                    "Programming Foundations",
                    "Data Structures & Algorithms",
                    "Problem Solving",
                    "Software Development Practices",
                ]

    # Build a confidence score from marks and interest-skill alignment
    try:
        marks_value = float(marks)
    except ValueError:
        marks_value = 0.0

    base_confidence = 55 + marks_value * 0.25

    interest_skill_bonus = 0
    if interest == "Artificial Intelligence" and skill in ["Python", "C++", "SQL", "Machine Learning"]:
        interest_skill_bonus = 5
    elif interest == "Web Development" and skill in ["HTML CSS", "JavaScript", "React", "Python", "Java"]:
        interest_skill_bonus = 5
    elif interest == "Cyber Security" and skill in ["Python", "C++", "SQL"]:
        interest_skill_bonus = 5
    elif interest == "Networking" and skill in ["Python", "SQL"]:
        interest_skill_bonus = 5
    elif interest == "Data Science" and skill in ["Python", "SQL", "Machine Learning"]:
        interest_skill_bonus = 5
    elif interest == "Cloud Computing" and skill in ["AWS", "Python", "SQL"]:
        interest_skill_bonus = 5
    elif interest == "Mobile App Development" and skill in ["JavaScript", "React", "Java", "Python"]:
        interest_skill_bonus = 5
    elif interest == "UI/UX Design" and skill in ["Figma", "HTML CSS"]:
        interest_skill_bonus = 5
    elif interest == "Data Engineering" and skill in ["Python", "SQL"]:
        interest_skill_bonus = 5
    elif interest == "Product Management" and skill in ["Figma", "JavaScript"]:
        interest_skill_bonus = 5

    education_bonus = 0
    if education == "School":
        education_bonus = -3
    elif education == "Graduate":
        education_bonus = 3

    confidence = base_confidence + interest_skill_bonus + education_bonus
    confidence = min(98, max(60, round(confidence)))

    # Get career insights
    career_insight = CAREER_INSIGHTS.get(career, {
        "salary_min": 70000,
        "salary_max": 140000,
        "currency": "USD/year",
        "growth_rate": 10,
        "demand": "Moderate",
        "demand_color": "yellow",
        "description": "This career field offers competitive opportunities in the job market."
    })

    # Generate reasoning for career recommendation
    career_reasoning = []
    if interest:
        career_reasoning.append(f"✓ Your interest in '{interest}' aligns well with {career} roles")
    if skill and skill != "Learning":
        career_reasoning.append(f"✓ Your '{skill}' skill is highly valued in {career} positions")
    if branch != "N/A" and branch != "N/A":
        career_reasoning.append(f"✓ Your {branch} background provides strong foundation for {career}")
    if marks and float(marks) >= 80:
        career_reasoning.append(f"✓ Your academic performance ({marks}%) demonstrates capability for advanced roles")
    if knowledge:
        career_reasoning.append(f"✓ Your {knowledge} knowledge level suits the entry requirements for {career}")
    
    if not career_reasoning:
        career_reasoning = [f"✓ Your overall profile matches {career} career requirements", 
                          "✓ Recommended based on skill, interest, and education alignment"]

    # Generate reasoning for course recommendations
    course_reasoning_dict = {}
    
    # Default reasoning based on career
    if career == "AI Engineer":
        course_reasoning_dict = {
            "Machine Learning" if "Machine Learning" in recommended_courses else recommended_courses[0]: 
                "Core skill for AI development and model building",
            "Data Structures & Algorithms" if "Data Structures & Algorithms" in recommended_courses else (recommended_courses[1] if len(recommended_courses) > 1 else ""): 
                "Essential for optimizing AI algorithms",
            "Python Programming" if "Python Programming" in recommended_courses else (recommended_courses[2] if len(recommended_courses) > 2 else ""): 
                "Primary language for AI/ML development"
        }
    elif career == "Full Stack Developer":
        course_reasoning_dict = {
            "React Fundamentals" if any("React" in c for c in recommended_courses) else recommended_courses[0]: 
                "Modern frontend framework for building scalable UIs",
            "Backend API Design" if any("API" in c or "Backend" in c for c in recommended_courses) else (recommended_courses[1] if len(recommended_courses) > 1 else ""): 
                "Critical for building robust server-side applications",
            "SQL & Database Management" if any("SQL" in c or "Database" in c for c in recommended_courses) else (recommended_courses[2] if len(recommended_courses) > 2 else ""): 
                "Essential for data management and retrieval"
        }
    elif career == "Data Scientist":
        course_reasoning_dict = {
            "Deep Learning Fundamentals" if any("Deep" in c for c in recommended_courses) else recommended_courses[0]: 
                "Advanced techniques for complex data analysis",
            "Data Structures & Algorithms" if any("Data" in c and "Structures" in c for c in recommended_courses) else (recommended_courses[1] if len(recommended_courses) > 1 else ""): 
                "Optimize data processing efficiency",
            "Python Programming" if any("Python" in c for c in recommended_courses) else (recommended_courses[2] if len(recommended_courses) > 2 else ""): 
                "Most popular language for data science"
        }
    else:
        # Generic reasoning for other careers
        for i, course in enumerate(recommended_courses[:3]):
            if i == 0:
                course_reasoning_dict[course] = f"Foundational knowledge for {career} roles"
            elif i == 1:
                course_reasoning_dict[course] = f"Practical skills needed for {career} specialization"
            else:
                course_reasoning_dict[course] = f"Advanced competency for {career} excellence"

    return render_template(
        "result.html",
        name=name,
        age=age,
        marks=marks,
        education=education,
        degree=degree,
        branch=branch,
        cgpa=cgpa,
        knowledge=knowledge,
        interest=interest,
        skill=skill,
        core_skills=core_skills,
        career=career,
        confidence=confidence,
        recommended_action=recommended_action,
        career_note=career_note,
        career_detail=career_detail,
        recommended_courses=recommended_courses,
        education_notice=education_notice,
        career_insight=career_insight,
        career_reasoning=career_reasoning,
        course_reasoning_dict=course_reasoning_dict
    )


# Career-specific learning roadmaps
CAREER_ROADMAPS = {
    "AI Engineer": [
        "Learn Python Programming",
        "Master Data Structures & Algorithms",
        "Learn SQL & Database Management",
        "Study Machine Learning Basics",
        "Build Real-World AI Projects",
        "Learn Deep Learning & Neural Networks",
        "Study Natural Language Processing",
        "Complete an AI Internship",
        "Become an AI Engineer 🚀",
    ],
    "Full Stack Developer": [
        "Learn HTML, CSS & JavaScript",
        "Master Frontend Frameworks (React)",
        "Learn Backend Programming (Node.js/Python)",
        "Study SQL & Database Management",
        "Learn API Design & REST",
        "Master Version Control (Git)",
        "Build Full Stack Projects",
        "Complete a Development Internship",
        "Become a Full Stack Developer 🚀",
    ],
    "Cyber Security Analyst": [
        "Learn Networking Fundamentals",
        "Master Linux & System Administration",
        "Study Ethical Hacking Basics",
        "Learn Cryptography & Encryption",
        "Study Network Security Protocols",
        "Build Security Projects & Labs",
        "Pursue Security Certifications (CEH)",
        "Complete a Cyber Security Internship",
        "Become a Cyber Security Analyst 🚀",
    ],
    "Data Scientist": [
        "Learn Python Programming",
        "Master Statistics & Probability",
        "Study SQL & Database Management",
        "Learn Data Analysis & Visualization",
        "Master Machine Learning Algorithms",
        "Build Real-World Data Science Projects",
        "Learn Big Data & Analytics",
        "Complete a Data Science Internship",
        "Become a Data Scientist 🚀",
    ],
    "Cloud Engineer": [
        "Learn Linux & Networking Basics",
        "Study Cloud Platforms (AWS/Azure/GCP)",
        "Master Infrastructure as Code (Terraform)",
        "Learn Docker & Kubernetes",
        "Study Cloud Security & Compliance",
        "Build Cloud Infrastructure Projects",
        "Master DevOps Practices",
        "Complete a Cloud Engineering Internship",
        "Become a Cloud Engineer 🚀",
    ],
    "Mobile App Developer": [
        "Learn JavaScript or Swift",
        "Master Mobile UI/UX Design",
        "Study React Native or Native Development",
        "Learn State Management & APIs",
        "Build Mobile App Projects",
        "Master App Performance Optimization",
        "Learn Mobile App Testing",
        "Complete a Mobile Development Internship",
        "Become a Mobile App Developer 🚀",
    ],
    "UI/UX Designer": [
        "Learn Design Principles & Color Theory",
        "Master Figma & Design Tools",
        "Study User Research & Personas",
        "Learn Wireframing & Prototyping",
        "Build Design Portfolio Projects",
        "Study Interaction Design & Animations",
        "Learn Design Systems & Accessibility",
        "Complete a UX/UI Design Internship",
        "Become a UI/UX Designer 🚀",
    ],
    "Network Engineer": [
        "Learn Networking Fundamentals (OSI Model)",
        "Master TCP/IP & Routing Protocols",
        "Study Network Configuration & Switches",
        "Learn Network Security Basics",
        "Study Cloud Networking Solutions",
        "Build Network Architecture Projects",
        "Learn Network Monitoring & Troubleshooting",
        "Complete a Networking Internship",
        "Become a Network Engineer 🚀",
    ],
    "Data Engineer": [
        "Learn Python & SQL Programming",
        "Master Data Structures & Algorithms",
        "Study SQL & Database Design",
        "Learn ETL & Data Pipelines",
        "Master Big Data Technologies (Hadoop/Spark)",
        "Learn Cloud Data Services (AWS Glue)",
        "Build Data Engineering Projects",
        "Complete a Data Engineering Internship",
        "Become a Data Engineer 🚀",
    ],
    "Product Manager": [
        "Learn Business Fundamentals",
        "Master Product Management Concepts",
        "Study User Research & Analytics",
        "Learn Data-Driven Decision Making",
        "Master Product Strategy & Roadmapping",
        "Study Design Thinking & Innovation",
        "Build Product Management Case Studies",
        "Complete a Product Management Internship",
        "Become a Product Manager 🚀",
    ],
    "QA Engineer": [
        "Learn Software Testing Fundamentals",
        "Master Manual & Automated Testing",
        "Study Test Automation Tools (Selenium)",
        "Learn Python/Java for Test Automation",
        "Study API & Database Testing",
        "Build Test Automation Projects",
        "Learn CI/CD & Test Integration",
        "Complete a QA Engineering Internship",
        "Become a QA Engineer 🚀",
    ],
    "Embedded Systems Engineer": [
        "Learn C/C++ Programming",
        "Study Microcontroller Fundamentals",
        "Learn Embedded Linux",
        "Study IoT Protocols & Communication",
        "Learn Hardware Integration",
        "Build Embedded Projects & Prototypes",
        "Study Real-Time Operating Systems",
        "Complete an Embedded Systems Internship",
        "Become an Embedded Systems Engineer 🚀",
    ],
    "Software Engineer": [
        "Learn Core Programming Concepts",
        "Master Data Structures & Algorithms",
        "Study Software Design Patterns",
        "Learn System Design & Architecture",
        "Master Version Control (Git)",
        "Build Full-Scale Software Projects",
        "Study Testing & Debugging Practices",
        "Complete a Software Engineering Internship",
        "Become a Software Engineer 🚀",
    ],
}


# Interview Preparation Database
INTERVIEW_QUESTIONS = {
    "AI Engineer": {
        "technical": [
            "Explain the difference between supervised and unsupervised learning with real-world examples.",
            "What is the curse of dimensionality? How do you handle it?",
            "Describe the process of training a neural network. What are backpropagation and gradient descent?",
            "How would you approach building an end-to-end machine learning pipeline?",
            "Explain cross-validation and why it's important in model evaluation.",
            "What is overfitting? How do you detect and prevent it?",
            "Tell me about activation functions and why we use them.",
            "How would you optimize a slow machine learning model in production?"
        ],
        "behavioral": [
            "Describe a challenging ML project you worked on and how you solved it.",
            "How do you stay updated with the latest AI/ML advancements?",
            "Tell me about a time you had to explain complex ML concepts to non-technical stakeholders.",
            "How do you approach debugging a model that's underperforming?",
            "Describe your experience with deployment and monitoring of ML models.",
            "What's your approach to handling imbalanced datasets?"
        ],
        "tips": [
            "🎯 Prepare real project examples with metrics and results",
            "📊 Master statistics and probability concepts thoroughly",
            "💻 Practice coding on platforms like LeetCode with ML focus",
            "🧠 Know popular architectures: CNNs, RNNs, Transformers",
            "⚡ Understand computational complexity and optimization",
            "📈 Be ready to discuss your GitHub projects in detail",
            "🔬 Study recent papers in your area of interest",
            "🎤 Practice explaining technical concepts simply"
        ]
    },
    "Full Stack Developer": {
        "technical": [
            "Explain the difference between SQL and NoSQL databases. When would you use each?",
            "How does the DOM work? Explain event delegation and bubbling.",
            "What is REST API? Design a simple REST API for a social media application.",
            "Explain CORS and how to handle CORS errors.",
            "What are async/await and Promises? How do they help with asynchronous code?",
            "How would you optimize a slow database query?",
            "Explain session management and JWT authentication.",
            "What's the difference between GET and POST requests?"
        ],
        "behavioral": [
            "Describe a full stack project where you handled both frontend and backend.",
            "How do you approach debugging issues in a full stack application?",
            "Tell me about a time you optimized application performance.",
            "How do you handle version control in team projects?",
            "Describe your experience with deploying applications.",
            "How do you approach learning new frameworks and technologies?"
        ],
        "tips": [
            "🎯 Build real full-stack projects and host them on GitHub",
            "🔗 Master both frontend and backend technologies deeply",
            "🗄️ Practice SQL and database design thoroughly",
            "🚀 Understand deployment pipelines and CI/CD",
            "🔐 Know security best practices (CORS, HTTPS, input validation)",
            "⚡ Optimize for performance: caching, lazy loading, etc.",
            "🧪 Write clean, testable code with proper error handling",
            "📱 Design responsive, accessible UIs"
        ]
    },
    "Data Scientist": {
        "technical": [
            "Walk me through your process for building a predictive model from scratch.",
            "How do you handle missing data? What techniques would you use?",
            "Explain different evaluation metrics (precision, recall, F1, AUC) and when to use each.",
            "What is the bias-variance tradeoff?",
            "How do you feature engineer for a machine learning model?",
            "Describe hyperparameter tuning methods.",
            "Explain different types of regression and classification algorithms.",
            "How would you approach an A/B testing scenario?"
        ],
        "behavioral": [
            "Describe a data science project where you provided business value.",
            "How do you communicate findings to non-technical stakeholders?",
            "Tell me about a time you had to work with messy, incomplete data.",
            "How do you validate if your model is actually solving the business problem?",
            "Describe your experience with big data tools and technologies.",
            "How do you stay current with data science trends?"
        ],
        "tips": [
            "📊 Build a strong portfolio with diverse projects on GitHub",
            "🎯 Focus on business impact, not just accuracy",
            "📈 Master visualization libraries: Matplotlib, Seaborn, Plotly",
            "🧮 Know statistics deeply: distributions, hypothesis testing, etc.",
            "💾 Understand big data tools: Spark, Hadoop, etc.",
            "🔍 Practice EDA (Exploratory Data Analysis) rigorously",
            "📝 Write clear documentation and insights reports",
            "🎤 Practice presenting findings to business stakeholders"
        ]
    },
    "Cloud Engineer": {
        "technical": [
            "Explain the differences between AWS, Azure, and GCP services.",
            "What is Infrastructure as Code? How would you implement it with Terraform?",
            "Describe containerization with Docker and orchestration with Kubernetes.",
            "How do you ensure high availability and disaster recovery in cloud architecture?",
            "Explain different cloud deployment models: IaaS, PaaS, SaaS.",
            "What is auto-scaling? How would you configure it?",
            "How do you approach cloud security and compliance?",
            "Describe your approach to monitoring and logging in the cloud."
        ],
        "behavioral": [
            "Tell me about a complex cloud migration project you worked on.",
            "How do you handle cost optimization in cloud environments?",
            "Describe a time you resolved a production issue in the cloud.",
            "How do you stay updated with cloud platform changes?",
            "Tell me about your experience with CI/CD pipelines.",
            "How do you approach learning new cloud services?"
        ],
        "tips": [
            "☁️ Get certified: AWS, Azure, or GCP certifications are valuable",
            "🏗️ Master Infrastructure as Code (Terraform, CloudFormation)",
            "🐳 Understand Docker and Kubernetes deeply",
            "💰 Learn cost optimization and resource management",
            "🔐 Know cloud security best practices and compliance",
            "📊 Practice designing scalable, highly available architectures",
            "🔄 Understand CI/CD and DevOps practices",
            "🧪 Build and deploy projects on actual cloud platforms"
        ]
    },
    "Cyber Security Analyst": {
        "technical": [
            "Explain the OSI model and security at each layer.",
            "What is encryption? Describe symmetric vs asymmetric encryption.",
            "Explain common vulnerability types: SQL injection, XSS, CSRF.",
            "How would you conduct a security audit of a web application?",
            "What is a firewall? What are different types?",
            "Describe common attack vectors: phishing, malware, DDoS.",
            "What is penetration testing? How would you approach it?",
            "Explain authentication and authorization mechanisms."
        ],
        "behavioral": [
            "Tell me about a security incident you've responded to.",
            "How do you stay updated with the latest security threats?",
            "Describe your experience with security compliance (HIPAA, GDPR, PCI-DSS).",
            "How would you approach securing a legacy application?",
            "Tell me about your experience with vulnerability assessment tools.",
            "How do you balance security with user experience?"
        ],
        "tips": [
            "🔐 Get security certifications: CEH, CISSP, CompTIA Security+",
            "🧠 Understand cryptography and encryption thoroughly",
            "🔍 Learn penetration testing and vulnerability assessment tools",
            "📋 Study compliance frameworks: GDPR, HIPAA, PCI-DSS, NIST",
            "🌐 Master networking and system administration",
            "⚠️ Keep up with latest CVEs and security vulnerabilities",
            "🛡️ Understand defensive strategies and incident response",
            "🧪 Practice on platforms: HackTheBox, TryHackMe"
        ]
    },
    "Mobile App Developer": {
        "technical": [
            "Explain the app lifecycle and activity lifecycle in Android/iOS.",
            "What is state management in mobile apps? How would you handle it?",
            "Describe the difference between native and cross-platform development.",
            "Explain RESTful APIs and how mobile apps consume them.",
            "What is responsive design in mobile? How do you handle different screen sizes?",
            "Describe your approach to mobile app testing.",
            "How do you handle local data storage in mobile apps?",
            "Explain push notifications and how you'd implement them."
        ],
        "behavioral": [
            "Describe a mobile app project you built from concept to launch.",
            "How do you approach optimizing app performance and battery usage?",
            "Tell me about a time you handled a critical app bug in production.",
            "How do you stay updated with new mobile technologies?",
            "Describe your experience with app stores and deployment.",
            "How do you gather and implement user feedback?"
        ],
        "tips": [
            "📱 Master at least one platform deeply: iOS or Android",
            "🔄 Understand app lifecycle and state management",
            "🎨 Design responsive, user-friendly interfaces",
            "⚡ Focus on performance optimization and battery efficiency",
            "🧪 Write testable, clean code with proper architecture",
            "📦 Know app deployment and app store requirements",
            "🔌 Understand API integration and local storage",
            "🎯 Build a strong portfolio with 3-5 polished apps"
        ]
    },
    "UI/UX Designer": {
        "technical": [
            "Walk me through your design process from research to implementation.",
            "Explain wireframing and prototyping. What tools do you use?",
            "How do you approach user research and creating personas?",
            "What are design systems? How would you build one?",
            "Explain accessibility in UI/UX design. How do you ensure it?",
            "How do you handle design feedback and iterations?",
            "Describe your knowledge of information architecture.",
            "What is interaction design? How do you design interactions?"
        ],
        "behavioral": [
            "Describe a design project where you significantly improved user experience.",
            "How do you balance aesthetics with functionality?",
            "Tell me about a time you had to defend a design decision.",
            "How do you handle usability testing?",
            "Describe your experience collaborating with developers.",
            "How do you stay updated with design trends?"
        ],
        "tips": [
            "🎨 Master Figma and design tools deeply",
            "👥 Learn user research and testing methodologies",
            "🎭 Build a strong portfolio showcasing your design process",
            "♿ Understand accessibility (WCAG, color contrast, etc.)",
            "📐 Know design principles: hierarchy, alignment, contrast",
            "🔍 Practice competitive analysis and market research",
            "🎬 Include case studies showing your problem-solving",
            "💻 Understand HTML/CSS basics to collaborate with developers"
        ]
    },
    "Product Manager": {
        "technical": [
            "Walk me through your approach to defining product strategy.",
            "How would you prioritize features for a product roadmap?",
            "Explain how you would define success metrics for a new feature.",
            "How do you approach competitive analysis?",
            "Describe your experience with user research and feedback loops.",
            "How would you handle conflicting stakeholder priorities?",
            "Explain the product development lifecycle.",
            "How do you approach launching a new product?"
        ],
        "behavioral": [
            "Describe a product you managed that had significant impact.",
            "Tell me about a failed product or feature and what you learned.",
            "How do you work with engineering and design teams?",
            "Describe your experience with data-driven decision making.",
            "How do you gather and prioritize customer feedback?",
            "Tell me about a time you had to make a difficult decision."
        ],
        "tips": [
            "📊 Master data analysis and metrics interpretation",
            "👥 Understand user psychology and behavioral economics",
            "🎯 Define clear OKRs and success metrics",
            "📈 Learn from case studies of successful products",
            "🔄 Master product discovery and validation",
            "💼 Understand business models and market dynamics",
            "🤝 Develop strong cross-functional leadership skills",
            "📱 Know your domain: mobile, SaaS, enterprise, etc."
        ]
    },
    "Data Engineer": {
        "technical": [
            "Explain ETL vs ELT. When would you use each?",
            "Describe your experience with data warehousing and data lakes.",
            "How would you design a data pipeline for real-time streaming data?",
            "Explain MapReduce and Apache Spark in big data processing.",
            "What is data quality? How do you ensure it?",
            "Describe different data modeling techniques.",
            "How do you approach optimizing SQL queries?",
            "Explain your experience with cloud data services (Snowflake, BigQuery, etc.)."
        ],
        "behavioral": [
            "Describe a complex data pipeline you designed and built.",
            "Tell me about a time you had to optimize data processing performance.",
            "How do you handle data pipeline failures?",
            "Describe your experience working with data scientists.",
            "How do you approach data governance and compliance?",
            "Tell me about your experience with monitoring and alerting."
        ],
        "tips": [
            "🗄️ Master SQL and database design deeply",
            "⚡ Understand big data technologies: Spark, Hadoop, Kafka",
            "🔄 Learn ETL/ELT tools: Airflow, dbt, Talend",
            "☁️ Know cloud data platforms: Snowflake, BigQuery, Redshift",
            "🔍 Understand data quality and validation frameworks",
            "📊 Practice designing scalable data architectures",
            "🧪 Write clean, tested, maintainable data code",
            "📈 Build end-to-end projects from data collection to analytics"
        ]
    },
    "Cyber Security Analyst": {
        "technical": [
            "Explain the CIA triad and how it guides security decisions.",
            "What is a threat model? How would you create one?",
            "Describe common vulnerability scanning tools and techniques.",
            "Explain zero-trust security architecture.",
            "What is risk assessment? How do you prioritize remediation?",
            "Describe security incident response procedures.",
            "How do you approach secure coding practices?",
            "Explain different types of firewalls and their configurations."
        ],
        "behavioral": [
            "Tell me about your incident response experience.",
            "How do you communicate security risks to management?",
            "Describe a time you identified a critical vulnerability.",
            "How do you balance security with business needs?",
            "Tell me about your experience with security audits.",
            "How do you handle false positives in security alerts?"
        ],
        "tips": [
            "🎓 Pursue industry certifications (CEH, OSCP, CISSP)",
            "📚 Study the OWASP Top 10 thoroughly",
            "🔧 Master security tools: Burp Suite, Metasploit, Wireshark",
            "🛡️ Understand defense in depth strategies",
            "📋 Know compliance frameworks relevant to your industry",
            "🔍 Practice hands-on labs on HackTheBox and TryHackMe",
            "📊 Stay informed about latest CVEs and threats",
            "🤝 Develop communication skills for non-technical audiences"
        ]
    },
    "Software Engineer": {
        "technical": [
            "Explain SOLID principles and why they matter.",
            "Describe different software design patterns with examples.",
            "How would you approach system design for a large-scale application?",
            "Explain the difference between monolithic and microservices architecture.",
            "What is ACID? How does it relate to database transactions?",
            "Describe your experience with version control and branching strategies.",
            "How do you approach writing testable, maintainable code?",
            "Explain refactoring and when you would do it."
        ],
        "behavioral": [
            "Describe a complex software project you developed.",
            "Tell me about a time you refactored significant code.",
            "How do you approach code reviews?",
            "Describe your experience with technical debt.",
            "Tell me about a time you optimized code performance.",
            "How do you stay updated with software engineering best practices?"
        ],
        "tips": [
            "🏗️ Master algorithms and data structures",
            "💻 Build real-world projects on GitHub",
            "🧪 Learn testing: unit, integration, end-to-end tests",
            "🔄 Understand design patterns and architectural principles",
            "📚 Practice coding on platforms like LeetCode",
            "🎯 Focus on code quality and maintainability",
            "🤝 Develop strong collaboration and communication skills",
            "⚡ Learn performance optimization techniques"
        ]
    },
    "DevOps Engineer": {
        "technical": [
            "Explain the DevOps philosophy and its impact on software delivery.",
            "Describe your experience with CI/CD pipelines and tools like Jenkins or GitLab CI.",
            "What is Infrastructure as Code? Explain tools like Terraform or Ansible.",
            "How would you design a monitoring and logging strategy?",
            "Explain containerization with Docker and orchestration with Kubernetes.",
            "What is GitOps and how does it differ from traditional deployment?",
            "How do you approach disaster recovery and backup strategies?",
            "Describe your experience with cloud platforms (AWS, Azure, GCP)."
        ],
        "behavioral": [
            "Tell me about a complex deployment issue you resolved.",
            "How do you approach improving deployment frequency and reliability?",
            "Describe your experience collaborating with development teams.",
            "Tell me about a time you reduced infrastructure costs.",
            "How do you handle on-call responsibilities and incidents?",
            "Describe your experience with security and compliance in DevOps."
        ],
        "tips": [
            "🔄 Master CI/CD tools: Jenkins, GitLab CI, GitHub Actions, CircleCI",
            "🏗️ Learn Infrastructure as Code: Terraform, CloudFormation, Ansible",
            "🐳 Deeply understand Docker and Kubernetes",
            "☁️ Know cloud platforms: AWS, Azure, GCP",
            "📊 Learn monitoring tools: Prometheus, Grafana, ELK Stack",
            "🔐 Understand security in DevOps: secrets management, scanning",
            "🚀 Practice designing scalable CI/CD pipelines",
            "🧪 Automate everything: testing, deployment, monitoring"
        ]
    },
    "Backend Developer": {
        "technical": [
            "Explain how you design RESTful APIs with proper HTTP methods and status codes.",
            "What are microservices? Describe the pros and cons compared to monolithic architecture.",
            "How do you handle database transactions and ACID properties?",
            "Explain different caching strategies and when to use each.",
            "What is horizontal vs vertical scaling? When would you use each?",
            "How do you approach API authentication and authorization?",
            "Describe your experience with message queues and asynchronous processing.",
            "How would you optimize database query performance?"
        ],
        "behavioral": [
            "Describe a backend system you designed from scratch.",
            "Tell me about a time you handled a critical production issue.",
            "How do you approach API versioning and backward compatibility?",
            "Describe your experience with database migrations.",
            "How do you work with frontend developers to design APIs?",
            "Tell me about your experience with code reviews and best practices."
        ],
        "tips": [
            "🌐 Master RESTful API design principles",
            "🗄️ Deep understanding of SQL and database design",
            "🔄 Learn about microservices patterns and challenges",
            "💾 Understand caching strategies: Redis, Memcached",
            "📊 Master database optimization and indexing",
            "🔐 Know authentication/authorization: JWT, OAuth, SAML",
            "📨 Understand message queues: RabbitMQ, Kafka",
            "🧪 Write well-tested backend code with proper documentation"
        ]
    },
    "Frontend Developer": {
        "technical": [
            "Explain the virtual DOM and how React uses it for efficient updates.",
            "What is state management? Describe tools like Redux or Context API.",
            "How do you approach responsive design and mobile-first development?",
            "Explain CSS Grid and Flexbox with practical examples.",
            "What are web components and when would you use them?",
            "How do you optimize web application performance?",
            "Describe your experience with build tools like Webpack or Vite.",
            "How would you implement real-time updates using WebSockets?"
        ],
        "behavioral": [
            "Describe a complex frontend feature you implemented.",
            "Tell me about a time you improved user experience.",
            "How do you handle browser compatibility issues?",
            "Describe your experience with accessibility and inclusive design.",
            "Tell me about your experience with design collaboration.",
            "How do you approach performance optimization?"
        ],
        "tips": [
            "⚛️ Master React, Vue, or Angular deeply",
            "🎨 Understand CSS, Flexbox, Grid, animations",
            "🚀 Learn performance optimization techniques",
            "📱 Master responsive design and mobile development",
            "♿ Understand accessibility (WCAG) principles",
            "🧪 Write testable code with Jest, React Testing Library",
            "📦 Master build tools: Webpack, Vite, Parcel",
            "💻 Practice with modern JavaScript (ES6+, TypeScript)"
        ]
    },
    "Machine Learning Engineer": {
        "technical": [
            "Explain the difference between ML Engineering and Data Science.",
            "How would you deploy a machine learning model to production?",
            "Describe your experience with model versioning and experiment tracking.",
            "What is model drift? How do you detect and handle it?",
            "Explain how you would build a feature store for ML systems.",
            "How do you approach A/B testing for ML models?",
            "Describe your experience with model inference optimization.",
            "What is MLOps and why is it important?"
        ],
        "behavioral": [
            "Describe a machine learning project you took from research to production.",
            "Tell me about challenges you faced deploying models to production.",
            "How do you collaborate with data scientists and software engineers?",
            "Describe your experience with model monitoring and debugging.",
            "Tell me about a time you improved model performance.",
            "How do you approach model scalability and reliability?"
        ],
        "tips": [
            "🤖 Master ML frameworks: TensorFlow, PyTorch, scikit-learn",
            "📊 Understand feature engineering and data pipelines",
            "🚀 Learn model deployment: Docker, Kubernetes, serverless",
            "📈 Master MLOps tools: MLflow, Kubeflow, SageMaker",
            "🔄 Understand version control for models and data",
            "⚡ Optimize model inference for performance",
            "📉 Learn about model monitoring and drift detection",
            "🧪 Practice end-to-end ML projects with production considerations"
        ]
    },
    "Data Analyst": {
        "technical": [
            "Explain how you approach data exploration and analysis.",
            "What is the difference between descriptive, diagnostic, predictive, and prescriptive analytics?",
            "How would you design a dashboard for business stakeholders?",
            "Explain SQL window functions and when to use them.",
            "What are common statistical distributions and when would you use them?",
            "How do you approach data validation and quality checks?",
            "Describe your experience with BI tools like Tableau or Power BI.",
            "How would you identify and handle data outliers?"
        ],
        "behavioral": [
            "Describe a data analysis project that drove business decisions.",
            "Tell me about a time you presented findings to non-technical stakeholders.",
            "How do you approach gathering requirements for reports or dashboards?",
            "Describe your experience with data storytelling.",
            "Tell me about a time you identified a data quality issue.",
            "How do you stay updated with analytics trends?"
        ],
        "tips": [
            "📊 Master SQL deeply for data extraction",
            "📈 Learn BI tools: Tableau, Power BI, Looker",
            "📉 Understand statistics and probability",
            "🎨 Develop data visualization skills",
            "💾 Master Python for data analysis: pandas, numpy",
            "🗄️ Understand database concepts and data modeling",
            "📝 Practice data storytelling and communication",
            "🔍 Build a portfolio with interesting analyses"
        ]
    },
    "Database Administrator": {
        "technical": [
            "Explain ACID properties and their importance in database systems.",
            "How would you approach database performance tuning?",
            "Describe your experience with backup, recovery, and disaster recovery.",
            "What is database replication and when would you use it?",
            "How do you handle database security and access control?",
            "Explain indexing strategies and how they impact query performance.",
            "Describe your experience with both relational and NoSQL databases.",
            "How would you approach database migration and upgrades?"
        ],
        "behavioral": [
            "Tell me about a time you resolved a critical database issue.",
            "Describe your experience with high-availability database systems.",
            "How do you approach capacity planning for databases?",
            "Tell me about your experience with database monitoring.",
            "Describe a time you optimized database performance.",
            "How do you balance performance with data integrity?"
        ],
        "tips": [
            "🗄️ Master SQL database administration (MySQL, PostgreSQL, Oracle)",
            "🔒 Understand security: encryption, access control, auditing",
            "📊 Master backup and recovery strategies",
            "⚡ Learn performance tuning: indexing, query optimization",
            "🔄 Understand replication and high availability",
            "📈 Know NoSQL databases: MongoDB, Cassandra",
            "🧪 Practice monitoring and alerting setup",
            "🚀 Understand cloud database services: RDS, Azure SQL, Cloud SQL"
        ]
    },
    "Solutions Architect": {
        "technical": [
            "How would you approach designing a scalable enterprise solution?",
            "Explain how you select technologies for a given business problem.",
            "What is cloud-native architecture? What are its benefits?",
            "How do you ensure high availability and fault tolerance in designs?",
            "Describe your experience with multi-cloud or hybrid cloud strategies.",
            "How would you design security into an architecture from the start?",
            "What is the CAP theorem and how does it relate to distributed systems?",
            "How do you approach cost optimization in cloud architectures?"
        ],
        "behavioral": [
            "Describe a complex architecture you designed for an enterprise client.",
            "How do you work with business stakeholders to understand requirements?",
            "Tell me about a time you recommended a technology change.",
            "Describe your experience with architecture documentation.",
            "How do you balance technical perfection with practical constraints?",
            "Tell me about your experience with proof of concepts (POCs)."
        ],
        "tips": [
            "🏗️ Master enterprise architecture frameworks (TOGAF, Zachman)",
            "☁️ Deep knowledge of cloud platforms and services",
            "🔐 Understand security best practices and compliance",
            "📊 Learn distributed systems concepts",
            "💰 Master cost analysis and optimization",
            "🔄 Understand microservices and modern architectures",
            "🧭 Practice creating architecture documentation",
            "💼 Develop business acumen and stakeholder management skills"
        ]
    },
    "Systems Administrator": {
        "technical": [
            "Explain the difference between Windows and Linux systems administration.",
            "How would you set up and configure a secure network?",
            "Describe your experience with active directory and user management.",
            "What is a firewall? How would you configure one?",
            "How do you approach system patching and updates?",
            "Explain your experience with virtualization technologies.",
            "How would you implement disk encryption and data protection?",
            "Describe your experience with system monitoring and alerting."
        ],
        "behavioral": [
            "Tell me about a time you prevented a major system outage.",
            "Describe your experience with disaster recovery planning.",
            "How do you handle after-hours support and on-call duties?",
            "Tell me about a time you improved system security.",
            "How do you approach capacity planning?",
            "Describe your experience with system documentation."
        ],
        "tips": [
            "🖥️ Master Windows and Linux administration deeply",
            "🔒 Understand network security and firewalls",
            "📝 Learn Active Directory and user management",
            "🔄 Understand virtualization: Hyper-V, VMware, KVM",
            "💾 Master backup and recovery procedures",
            "📊 Learn system monitoring tools: Zabbix, Nagios",
            "⚡ Automate administration tasks with scripts",
            "🧪 Stay current with security best practices"
        ]
    },
    "Business Analyst": {
        "technical": [
            "How do you gather and document business requirements?",
            "Explain different business analysis methodologies (BABOK).",
            "How would you create use cases and user stories?",
            "What is process modeling? Describe notation like BPMN.",
            "How do you approach data requirements analysis?",
            "Explain the difference between functional and non-functional requirements.",
            "How would you validate requirements with stakeholders?",
            "What is a requirements traceability matrix and why is it important?"
        ],
        "behavioral": [
            "Describe a complex business problem you helped solve.",
            "Tell me about a time requirements changed mid-project.",
            "How do you manage stakeholder expectations?",
            "Describe your experience presenting findings to executives.",
            "Tell me about your experience with agile methodologies.",
            "How do you ensure requirements are clear and testable?"
        ],
        "tips": [
            "📋 Master requirements gathering techniques",
            "🎯 Learn use case and user story writing",
            "📊 Understand process modeling and BPMN",
            "🧠 Develop stakeholder management skills",
            "💬 Practice clear communication and documentation",
            "📈 Understand business metrics and KPIs",
            "🔄 Learn agile and scrum methodologies",
            "🧪 Practice creating requirements documentation"
        ]
    },
    "Technical Writer": {
        "technical": [
            "How do you approach writing technical documentation?",
            "Explain different types of technical documentation (API docs, user guides, etc.).",
            "What tools do you use for documentation and knowledge management?",
            "How do you ensure documentation accuracy and completeness?",
            "Describe your experience with version control for documentation.",
            "How do you make complex technical concepts understandable?",
            "What is API documentation and how would you write it?",
            "How do you approach documentation maintenance and updates?"
        ],
        "behavioral": [
            "Describe a documentation project you led that improved user experience.",
            "Tell me about a time you had to clarify complex technical concepts.",
            "How do you work with development teams to gather information?",
            "Describe your experience with technical review processes.",
            "Tell me about your experience with agile documentation.",
            "How do you handle feedback and iterative improvements?"
        ],
        "tips": [
            "✍️ Master technical writing best practices",
            "🛠️ Learn documentation tools: Confluence, GitBook, ReadTheDocs",
            "📚 Understand different documentation types",
            "🎨 Learn to create diagrams and visual aids",
            "🔍 Develop attention to detail for accuracy",
            "💬 Practice explaining technical concepts simply",
            "📱 Understand responsive documentation design",
            "🧪 Practice creating user-focused documentation"
        ]
    },
    "IT Manager": {
        "technical": [
            "How do you approach IT strategy and planning for an organization?",
            "Describe your experience managing IT budgets and resources.",
            "How would you build and manage a high-performing IT team?",
            "Explain your understanding of IT governance and compliance.",
            "How do you approach IT risk management?",
            "Describe your experience with vendor management.",
            "How would you approach digital transformation initiatives?",
            "What is IT service management and how would you implement it?"
        ],
        "behavioral": [
            "Describe a successful IT project you led.",
            "Tell me about a time you managed a crisis or outage.",
            "How do you communicate IT value to business leaders?",
            "Describe your experience with change management.",
            "Tell me about your experience with team development.",
            "How do you balance IT security with business needs?"
        ],
        "tips": [
            "👔 Develop strong business acumen and leadership skills",
            "📊 Master IT budgeting and financial management",
            "🎯 Learn IT service management (ITIL)",
            "🔐 Understand IT governance and compliance frameworks",
            "🤝 Develop team management and communication skills",
            "🔄 Understand change management practices",
            "📈 Master strategic planning and roadmap creation",
            "🧪 Stay informed about emerging IT trends"
        ]
    },
    "Engineering Manager": {
        "technical": [
            "How do you balance technical depth with management responsibilities?",
            "Describe your approach to team organization and structure.",
            "How do you conduct effective one-on-ones and performance reviews?",
            "Explain your approach to technical decision-making.",
            "How do you foster innovation and experimentation?",
            "Describe your experience with agile methodologies.",
            "How do you approach hiring and team building?",
            "What is your philosophy on code reviews and technical excellence?"
        ],
        "behavioral": [
            "Describe a difficult personnel situation you managed.",
            "Tell me about a time you had to make a tough technical decision.",
            "How do you support your team's professional development?",
            "Describe your experience with conflict resolution.",
            "Tell me about a successful project you managed.",
            "How do you maintain team morale and engagement?"
        ],
        "tips": [
            "👥 Develop strong leadership and mentoring skills",
            "🎯 Master agile/scrum methodologies",
            "📊 Learn performance management and reviews",
            "🤝 Develop emotional intelligence and communication",
            "🔄 Understand change management",
            "💬 Practice giving and receiving feedback",
            "📈 Learn strategic planning for technical teams",
            "🧪 Stay hands-on with technical decisions"
        ]
    },
    "Scrum Master": {
        "technical": [
            "Explain the Scrum framework and its key ceremonies.",
            "What is the difference between Scrum Master and Project Manager?",
            "How do you facilitate sprint planning and estimation?",
            "Describe your approach to removing impediments.",
            "What is a definition of done and why is it important?",
            "How do you facilitate backlog refinement?",
            "Explain retrospectives and how you use them for continuous improvement.",
            "How would you handle a team resistant to Scrum practices?"
        ],
        "behavioral": [
            "Describe a team you helped transform through Scrum.",
            "Tell me about a time you resolved team conflict.",
            "How do you work with product owners on backlog management?",
            "Describe your experience with scaling Scrum.",
            "Tell me about your experience with metrics and dashboards.",
            "How do you foster psychological safety in the team?"
        ],
        "tips": [
            "🎯 Get Certified Scrum Master (CSM) certification",
            "📋 Master Scrum ceremonies and practices",
            "🤝 Develop strong facilitation skills",
            "💬 Learn effective communication techniques",
            "🔄 Understand continuous improvement mindset",
            "📊 Master agile metrics and reporting",
            "👥 Develop team coaching skills",
            "🧪 Stay updated with agile best practices"
        ]
    },
    "Release Manager": {
        "technical": [
            "How do you approach release planning and scheduling?",
            "Describe your experience with version control and branching strategies.",
            "How would you manage dependencies between releases?",
            "Explain your approach to release testing and quality assurance.",
            "How do you manage rollback procedures?",
            "Describe your experience with release notes and documentation.",
            "How would you communicate release plans to stakeholders?",
            "What is continuous delivery and how does it relate to release management?"
        ],
        "behavioral": [
            "Describe a complex release you managed successfully.",
            "Tell me about a time a release had issues.",
            "How do you manage stakeholder expectations around release timing?",
            "Describe your experience with crisis management.",
            "Tell me about your experience with post-release monitoring.",
            "How do you balance speed with stability?"
        ],
        "tips": [
            "🚀 Master release management best practices",
            "📋 Learn version control deeply: Git, branching strategies",
            "🔄 Understand CI/CD pipelines and automation",
            "📊 Master release metrics and reporting",
            "🤝 Develop stakeholder communication skills",
            "🔐 Understand change control and governance",
            "🧪 Learn testing strategies for releases",
            "📈 Master release planning and scheduling tools"
        ]
    },
    "Blockchain Developer": {
        "technical": [
            "Explain how blockchain technology works and its key components.",
            "What is the difference between Bitcoin and Ethereum?",
            "Describe your experience with smart contracts and Solidity.",
            "Explain consensus mechanisms: Proof of Work vs Proof of Stake.",
            "How would you approach building a decentralized application (dApp)?",
            "What are the security considerations in blockchain development?",
            "Describe your experience with blockchain platforms.",
            "How do you approach testing and auditing smart contracts?"
        ],
        "behavioral": [
            "Describe a blockchain project you developed.",
            "Tell me about security vulnerabilities you've encountered.",
            "How do you stay updated with blockchain developments?",
            "Describe your experience with token economics.",
            "Tell me about your experience with blockchain communities.",
            "How do you approach scalability challenges?"
        ],
        "tips": [
            "⛓️ Master Solidity and smart contract development",
            "🏗️ Understand blockchain fundamentals deeply",
            "🔐 Learn security best practices for blockchain",
            "📚 Study consensus mechanisms and their trade-offs",
            "🧪 Practice smart contract testing and auditing",
            "💡 Understand DeFi and crypto economics",
            "🌐 Master web3 development: Web3.js, Ethers.js",
            "🎯 Build real dApps and share on GitHub"
        ]
    },
    "Game Developer": {
        "technical": [
            "Explain the game development pipeline from concept to release.",
            "Describe your experience with game engines like Unity or Unreal Engine.",
            "How do you approach game physics and collision detection?",
            "Explain different types of games and their technical requirements.",
            "How would you optimize a game for performance?",
            "Describe your experience with multiplayer game development.",
            "What is a game loop and why is it important?",
            "How do you approach graphics programming and shaders?"
        ],
        "behavioral": [
            "Describe a game you developed from concept to completion.",
            "Tell me about technical challenges you've overcome.",
            "How do you approach player experience and balance?",
            "Describe your experience with game testing.",
            "Tell me about your experience with game communities.",
            "How do you stay updated with game development trends?"
        ],
        "tips": [
            "🎮 Master Unity or Unreal Engine deeply",
            "🎨 Understand game design principles",
            "⚡ Master game physics and performance optimization",
            "🧬 Learn C# or C++ for game development",
            "🌐 Understand networking for multiplayer games",
            "🎬 Master graphics programming basics",
            "🧪 Build a strong portfolio with published games",
            "👥 Participate in game development communities"
        ]
    },
    "Embedded Systems Engineer": {
        "technical": [
            "Explain the difference between embedded systems and general computing.",
            "Describe your experience with microcontrollers and microprocessors.",
            "How do you approach embedded software development?",
            "Explain hardware and software integration challenges.",
            "Describe your experience with IoT platforms and protocols.",
            "How would you debug embedded systems?",
            "What is real-time operating systems (RTOS) and when do you use it?",
            "Explain power consumption optimization in embedded systems."
        ],
        "behavioral": [
            "Describe an embedded systems project you led.",
            "Tell me about a challenging hardware/software integration issue.",
            "How do you approach prototyping and testing?",
            "Describe your experience with product development lifecycle.",
            "Tell me about your experience with IoT deployments.",
            "How do you stay current with embedded technology trends?"
        ],
        "tips": [
            "🔌 Master C/C++ for embedded systems",
            "🏗️ Deep understanding of microcontrollers and ARM architecture",
            "📡 Learn IoT protocols: MQTT, CoAP, LoRaWAN",
            "🔧 Master hardware debugging and profiling tools",
            "⚡ Understand power management and optimization",
            "🧬 Know real-time OS concepts",
            "🧪 Practice prototyping with Arduino, Raspberry Pi",
            "📊 Understand firmware development and deployment"
        ]
    },
    "Network Engineer": {
        "technical": [
            "Explain the OSI model and protocols at each layer.",
            "Describe your experience with network design and implementation.",
            "How would you secure a corporate network?",
            "Explain routing protocols and how they work.",
            "What is network virtualization and when would you use it?",
            "Describe your experience with network monitoring and troubleshooting.",
            "How do you approach network capacity planning?",
            "Explain VPN technology and its applications."
        ],
        "behavioral": [
            "Describe a complex network you designed or managed.",
            "Tell me about a time you resolved a critical network issue.",
            "How do you approach network upgrades and migrations?",
            "Describe your experience with vendor management.",
            "Tell me about your experience with disaster recovery.",
            "How do you balance performance with security?"
        ],
        "tips": [
            "🌐 Master networking fundamentals: TCP/IP, DNS, DHCP",
            "🔧 Learn networking tools: Wireshark, Cisco devices",
            "🔐 Understand network security: firewalls, VPNs, IDS/IPS",
            "📊 Master network monitoring: NetFlow, SNMP",
            "🔄 Learn routing and switching protocols",
            "☁️ Understand SD-WAN and cloud networking",
            "🧪 Get certifications: CCNA, CCNP",
            "📈 Practice network design and documentation"
        ]
    },
    "IT Security Specialist": {
        "technical": [
            "Explain defense in depth strategy for information security.",
            "Describe your experience with security information and event management (SIEM).",
            "How do you approach vulnerability management and remediation?",
            "Explain different types of authentication and authorization.",
            "Describe your experience with security compliance frameworks.",
            "How would you design a security incident response plan?",
            "Explain data loss prevention (DLP) strategies.",
            "What is security automation and why is it important?"
        ],
        "behavioral": [
            "Describe a security incident you helped resolve.",
            "Tell me about your experience with security audits.",
            "How do you communicate security concerns to executives?",
            "Describe your experience with security training programs.",
            "Tell me about your experience with compliance audits.",
            "How do you stay updated with emerging security threats?"
        ],
        "tips": [
            "🔐 Master security frameworks: NIST, ISO 27001",
            "🧪 Learn security testing: penetration testing, vulnerability assessment",
            "📊 Master SIEM and security monitoring tools",
            "🛡️ Understand threat intelligence and incident response",
            "📋 Learn compliance requirements: GDPR, HIPAA, PCI-DSS",
            "🔄 Understand security automation and orchestration",
            "📈 Get certifications: CISSP, CISM, CEH",
            "🎯 Stay informed about latest threats and vulnerabilities"
        ]
    },
    "Solutions Engineer": {
        "technical": [
            "How do you approach understanding customer technical requirements?",
            "Describe your experience with solution architecture and design.",
            "How would you evaluate and recommend technologies to clients?",
            "Explain your approach to proof of concepts (POCs).",
            "How do you handle technical due diligence?",
            "Describe your experience with system integration.",
            "How would you approach migration planning for large systems?",
            "Explain your experience with technical sales enablement."
        ],
        "behavioral": [
            "Describe a complex solution you designed for a client.",
            "Tell me about a time you had to manage difficult stakeholder expectations.",
            "How do you communicate technical concepts to non-technical audiences?",
            "Describe your experience with post-sales support.",
            "Tell me about your experience with customer success.",
            "How do you handle objections and technical concerns?"
        ],
        "tips": [
            "🏗️ Master solution architecture and design methodologies",
            "🤝 Develop strong presentation and communication skills",
            "💼 Understand customer business models and needs",
            "🔧 Keep hands-on with technical skills",
            "📊 Master product knowledge deeply",
            "🎯 Learn sales techniques and negotiation",
            "🧪 Experience with real customer implementations",
            "📈 Develop thought leadership and industry knowledge"
        ]
    },
    "Technical Consultant": {
        "technical": [
            "How do you approach consulting engagements and discovery?",
            "Describe your experience with technology assessments.",
            "How would you create a technology roadmap for a client?",
            "Explain your approach to best practices and standards adoption.",
            "How do you handle resistance to change in consulting?",
            "Describe your experience with cost-benefit analysis.",
            "How would you approach building a business case for technology investments?",
            "Explain your experience with competitive analysis and positioning."
        ],
        "behavioral": [
            "Describe a successful consulting engagement.",
            "Tell me about a challenging client situation you resolved.",
            "How do you build trust and credibility with clients?",
            "Describe your experience with C-level presentations.",
            "Tell me about your experience with long-term client relationships.",
            "How do you measure success of consulting engagements?"
        ],
        "tips": [
            "💼 Develop strong business acumen and strategic thinking",
            "🤝 Master consulting methodologies and frameworks",
            "🎯 Learn effective stakeholder management",
            "📊 Develop data-driven decision making skills",
            "💬 Master presentation and communication skills",
            "🔍 Deep industry and technology knowledge",
            "📈 Build a strong personal brand and reputation",
            "🧪 Continuous learning and professional development"
        ]
    },
    "API Developer": {
        "technical": [
            "Explain REST principles and how to design RESTful APIs.",
            "Describe your experience with API versioning strategies.",
            "How do you approach API security and rate limiting?",
            "Explain GraphQL and how it differs from REST.",
            "How would you document your APIs for developers?",
            "Describe your experience with API testing and validation.",
            "How do you approach API error handling and status codes?",
            "Explain your experience with API gateways and management."
        ],
        "behavioral": [
            "Describe an API you designed that had significant adoption.",
            "Tell me about a time you had to make breaking changes to an API.",
            "How do you gather feedback from API consumers?",
            "Describe your experience with API performance optimization.",
            "Tell me about your experience with API versioning challenges.",
            "How do you approach developer experience for your APIs?"
        ],
        "tips": [
            "🌐 Master REST API design principles deeply",
            "📚 Learn API documentation: OpenAPI/Swagger, AsyncAPI",
            "🔐 Understand API security: OAuth, JWT, API keys",
            "⚡ Master API performance optimization",
            "🧪 Learn API testing frameworks and tools",
            "📊 Understand API analytics and monitoring",
            "🔄 Learn API versioning and evolution strategies",
            "👥 Focus on developer experience and adoption"
        ]
    },
    "Integration Engineer": {
        "technical": [
            "Explain different integration patterns and when to use each.",
            "Describe your experience with ETL tools and platforms.",
            "How would you design an integration solution for legacy systems?",
            "Explain API-led connectivity and its benefits.",
            "How do you approach data mapping and transformation?",
            "Describe your experience with message queues and event-driven architecture.",
            "How would you ensure data quality in integrations?",
            "Explain your experience with iPaaS platforms."
        ],
        "behavioral": [
            "Describe a complex integration project you led.",
            "Tell me about challenges you faced with legacy systems.",
            "How do you approach integration testing?",
            "Describe your experience with cross-team collaboration.",
            "Tell me about your experience with integration monitoring.",
            "How do you handle integration failures and recovery?"
        ],
        "tips": [
            "🔄 Master integration patterns and best practices",
            "🛠️ Learn integration platforms: MuleSoft, Boomi, Talend",
            "📊 Understand ETL and data transformation",
            "📨 Master message queues and event streaming",
            "🔐 Understand data security in integrations",
            "🧪 Master integration testing approaches",
            "📈 Learn API design for integrations",
            "🎯 Build real integration solutions and case studies"
        ]
    },
    "IT Portfolio Manager": {
        "technical": [
            "How do you approach IT portfolio management and governance?",
            "Explain different portfolio management frameworks and methodologies.",
            "How would you balance innovation vs maintenance in IT investments?",
            "Describe your experience with project prioritization.",
            "How do you measure IT portfolio value and ROI?",
            "Explain your approach to risk management in portfolios.",
            "How would you align IT portfolio with business strategy?",
            "Describe your experience with resource capacity planning."
        ],
        "behavioral": [
            "Describe a portfolio you managed successfully.",
            "Tell me about a difficult prioritization decision.",
            "How do you communicate portfolio status to executives?",
            "Describe your experience with stakeholder management.",
            "Tell me about your experience with change management.",
            "How do you handle conflicting project priorities?"
        ],
        "tips": [
            "📊 Master portfolio management frameworks",
            "💼 Develop strong business acumen",
            "🎯 Learn strategic planning and alignment",
            "📈 Master financial analysis and ROI calculation",
            "🤝 Develop stakeholder and executive communication skills",
            "🔄 Understand agile and hybrid portfolio management",
            "💡 Learn risk management practices",
            "📱 Master portfolio management tools and dashboards"
        ]
    }
}

INTERVIEW_TIPS = {
    "general": {
        "before_interview": [
            "Research the company thoroughly: mission, products, culture, recent news",
            "Understand the job description and required skills",
            "Prepare your elevator pitch (30 seconds about yourself)",
            "Practice common questions: Tell me about yourself, Why this role?",
            "Test your audio/video setup if it's a virtual interview",
            "Plan your route and timing to arrive 10-15 minutes early",
            "Prepare specific examples using the STAR method",
            "Have your resume and portfolio ready"
        ],
        "during_interview": [
            "Make strong eye contact and maintain good posture",
            "Listen carefully and answer the complete question",
            "Use specific examples with metrics and outcomes",
            "Ask clarifying questions if you don't understand",
            "Don't interrupt the interviewer",
            "Show genuine enthusiasm for the role and company",
            "Be prepared to discuss your projects in detail",
            "Avoid speaking negatively about previous employers",
            "Stay calm and think before answering",
            "Take notes during the interview"
        ],
        "after_interview": [
            "Send a thank you email within 24 hours",
            "Mention specific topics you discussed",
            "Reiterate your interest in the position",
            "Address any concerns you think the interviewer had",
            "Follow up if you don't hear back within the expected timeframe",
            "Reflect on what went well and what to improve",
            "Keep records of interview details and contacts"
        ]
    },
    "star_method": {
        "what": "The STAR method helps you structure behavioral answers effectively",
        "framework": [
            "Situation: Describe the context and challenge",
            "Task: Explain your specific responsibility",
            "Action: Detail the steps you took to address it",
            "Result: Share the outcome and what you learned"
        ],
        "example": "When answering 'Tell me about a challenge you overcame': S - We had a broken deployment pipeline, T - I was tasked with fixing it, A - I analyzed logs, rewrote scripts, and coordinated with the team, R - Reduced deployment time by 80%, saving 10 hours/week"
    },
    "red_flags": [
        "❌ Speaking negatively about past companies or managers",
        "❌ Lack of specific examples or vague answers",
        "❌ Talking too much or not listening",
        "❌ Not asking questions about the role or company",
        "❌ Appearing unprepared or unfamiliar with your own resume",
        "❌ Salary negotiations too early in the process",
        "❌ Speaking about compensation before discussing value",
        "❌ Poor body language or lack of eye contact"
    ],
    "green_flags": [
        "✅ Concrete examples with specific metrics",
        "✅ Genuine curiosity about the company and role",
        "✅ Clear communication and good listening skills",
        "✅ Enthusiasm and passion for the work",
        "✅ Growth mindset and willingness to learn",
        "✅ Asking thoughtful questions about team and company",
        "✅ Professional behavior and appropriate energy level"
    ]
}


@app.route('/interview', methods=['GET', 'POST'])
def interview():
    career = request.form.get('career', '') or request.args.get('career', 'AI Engineer')
    question_type = request.form.get('question_type', 'technical')
    
    questions = INTERVIEW_QUESTIONS.get(career, INTERVIEW_QUESTIONS["AI Engineer"])
    tips = questions.get("tips", [])
    
    selected_questions = questions.get(question_type, [])
    
    career_list = sorted(INTERVIEW_QUESTIONS.keys())
    
    return render_template(
        'interview.html',
        career=career,
        career_list=career_list,
        question_type=question_type,
        selected_questions=selected_questions,
        tips=tips,
        interview_tips=INTERVIEW_TIPS,
        all_tips=INTERVIEW_TIPS
    )


@app.route("/roadmap/<career>")
def roadmap(career):
    steps = CAREER_ROADMAPS.get(career, CAREER_ROADMAPS["AI Engineer"])
    return render_template("roadmap.html", career=career, steps=steps)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

