import streamlit as st
import os
from utils import get_openai_client, batch_generate

# Configuration
st.set_page_config(page_title="Resume & Cover Letter Generator", layout="wide")

# Title and Intro
st.title("Synthetic Application Generator")
st.markdown("""
Generate **bulk professional resumes and cover letters** tailored to a specific job description.
The system automatically generates a diverse pool of candidates (50% White-origin, 50% Black-origin) based in Germany.
""")

# Sidebar settings

st.sidebar.header("Configuration")
# API Key is expected to be in .env or environment variables
if not os.getenv("OPENAI_API_KEY"):
    st.warning("⚠️ OPENAI_API_KEY not found in environment. Please set it in .env file.")

num_candidates = st.sidebar.number_input("Number of Candidates", min_value=2, max_value=12, value=12, step=1)
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
                zip_file = batch_generate(job_description, int(num_candidates), education_level, int(graduation_year), client)
                if zip_file:
                    st.session_state['generated_zip'] = zip_file
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

# Footer
st.markdown("---")
st.caption("Powered by OpenAI & ReportLab. Developed for synthetic data generation.")
