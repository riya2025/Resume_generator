import streamlit as st
import os
from utils import get_openai_client, batch_generate, answer_screening_question

# Configuration
st.set_page_config(page_title="Resume & Cover Letter Generator", layout="wide")

# Title and Intro
st.title("Synthetic Application Generator")
st.markdown("""
Generate **bulk professional resumes and cover letters** tailored to a specific job description.

""")

# Sidebar settings

st.sidebar.header("Configuration")
# API Key is expected to be in .env or environment variables
if not os.getenv("OPENAI_API_KEY"):
    st.warning("⚠️ OPENAI_API_KEY not found in environment. Please set it in .env file.")

target_country = st.sidebar.selectbox("Target Country", ["Germany", "France", "Italy", "Netherlands", "Finland"])
num_candidates = st.sidebar.number_input("Number of Candidates", min_value=2, max_value=6, value=6, step=1)
education_level = st.sidebar.selectbox("Education Level", ["Master of Science in Computer Science", "Bachelor of Science in Computer Science"])
graduation_year = st.sidebar.number_input("Graduation Year", min_value=2020, max_value=2030, value=2025, step=1)

# Main UI
st.subheader("1. Job Description")
job_description = st.text_area(
    "Paste the Job Description here...",
    height=300,
    placeholder="e.g. Seeking a Senior Python Developer with experience in Django, AWS..."
)

st.subheader("2. Generation")
generate_btn = st.button(" Generate Resumes", type="primary")

if generate_btn:
    client = get_openai_client()
    if not client:
        st.error("❌ OpenAI API Key is missing. Please set provided input or environment variable.")
    elif not job_description.strip():
        st.error("❌ Please enter a Job Description.")
    else:
        with st.spinner(f"Creating {num_candidates} detailed candidate profiles... This may take a minute."):
            try:
                zip_file, candidates_data = batch_generate(job_description, int(num_candidates), education_level, int(graduation_year), target_country, client)
                if zip_file:
                    st.session_state['generated_zip'] = zip_file
                    st.session_state['candidates_data'] = candidates_data
                    st.success("✅ Generation Complete!")
                else:
                    st.error("Failed to generate candidates. Please check API quota or try again.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Display Download Button if data exists in session state
if 'generated_zip' in st.session_state:
    st.download_button(
        label="📥 Download All Resumes & Cover Letters (ZIP)",
        data=st.session_state['generated_zip'],
        file_name="generated_applications.zip",
        mime="application/zip"
    )

# Application Assistant Chatbot
if 'candidates_data' in st.session_state:
    st.markdown("---")
    st.subheader("3. Application Assistant")
    st.write("Answer screening questions (e.g. from Indeed) acting as one of the generated candidates.")
    
    candidates = st.session_state['candidates_data']
    candidate_names = [c[0]['name'] for c in candidates]
    
    selected_name = st.selectbox("Select Candidate Persona", candidate_names)
    selected_candidate_tuple = next(c for c in candidates if c[0]['name'] == selected_name)
    cand_dict, resume_data, _, _ = selected_candidate_tuple
    
    question = st.text_area("Screening Question", placeholder="e.g. How many years of experience do you have in Python?")
    
    if st.button("Generate Answer"):
        if not question.strip():
            st.error("Please enter a question.")
        else:
            client = get_openai_client()
            with st.spinner(f"Generating answer as {selected_name}..."):
                answer = answer_screening_question(cand_dict, resume_data, job_description, question, client)
                st.info(answer)

# Footer
st.markdown("---")
st.caption("Powered by OpenAI & ReportLab. Developed for synthetic data generation.")
