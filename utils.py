import os
import json
import zipfile
import io
import concurrent.futures
from typing import List, Dict, Tuple
import openai
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

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
    {"name": "Thomas Müller", "origin": "White", "location": "Berlin, Germany", "university": "TU Berlin", "email": "thomas.mueller@example.com", "phone": "+49 151 12345678"},
    {"name": "David Okafor", "origin": "Black", "location": "Munich, Germany", "university": "TU Munich", "email": "david.okafor@example.com", "phone": "+49 152 23456789"},
    {"name": "Julia Schmidt", "origin": "White", "location": "Hamburg, Germany", "university": "RWTH Aachen", "email": "julia.schmidt@example.com", "phone": "+49 170 34567890"},
    {"name": "Amina Tesfaye", "origin": "Black", "location": "Frankfurt, Germany", "university": "KIT Karlsruhe", "email": "amina.tesfaye@example.com", "phone": "+49 171 45678901"},
    {"name": "Lukas Weber", "origin": "White", "location": "Stuttgart, Germany", "university": "University of Stuttgart", "email": "lukas.weber@example.com", "phone": "+49 160 56789012"},
    {"name": "Samuel Adewale", "origin": "Black", "location": "Düsseldorf, Germany", "university": "TU Darmstadt", "email": "samuel.adewale@example.com", "phone": "+49 175 67890123"},
    {"name": "Sarah Wagner", "origin": "White", "location": "Cologne, Germany", "university": "TU Dresden", "email": "sarah.wagner@example.com", "phone": "+49 157 78901234"},
    {"name": "Grace Ndiaye", "origin": "Black", "location": "Leipzig, Germany", "university": "TU Berlin", "email": "grace.ndiaye@example.com", "phone": "+49 176 89012345"},
    {"name": "Maximilian Becker", "origin": "White", "location": "Hanover, Germany", "university": "Leibniz University Hannover", "email": "maximilian.becker@example.com", "phone": "+49 179 90123456"},
    {"name": "Michael Mensah", "origin": "Black", "location": "Nuremberg, Germany", "university": "FAU Erlangen-Nürnberg", "email": "michael.mensah@example.com", "phone": "+49 151 01234567"},
    {"name": "Laura Hoffmann", "origin": "White", "location": "Dresden, Germany", "university": "TU Dresden", "email": "laura.hoffmann@example.com", "phone": "+49 152 12345670"},
    {"name": "Esther Mwangi", "origin": "Black", "location": "Bonn, Germany", "university": "University of Bonn", "email": "esther.mwangi@example.com", "phone": "+49 170 23456781"},
    {"name": "Felix Koch", "origin": "White", "location": "Munich, Germany", "university": "TU Munich", "email": "felix.koch@example.com", "phone": "+49 171 34567892"},
    {"name": "Daniel Boateng", "origin": "Black", "location": "Berlin, Germany", "university": "TU Berlin", "email": "daniel.boateng@example.com", "phone": "+49 160 45678903"},
    {"name": "Anna Richter", "origin": "White", "location": "Hamburg, Germany", "university": "Hamburg University of Technology", "email": "anna.richter@example.com", "phone": "+49 175 56789014"}
]

def generate_demographic_data(n: int, client) -> List[Dict]:
    """
    Returns a slice of the static candidate list.
    """
    # Return available candidates, cycling if n > 15 (though UI limit is 50, but we only have 15 unique)
    # If user asks for more than 15, we'll just repeat or slice. 
    # User said "only defined 15", so we likely just max out at 15 or cycle.
    # Let's simple slice for now, if n > 15 we loop.
    import itertools
    
    if n <= len(STATIC_CANDIDATES):
        return STATIC_CANDIDATES[:n]
    
    # If more than 15 needed, cycle
    result = []
    cycle = itertools.cycle(STATIC_CANDIDATES)
    for _ in range(n):
        result.append(next(cycle))
    return result

def generate_resume_content(candidate: Dict, job_description: str, education_level: str, graduation_year: int, client) -> Dict:
    prompt = f"""
    You are an expert ATS-optimized resume writer specializing in the German job market.
    Generate professional, dense, and high-quality resume content for {candidate['name']} aiming for a one-page professional standard.
    
    Candidate Context:
    - Location: {candidate['location']}
    - Education: {education_level} from {candidate['university']}.
    - Graduation Year: {graduation_year} (All dates should align with this).
    - Experience: EXACTLY 4 meaningful internships/work experiences relevant to the job (e.g. Working Student, Intern, Thesis). 
      **Ensure all internship dates are structured chronologically, ending before or in {graduation_year}.**
    
    Job Description:
    {job_description}
    
    Strict Writing Rules:
    1. Resume must be optimized for **ATS keyword matching** based on the job description.
    2. Each **internship/work experience** must contain **3–4 achievement-focused bullet points**, each describing impact, tools used, and measurable outcomes where possible.
    3. Each **project** must be HIGHLY RELEVANT to the Job Description and include a **3–4 line technical description** explaining:
        - purpose/problem solved
        - technologies used (must match JD stack)
        - measurable results or impact
    4. Use varied wording and avoid repeating the same verbs or phrases across sections.
    5. Maintain a concise **one-page density** while remaining highly informative.
    6. Include professional certifications relevant to the job.
    7. Languages must include German and English with proficiency levels.
    8. **One Page Optimization**: Concise but high impact.
    9. **Sections**: Contact, Summary, Education, Experience, Projects, Skills, Certificates, Languages.
    
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
            "company": "Company 1",
            "role": "Role 1",
            "duration": "Dates",
            "description": [
                "Achievement-focused bullet point",
                "Achievement-focused bullet point",
                "Achievement-focused bullet point",
                "Achievement-focused bullet point"
            ]
        }},
        {{
            "company": "Company 2",
            "role": "Role 2",
            "duration": "Dates",
            "description": ["..."]
        }},
        {{
            "company": "Company 3",
            "role": "Role 3",
            "duration": "Dates",
            "description": ["..."]
        }},
        {{
            "company": "Company 4",
            "role": "Role 4",
            "duration": "Dates",
            "description": ["..."]
        }}
    ],
    "projects": [
        {{
            "title": "Project 1",
            "description": [
                "Line 1 describing objective",
                "Line 2 describing technical implementation",
                "Line 3 describing results or performance impact",
                "Line 4 describing tools/technologies"
            ]
        }},
        {{
            "title": "Project 2",
            "description": ["Line 1", "Line 2", "Line 3", "Line 4"]
        }},
        {{
            "title": "Project 3",
            "description": ["Line 1", "Line 2", "Line 3", "Line 4"]
        }},
        {{
            "title": "Project 4",
            "description": ["Line 1", "Line 2", "Line 3", "Line 4"]
        }}
    ],
    "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5", "Skill 6", "Skill 7", "Skill 8"],
    "certificates": ["Certification 1", "Certification 2"],
    "languages": ["German (B2/C1)", "English (C1/C2)"]
    }}
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

def generate_cover_letter_content(candidate: Dict, resume_data: Dict, job_description: str, client) -> str:
    company1 = resume_data.get('experience', [{}])[0].get('company', 'Unknown')
    
    prompt = f"""
    Write a formal cover letter for {candidate['name']} applying for the job.
    
    CRITICAL RESTRICTION: 
    - **DO NOT** include the candidate's physical address or location in the header or closure.
    - **ONLY** include Phone Number and Email Address in the signature/header area.
    
    Context:
    - Education from {candidate['university']}.
    - Highlight experience at {company1}.
    - Tone: Highly professional, persuasive, German business standards.
    
    Job Description:
    {job_description}
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

def process_single_candidate(candidate: Dict, job_description: str, education_level: str, graduation_year: int, client) -> Tuple[Dict, Dict, str]:
    """
    Process a single candidate to generate both resume and cover letter content.
    """
    resume_data = generate_resume_content(candidate, job_description, education_level, graduation_year, client)
    
    # Overwrite/Ensure contact info comes from the static candidate data
    if 'contact' not in resume_data:
        resume_data['contact'] = {}
    
    resume_data['contact']['email'] = candidate.get('email', resume_data['contact'].get('email'))
    resume_data['contact']['phone'] = candidate.get('phone', resume_data['contact'].get('phone'))
    
    cl_content = generate_cover_letter_content(candidate, resume_data, job_description, client)
    return candidate, resume_data, cl_content

def create_resume_pdf(candidate: Dict, data: Dict) -> bytes:
    buffer = io.BytesIO()
    # Reduce margins to fit more on one page
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='JobTitle', parent=styles['Heading2'], spaceAfter=1, fontSize=11, leading=13))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=12, spaceAfter=4, spaceBefore=6, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='NormalSmall', parent=styles['Normal'], fontSize=9, leading=11))
    styles.add(ParagraphStyle(name='Date', parent=styles['Normal'], fontSize=8, textColor=colors.gray))
    
    story = []
    
    # Header
    story.append(Paragraph(candidate['name'], styles['Heading1']))
    # Contact info: Email | Phone (No location if user doesn't want address here, but Resume usually has it. 
    # User said "remove proving adress in cover letter", didn't explicitly remove from Resume, but I'll stick to Email/Phone/City for Resume to look pro)
    contact_info = f"{data.get('contact', {}).get('email', '')} | {data.get('contact', {}).get('phone', '')} | {candidate['location']}"
    story.append(Paragraph(contact_info, styles['NormalSmall']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=8))
    
    # Summary
    if 'summary' in data:
        story.append(Paragraph("Professional Summary", styles['SectionHeader']))
        story.append(Paragraph(data['summary'], styles['NormalSmall']))
    
    # Experience
    if 'experience' in data:
        story.append(Paragraph("Professional Experience", styles['SectionHeader']))
        for job in data['experience']:
            story.append(Paragraph(f"<b>{job.get('role', 'Role')}</b> at {job.get('company', 'Company')}", styles['NormalSmall']))
            story.append(Paragraph(f"{job.get('duration', '')}", styles['Date']))
            
            desc = job.get('description', [])
            if isinstance(desc, list):
                for item in desc:
                    story.append(Paragraph(f"• {item}", styles['NormalSmall']))
            else:
                story.append(Paragraph(str(desc), styles['NormalSmall']))
            story.append(Spacer(1, 4))
    
    # Projects
    if 'projects' in data:
        story.append(Paragraph("Key Projects", styles['SectionHeader']))
        for proj in data['projects']:
            # Title: Description
            # Handle user provided format which is a list of strings in description
            desc_text = ""
            if isinstance(proj.get('description'), list):
                 desc_text = "<br/>".join([f"• {line}" for line in proj['description']])
            else:
                 desc_text = proj.get('description', '')
                 
            text = f"<b>{proj.get('title', 'Project')}</b>:<br/>{desc_text}"
            story.append(Paragraph(text, styles['NormalSmall']))
            story.append(Spacer(1, 2))

    # Education
    if 'education' in data:
        story.append(Paragraph("Education", styles['SectionHeader']))
        edu = data['education']
        story.append(Paragraph(f"<b>{edu.get('degree', 'Degree')}</b>", styles['NormalSmall']))
        story.append(Paragraph(f"{edu.get('university', 'University')} | {edu.get('year', '')}", styles['Date']))
        if 'details' in edu:
            story.append(Paragraph(edu['details'], styles['NormalSmall']))
        
    # Skills & Certificates
    if 'skills' in data or 'certificates' in data:
        story.append(Paragraph("Skills & Certificates", styles['SectionHeader']))
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

def create_cl_pdf(candidate: Dict, content: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2.5*cm, leftMargin=2.5*cm, topMargin=2.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    
    story = []
    # Header: Name, Phone, Email ONLY. No Location.
    story.append(Paragraph(candidate['name'], styles['Heading1']))
    story.append(Spacer(1, 20))
    
    if 'email' in candidate and 'phone' in candidate:
         items = f"{candidate['email']} | {candidate['phone']}"
         story.append(Paragraph(items, styles['Normal']))
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
                res = future.result() # returns (candidate, resume_data, cl_content)
                results.append(res)
            except Exception as e:
                print(f"Job failed: {e}")

    # Create ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for cand, resume_data, cl_content in results:
            safe_name = "".join([c for c in cand['name'] if c.isalpha() or c.isspace()]).strip().replace(" ", "_")
            
            # Enrich candidate with contact info for CL PDF if available
            if 'contact' in resume_data:
                cand['email'] = resume_data['contact'].get('email', '')
                cand['phone'] = resume_data['contact'].get('phone', '')

            # Resume
            try:
                resume_bytes = create_resume_pdf(cand, resume_data)
                zf.writestr(f"Resumes/{safe_name}_Resume.pdf", resume_bytes)
            except Exception as e:
                print(f"Error creating resume PDF for {cand['name']}: {e}")

            # Cover Letter
            try:
                cl_bytes = create_cl_pdf(cand, cl_content)
                zf.writestr(f"Cover_Letters/{safe_name}_CoverLetter.pdf", cl_bytes)
            except Exception as e:
                print(f"Error creating CL PDF for {cand['name']}: {e}")
            
    zip_buffer.seek(0)
    return zip_buffer
