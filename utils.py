import os
import json
import zipfile
import io
import random
import concurrent.futures
from typing import List, Dict, Tuple
import openai
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
from datetime import datetime
import re

def clean_text_formatting(text: str) -> str:
    """
    Converts Markdown-style formatting (*, **, _) to ReportLab-compatible XML tags.
    """
    if not isinstance(text, str):
        return str(text)
        
    # Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Italics: *text* or _text_ -> <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    
    return text

# Load environment variables if running locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    # Streamlit Cloud deployment often uses st.secrets, but for now we rely on env vars or user input if implemented.
    if not api_key:
        return None
    return openai.OpenAI(api_key=api_key)

STATIC_CANDIDATES = [
   
  {
    "name": "Ananya Rao",
    "gender": "Female",
    "origin": "Asian",
    "location": "Berlin, Germany",
    "university": "TU Berlin",
    "email": "ananya.rao@example.com",
    "phone": "+49 151 11111111"
  },
  {
    "name": "Mei Lin Zhang",
    "gender": "Female",
    "origin": "Asian",
    "location": "Munich, Germany",
    "university": "TU Munich",
    "email": "mei.zhang@example.com",
    "phone": "+49 152 22222222"
  },
  {
    "name": "Julia Schmidt",
    "gender": "Female",
    "origin": "White",
    "location": "Hamburg, Germany",
    "university": "RWTH Aachen",
    "email": "julia.schmidt@example.com",
    "phone": "+49 170 33333333"
  },
  {
    "name": "Laura Hoffmann",
    "gender": "Female",
    "origin": "White",
    "location": "Dresden, Germany",
    "university": "TU Dresden",
    "email": "laura.hoffmann@example.com",
    "phone": "+49 171 44444444"
  },
  {
    "name": "Amina Tesfaye",
    "gender": "Female",
    "origin": "African",
    "location": "Frankfurt, Germany",
    "university": "KIT Karlsruhe",
    "email": "amina.tesfaye@example.com",
    "phone": "+49 160 55555555"
  },
  {
    "name": "Sofia Alvarez",
    "gender": "Female",
    "origin": "Latin American",
    "location": "Cologne, Germany",
    "university": "University of Cologne",
    "email": "sofia.alvarez@example.com",
    "phone": "+49 175 66666666"
  },
  {
    "name": "Rahul Verma",
    "gender": "Male",
    "origin": "Asian",
    "location": "Stuttgart, Germany",
    "university": "University of Stuttgart",
    "email": "rahul.verma@example.com",
    "phone": "+49 151 77777777"
  },
  {
    "name": "Hiroshi Tanaka",
    "gender": "Male",
    "origin": "Asian",
    "location": "Darmstadt, Germany",
    "university": "TU Darmstadt",
    "email": "hiroshi.tanaka@example.com",
    "phone": "+49 152 88888888"
  },
  {
    "name": "Thomas Müller",
    "gender": "Male",
    "origin": "White",
    "location": "Berlin, Germany",
    "university": "TU Berlin",
    "email": "thomas.mueller@example.com",
    "phone": "+49 170 99999999"
  },
  {
    "name": "Felix Koch",
    "gender": "Male",
    "origin": "White",
    "location": "Munich, Germany",
    "university": "TU Munich",
    "email": "felix.koch@example.com",
    "phone": "+49 171 10101010"
  },
  {
    "name": "Daniel Boateng",
    "gender": "Male",
    "origin": "African",
    "location": "Berlin, Germany",
    "university": "TU Berlin",
    "email": "daniel.boateng@example.com",
    "phone": "+49 160 11112222"
  },
  {
    "name": "Omar Al-Hassan",
    "gender": "Male",
    "origin": "Middle Eastern",
    "location": "Bonn, Germany",
    "university": "University of Bonn",
    "email": "omar.alhassan@example.com",
    "phone": "+49 175 33334444"
  },
  
  {
    "name": "Priya Nair",
    "gender": "Female",
    "origin": "Asian",
    "location": "Bremen, Germany",
    "university": "University of Bremen",
    "email": "priya.nair@example.com",
    "phone": "+49 151 21212121"
  },
  {
    "name": "Yuki Nakamura",
    "gender": "Female",
    "origin": "Asian",
    "location": "Augsburg, Germany",
    "university": "University of Augsburg",
    "email": "yuki.nakamura@example.com",
    "phone": "+49 152 23232323"
  },
  {
    "name": "Hannah Keller",
    "gender": "Female",
    "origin": "White",
    "location": "Freiburg, Germany",
    "university": "University of Freiburg",
    "email": "hannah.keller@example.com",
    "phone": "+49 170 24242424"
  },
  {
    "name": "Nina Bauer",
    "gender": "Female",
    "origin": "White",
    "location": "Regensburg, Germany",
    "university": "University of Regensburg",
    "email": "nina.bauer@example.com",
    "phone": "+49 171 25252525"
  },
  {
    "name": "Leila Haddad",
    "gender": "Female",
    "origin": "Middle Eastern",
    "location": "Mannheim, Germany",
    "university": "University of Mannheim",
    "email": "leila.haddad@example.com",
    "phone": "+49 160 26262626"
  },
  {
    "name": "Camila Rodriguez",
    "gender": "Female",
    "origin": "Latin American",
    "location": "Kiel, Germany",
    "university": "University of Kiel",
    "email": "camila.rodriguez@example.com",
    "phone": "+49 175 27272727"
  },
  {
    "name": "Arjun Malhotra",
    "gender": "Male",
    "origin": "Asian",
    "location": "Ulm, Germany",
    "university": "Ulm University",
    "email": "arjun.malhotra@example.com",
    "phone": "+49 151 28282828"
  },
  {
    "name": "Wei Chen",
    "gender": "Male",
    "origin": "Asian",
    "location": "Potsdam, Germany",
    "university": "University of Potsdam",
    "email": "wei.chen@example.com",
    "phone": "+49 152 29292929"
  },
  {
    "name": "Jonas Krüger",
    "gender": "Male",
    "origin": "White",
    "location": "Magdeburg, Germany",
    "university": "Otto von Guericke University Magdeburg",
    "email": "jonas.krueger@example.com",
    "phone": "+49 170 30303030"
  },
  {
    "name": "Sebastian Lang",
    "gender": "Male",
    "origin": "White",
    "location": "Jena, Germany",
    "university": "University of Jena",
    "email": "sebastian.lang@example.com",
    "phone": "+49 171 31313131"
  },
  {
    "name": "Youssef Benali",
    "gender": "Male",
    "origin": "Middle Eastern",
    "location": "Osnabrück, Germany",
    "university": "University of Osnabrück",
    "email": "youssef.benali@example.com",
    "phone": "+49 160 32323232"
  },
  {
    "name": "Lucas Pereira",
    "gender": "Male",
    "origin": "Latin American",
    "location": "Erfurt, Germany",
    "university": "University of Erfurt",
    "email": "lucas.pereira@example.com",
    "phone": "+49 175 33333333"
  }
]

COMPANY_POOL = [
    "SAP", "Siemens", "Allianz", "BMW", "Mercedes-Benz", "Volkswagen", "Deutsche Bank", 
    "Adidas", "Puma", "BASF", "Bayer", "Merck", "Deutsche Telekom", "E.ON", "Infineon", 
    "Zalando", "HelloFresh", "N26", "Delivery Hero", "Personio", "Celonis", "Trade Republic", 
    "Gorillas", "Flink", "Auto1", "Trivago", "Xing", "Soundcloud", "Babbel", "Tier", 
    "Voi", "Lilium", "Volocopter", "FlixBus", "Lufthansa", "Airbus", "Bosch", 
    "Continental", "Henkel", "Beiersdorf", "Audi", "Porsche", "DHL", "Commerzbank",
    "Munich Re", "RWE", "ThyssenKrupp", "HeidelbergCement", "Fresenius", "Covestro"
]

def get_random_theme():
    """Generates a random design theme for Resume and Cover Letter."""
    colors_list = [
        colors.darkblue, colors.darkslategray, colors.black, colors.darkgreen, 
        colors.darkred, colors.navy, colors.midnightblue, colors.teal,
        colors.firebrick, colors.seagreen, colors.indigo, colors.dimgray,
        colors.brown, colors.purple, colors.darkorange
    ]
    fonts_list = ['Helvetica-Bold', 'Times-Bold', 'Courier-Bold']
    
    return {
        'resume_header_color': random.choice(colors_list),
        'resume_company_style': random.choice(['Italic', 'Bold']),
        'resume_name_font': random.choice(['Helvetica-Bold', 'Times-Bold']),
        'resume_name_alignment': random.choice([0, 1]), # 0=Left, 1=Center
        'resume_header_case': random.choice(['UPPER', 'Title']), # UPPER or Title Case
        'cl_header_alignment': random.choice([0, 1]), # 0=Left, 1=Center
        'cl_header_font': random.choice(fonts_list),
        'cl_header_color': random.choice(colors_list)
    }



def generate_demographic_data(n: int, client) -> List[Dict]:
    candidates = STATIC_CANDIDATES

    females = [c for c in candidates if c['gender'] == 'Female']
    males = [c for c in candidates if c['gender'] == 'Male']

    def get_by_origin(pool, target_origins, limit):
        matches = [c for c in pool if c['origin'] in target_origins]
        return random.sample(matches, min(limit, len(matches)))

    selected = []

    # Females
    selected.extend(get_by_origin(females, ['Asian'], 2))
    selected.extend(get_by_origin(females, ['White'], 2))
    selected.extend(get_by_origin(
        females,
        ['Middle Eastern', 'African', 'Latin American'],
        2
    ))

    # Males
    selected.extend(get_by_origin(males, ['Asian'], 2))
    selected.extend(get_by_origin(males, ['White'], 2))
    selected.extend(get_by_origin(
        males,
        ['Middle Eastern', 'African', 'Latin American'],
        2
    ))

    # Fallback if needed
    if len(selected) < 12:
        remaining = [c for c in candidates if c not in selected]
        needed = 12 - len(selected)
        selected.extend(random.sample(remaining, min(needed, len(remaining))))

    return selected

def generate_resume_content(candidate: Dict, job_description: str, education_level: str, graduation_year: int, client) -> Dict:
    # Language Rule: Check if German is explicitly mentioned in JD (case-insensitive)
    include_german = "german" in job_description.lower()
    
    language_instruction = ""
    if include_german:
        language_instruction = "7. Languages: Include **German (C1)** and **English (C1/Fluent)**."
    else:
        language_instruction = "7. Languages: DO NOT include German. Only include English and other relevant languages if applicable (but NO German unless requested in JD)."

    # Company injection
    suggested_companies = ", ".join(random.sample(COMPANY_POOL, 8))

    # Origin context for diversity-aware generation
    origin_context = candidate.get('origin', 'General')
    
    prompt = f"""
    You are an expert ATS-optimized resume writer specializing in the job market.
    Generate professional, dense, and high-quality resume content for {candidate['name']} aiming for a one-page professional standard.
    
    Candidate Context:
    - Location: {candidate['location']}
    - Dynamic Context (Origin): {origin_context}. (Use to subtly inform style if relevant, but keep professional).
    - Education: {education_level} from {candidate['university']}.
    - Graduation Year: {graduation_year} (All dates should align with this).
    - Experience: EXACTLY 4 meaningful internships/work experiences relevant to the job.
      **Ensure all internship dates are structured chronologically, ending before or in {graduation_year}.**
    
    Job Description:
    {job_description}
    
    Strict Writing Rules:
    1. **REAL COMPANIES ONLY**: All companies listed in experience MUST be real, existing companies.
       - Use companies of a **similar market level/ranking**.
       - Suggested companies to draw from (or use similar): {suggested_companies}.
       - Do NOT use fictional names like "TechSolutions Inc". Use real names relevant to the location/industry.
    2. **CONSISTENT EXPERIENCE LEVEL**: Experience level/seniority must be comparable (4 internships/working student roles).
    3. **ATS Optimization**: Keywords must match the JD.
    4. Each **internship/work experience** must contain **3–4 achievement-focused bullet points**.
    5. Each **project** must be HIGHLY RELEVANT to the Job Description with a **3–4 line technical description**.
    6. Maintain a concise **one-page density**.
    {language_instruction}
    8. **Sections**: Contact, Summary, Education, Experience, Projects, Skills, Certificates, Languages.
    
    Output Format (JSON):
    {{
    "contact": {{ "email": "email_address", "phone": "phone_number" }},
    "summary": "3–4 line ATS-optimized professional summary tailored to the job.",
    "education": {{
        "degree": "{education_level}",
        "university": "{candidate['university']}",
        "year": "{graduation_year}",
        "details": "Relevant coursework or specialization"
    }},
    "experience": [
        {{
            "company": "Real Company Name 1",
            "role": "Role 1",
            "duration": "Dates",
            "description": ["Bullet 1", "Bullet 2", "Bullet 3"]
        }},
        {{
            "company": "Real Company Name 2",
            "role": "Role 2",
            "duration": "Dates",
            "description": ["..."]
        }},
        {{
            "company": "Real Company Name 3",
            "role": "Role 3",
            "duration": "Dates",
            "description": ["..."]
        }},
        {{
            "company": "Real Company Name 4",
            "role": "Role 4",
            "duration": "Dates",
            "description": ["..."]
        }}
    ],
    "projects": [
        {{
            "title": "Project 1",
            "description": ["Line 1", "Line 2", "Line 3", "Line 4"]
        }},
        {{
            "title": "Project 2",
            "description": ["Line 1", "Line 2", "Line 3"]
        }},
        {{
            "title": "Project 3",
            "description": ["Line 1", "Line 2", "Line 3", "Line 4"]
        }},
        {{
            "title": "Project 4",
            "description": ["Line 1", "Line 2", "Line 3"]
        }}
    ],
    "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5", "Skill 6", "Skill 7", "Skill 8"],
    "certificates": ["Certification 1", "Certification 2"],
    "languages": ["Language 1", "Language 2"]
    }}
    9. TEMPLATE VARIATION & FORMATTING:
- Each generated resume must follow a VISUALLY DISTINCT formatting template style.
- You MAY use **HTML tags** for formatting within the text strings:
  • Use <b>text</b> for bold (e.g., <b>Company Name</b>).
  • Use <i>text</i> for italics (e.g., <i>Role Title</i>).
  • DO NOT use Markdown (like ** or _). Use ONLY <b> and <i> tags.
  
- Vary formatting elements such as:
  • Company names in <b>bold</b>.
  • Role titles in <i>italics</i>.
  • Section headers in ALL CAPS or Title Case.
  • Use different separator styles (|, •, —).
  
- IMPORTANT:
  • JSON structure must remain EXACTLY the same.
  • Formatting tags (<bold>, <italic>) should appear ONLY inside string values.
  • Maintain ATS compatibility.



    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an expert resume writer."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        print(f"Error generating resume for {candidate['name']}: {e}")
        return {}

def generate_cover_letter_content(candidate: Dict, resume_data: Dict, job_description: str, education_level: str, client) -> str:
    company1 = resume_data.get('experience', [{}])[0].get('company', 'Unknown')
    
    prompt = f"""
    Write a highly professional, full one-page cover letter for {candidate['name']} applying for the given role.

CRITICAL OUTPUT RULES (MANDATORY):
1. START DIRECTLY with a formal salutation such as:
   "Respected Hiring Manager," or "Dear Hiring Manager,"
2. DO NOT include any header, personal details, address, email, phone number, or date.
3. DO NOT use placeholders such as "[Your Name]", "[Company Name]", or "[Date]".
4. DO NOT include meta-comments, explanations, or notes of any kind.
5. The output must read as a COMPLETE, FINAL cover letter ready for submission.

LENGTH & STRUCTURE REQUIREMENTS:
- The cover letter must be approximately ONE FULL PAGE (900-1000 words).
- Use clear professional paragraphing:
  • Opening paragraph: role interest + alignment with company
  • 2–3 body paragraphs: skills, impact, experience, and value
  • Closing paragraph: motivation, availability, and professional sign-off
- Maintain strong logical flow and business clarity.
- Avoid bullet points; use polished paragraph prose.

CONTEXT (MUST BE EXPLICITLY USED):
- Candidate Name: {candidate['name']}

- Education: {education_level} from {candidate['university']}  
  (Explicitly mention the degree level in a professional academic context.)
- Professional Experience:
  • Highlight relevant responsibilities, achievements, and impact at {company1}.
- Adapt skills, tools, and experience strictly based on the Job Description below.

LANGUAGE & TONE:
- Tone must be formal, persuasive, and aligned with German corporate communication standards.
- Confident but not exaggerated; factual, precise, and impact-driven.
- **DO NOT MENTION LANGUAGE SKILLS**. Do not say "I speak English" or "I speak German". Focus ONLY on technical/domain skills.

JOB DESCRIPTION (PRIMARY SOURCE OF TRUTH):
{job_description}

END REQUIREMENT:
- End with a professional closing sentence suitable for German business culture
  (e.g., expressing interest in further discussion).


    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a professional career coach."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating cover letter for {candidate['name']}: {e}")
        return "Error generating cover letter."

def process_single_candidate(candidate: Dict, job_description: str, education_level: str, graduation_year: int, client) -> Tuple[Dict, Dict, str, Dict]:
    """
    Process a single candidate to generate both resume and cover letter content.
    """
    theme = get_random_theme()
    resume_data = generate_resume_content(candidate, job_description, education_level, graduation_year, client)
    
    # Overwrite/Ensure contact info comes from the static candidate data
    if 'contact' not in resume_data:
        resume_data['contact'] = {}
    
    resume_data['contact']['email'] = candidate.get('email', resume_data['contact'].get('email'))
    resume_data['contact']['phone'] = candidate.get('phone', resume_data['contact'].get('phone'))
    
    cl_content = generate_cover_letter_content(candidate, resume_data, job_description, education_level, client)
    return candidate, resume_data, cl_content, theme

def create_resume_pdf(candidate: Dict, data: Dict, theme: Dict) -> bytes:
    buffer = io.BytesIO()
    # Reduce margins to fit more on one page
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='JobTitle', parent=styles['Heading2'], spaceAfter=1, fontSize=11, leading=13))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=12, spaceAfter=4, spaceBefore=6, textColor=theme['resume_header_color']))
    styles.add(ParagraphStyle(name='NormalSmall', parent=styles['Normal'], fontSize=9, leading=11))
    styles.add(ParagraphStyle(name='Date', parent=styles['Normal'], fontSize=8, textColor=colors.gray))
    
    story = []
    
    # Header
    name_style = ParagraphStyle(
        name='NameHeader', 
        parent=styles['Heading1'], 
        fontName=theme['resume_name_font'],
        alignment=theme['resume_name_alignment']
    )
    story.append(Paragraph(candidate['name'], name_style))
    # Contact info: Email | Phone (No location if user doesn't want address here, but Resume usually has it. 
    # User said "remove proving adress in cover letter", didn't explicitly remove from Resume, but I'll stick to Email/Phone/City for Resume to look pro)
    contact_info = f"{data.get('contact', {}).get('email', '')} | {data.get('contact', {}).get('phone', '')} | {candidate['location']}"
    story.append(Paragraph(contact_info, styles['NormalSmall']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=8))
    
    # Summary
    if 'summary' in data:
        header_text = "PROFESSIONAL SUMMARY" if theme.get('resume_header_case') == 'UPPER' else "Professional Summary"
        story.append(Paragraph(header_text, styles['SectionHeader']))
        story.append(Paragraph(data['summary'], styles['NormalSmall']))
    
    # Experience
    if 'experience' in data:
        header_text = "PROFESSIONAL EXPERIENCE" if theme.get('resume_header_case') == 'UPPER' else "Professional Experience"
        story.append(Paragraph(header_text, styles['SectionHeader']))
        for job in data['experience']:
            company_style = f"<i>{job.get('company', 'Company')}</i>" if theme['resume_company_style'] == 'Italic' else f"<b>{job.get('company', 'Company')}</b>"
            story.append(Paragraph(f"<b>{job.get('role', 'Role')}</b> at {company_style}", styles['NormalSmall']))
            story.append(Paragraph(f"{job.get('duration', '')}", styles['Date']))
            
            desc = job.get('description', [])
            if isinstance(desc, list):
                for item in desc:
                    story.append(Paragraph(f"• {clean_text_formatting(item)}", styles['NormalSmall']))
            else:
                story.append(Paragraph(clean_text_formatting(str(desc)), styles['NormalSmall']))
            story.append(Spacer(1, 4))
    
    # Projects
    if 'projects' in data:
        header_text = "KEY PROJECTS" if theme.get('resume_header_case') == 'UPPER' else "Key Projects"
        story.append(Paragraph(header_text, styles['SectionHeader']))
        for proj in data['projects']:
            # Title: Description
            # Handle user provided format which is a list of strings in description
            desc_text = ""
            if isinstance(proj.get('description'), list):
                 desc_text = "<br/>".join([f"• {clean_text_formatting(line)}" for line in proj['description']])
            else:
                 desc_text = clean_text_formatting(proj.get('description', ''))
                 
            text = f"<b>{proj.get('title', 'Project')}</b>:<br/>{desc_text}"
            story.append(Paragraph(text, styles['NormalSmall']))
            story.append(Spacer(1, 2))

    # Education
    if 'education' in data:
        header_text = "EDUCATION" if theme.get('resume_header_case') == 'UPPER' else "Education"
        story.append(Paragraph(header_text, styles['SectionHeader']))
        edu = data['education']
        story.append(Paragraph(f"<b>{edu.get('degree', 'Degree')}</b>", styles['NormalSmall']))
        story.append(Paragraph(f"{edu.get('university', 'University')} | {edu.get('year', '')}", styles['Date']))
        if 'details' in edu:
            story.append(Paragraph(edu['details'], styles['NormalSmall']))
        
    # Skills & Certificates
    if 'skills' in data or 'certificates' in data:
        header_text = "SKILLS & CERTIFICATES" if theme.get('resume_header_case') == 'UPPER' else "Skills & Certificates"
        story.append(Paragraph(header_text, styles['SectionHeader']))
        if 'skills' in data:
            skills_str = "<b>Skills:</b> " + ", ".join(data['skills'])
            story.append(Paragraph(skills_str, styles['NormalSmall']))
        if 'certificates' in data:
            cert_str = "<b>Certificates:</b> " + ", ".join(data['certificates'])
            story.append(Paragraph(cert_str, styles['NormalSmall']))
            
    # Languages
    if 'languages' in data:
        story.append(Spacer(1, 2))
        lang_str = "<b>Languages:</b> " + ", ".join(data['languages'])
        story.append(Paragraph(lang_str, styles['NormalSmall']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def create_cl_pdf(candidate: Dict, content: str, theme: Dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2.5*cm, leftMargin=2.5*cm, topMargin=2.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    
    story = []
    # Header: Name only. 
    header_style = ParagraphStyle(
        name='CLHeader', 
        parent=styles['Heading1'], 
        alignment=theme['cl_header_alignment'], 
        textColor=theme['cl_header_color'],
        fontName=theme['cl_header_font']
    )
    story.append(Paragraph(candidate['name'], header_style))
    story.append(Spacer(1, 10))
    
    # Date: Today's date
    current_date = datetime.now().strftime("%d.%m.%Y")
    story.append(Paragraph(f"Date: {current_date}", styles['Normal']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=20))

    for para in content.split('\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), styles['Normal']))
            story.append(Spacer(1, 6))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def batch_generate(job_description: str, count: int, education_level: str, graduation_year: int, client):
    """
    Orchestrates the full generation process using concurrent execution.
    """
    min_count = 2 # Minimum to ensure diversity logic works
    if count < min_count: count = min_count
    
    candidates = generate_demographic_data(count, client)
    if not candidates:
        return None
        
    results = []
    
    # Parallelize the full profile generation (Resume + CL)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_candidate, c, job_description, education_level, graduation_year, client) for c in candidates]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result() # returns (candidate, resume_data, cl_content, theme)
                results.append(res)
            except Exception as e:
                print(f"Job failed: {e}")

    # Create ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for cand, resume_data, cl_content, theme in results:
            safe_name = "".join([c for c in cand['name'] if c.isalpha() or c.isspace()]).strip().replace(" ", "_")
            
            # Enrich candidate with contact info for CL PDF if available
            if 'contact' in resume_data:
                cand['email'] = resume_data['contact'].get('email', '')
                cand['phone'] = resume_data['contact'].get('phone', '')

            # Resume
            try:
                resume_bytes = create_resume_pdf(cand, resume_data, theme)
                zf.writestr(f"Resumes/{safe_name}_Resume.pdf", resume_bytes)
            except Exception as e:
                print(f"Error creating resume PDF for {cand['name']}: {e}")

            # Cover Letter
            try:
                cl_bytes = create_cl_pdf(cand, cl_content, theme)
                zf.writestr(f"Cover_Letters/{safe_name}_CoverLetter.pdf", cl_bytes)
            except Exception as e:
                print(f"Error creating CL PDF for {cand['name']}: {e}")
            
    zip_buffer.seek(0)
    return zip_buffer
