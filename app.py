import streamlit as st
import fitz  # PyMuPDF
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.oxml import OxmlElement  # Needed for dynamic page numbers
from docx.oxml.ns import qn        # Needed for dynamic page numbers
from groq import Groq
import json
import io
import os

# --- 1. INITIAL SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if 'qp_bytes' not in st.session_state:
    st.session_state.qp_bytes = None
    st.session_state.ak_bytes = None
    st.session_state.current_sub_code = ""

# --- 2. CONFIGURATION (Groq) ---
# Check Render's Environment Variables first, then check local secrets
api_key = os.environ.get("GROQ_API_KEY")

# If it's not in the OS environment, try Streamlit's local secrets file
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (FileNotFoundError, KeyError):
        api_key = None

if api_key:
    client = Groq(api_key=api_key)
else:
    # We only show this error if the user is logged in
    if st.session_state.logged_in:
        st.error("Please add GROQ_API_KEY to Render Environment Variables or secrets.toml")
        st.stop()

GROQ_MODEL = "llama-3.3-70b-versatile"

# --- 3. UTILITY FUNCTIONS ---
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    return text

def get_llm_response(raw_text, config):
    # Calculate exact question counts for Section A based on the 30/30/40 ratio
    total_a = config['total_a']
    num_mcq = int(round(total_a * 0.30))    # 30% MCQs
    num_tf = int(round(total_a * 0.30))     # 30% True/False
    num_fill = total_a - num_mcq - num_tf   # 40% Fill-ups (math ensures the total is exact)

    prompt = f"""
    Act as an academic expert and exam controller. Based on this source material: {raw_text[:15000]}
    
    Create a professional bilingual examination paper:
    - Subject: {config['subject_name']} ({config['subject_code']})
    - Branch: {config['branch_name']}
    
    Section Requirements:
    1. Section A: Generate exactly {total_a} questions. 
       - EXACT BREAKDOWN: Generate {num_mcq} MCQs, {num_fill} Fill-in-the-blanks, and {num_tf} True/False questions.
       - Students will attempt {config['n_a']}. Difficulty: {config['diff_a']}.
       
    2. Section B: Generate exactly {config['total_b']} questions. 
       - Short answer types. Students attempt {config['n_b']}. Difficulty: {config['diff_b']}.
       
    3. Section C: Generate exactly {config['total_c']} questions. 
       - Long answer/descriptive types. Students attempt {config['n_c']}. Difficulty: {config['diff_c']}.
    
    CRITICAL RULES:
    - Every question ("q") must be bilingual: [English Question] / [Hindi Translation].
    - Every answer ("a") must be clear and accurate.
    - Return ONLY a valid JSON object.
    
    JSON Structure:
    {{
        "section_a": [{{"q": "Q Text / प्रश्न", "a": "Ans Text"}}, ...],
        "section_b": [{{"q": "Q Text / प्रश्न", "a": "Ans Text"}}, ...],
        "section_c": [{{"q": "Q Text / प्रश्न", "a": "Ans Text"}}, ...]
    }}
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert exam generator that outputs only JSON."},
            {"role": "user", "content": prompt}
        ],
        model=GROQ_MODEL,
        response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)

def create_word_files(data, config):
    def add_header(doc, is_ans=False):
        p_mm = doc.add_paragraph()
        p_mm.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_mm.add_run(f"Μ.Μ.: {config['total_marks']}").bold = True
        
        title_text = f"Answer Key: {config['title']}" if is_ans else config['title']
        h = doc.add_heading(title_text, 0)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        details = [
            f"Branch Name: {config['branch_name']} ({config['branch_code']})",
            f"Semester: {config['sem']} | Subject: {config['subject_name']} ({config['subject_code']})",
            f"Time: {config['duration']}"
        ]
        for line in details:
            p = doc.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("_" * 40).alignment = WD_ALIGN_PARAGRAPH.CENTER

    def add_custom_footer(doc, sub_code):
        # Access the footer of the document
        section = doc.sections[0]
        footer = section.footer
        p = footer.paragraphs[0]
        
        # Word's default footer style has a center tab and a right tab
        p.text = f"{sub_code}\tPage "
        
        # Add dynamic Page Number XML
        run = p.add_run()
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'separate')
        fldChar3 = OxmlElement('w:fldChar')
        fldChar3.set(qn('w:fldCharType'), 'end')
        run._r.extend([fldChar1, instrText, fldChar2, fldChar3])
        

    # --- 1. Generate Question Paper ---
    q_doc = Document()
    add_header(q_doc)
    
    sections = [("A / भाग - क", "section_a", config['n_a'], config['m_a']),
                ("B / भाग - ख", "section_b", config['n_b'], config['m_b']),
                ("C / भाग - ग", "section_c", config['n_c'], config['m_c'])]
    
    for label, key, req_count, sec_marks in sections:
        # Create heading and center it
        h = q_doc.add_heading(f"SECTION-{label}", level=1)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        q_doc.add_paragraph(f"Note: Attempt any {req_count} questions. (Total Marks: {sec_marks})").italic = True
        for i, item in enumerate(data[key], 1):
            q_doc.add_paragraph(f"{i}. {item['q']}", style='List Number')
            
    add_custom_footer(q_doc, config['subject_code'])

    # --- 2. Generate Answer Key ---
    a_doc = Document()
    add_header(a_doc, is_ans=True)
    for label, key, _, _ in sections:
        # Create heading and center it
        h = a_doc.add_heading(f"Answers: SECTION-{label}", level=1)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        for i, item in enumerate(data[key], 1):
            p = a_doc.add_paragraph()
            p.add_run(f"Q{i}: ").bold = True
            p.add_run(item['q'])
            a_doc.add_paragraph(f"Ans: {item['a']}")
            
    add_custom_footer(a_doc, config['subject_code'])
    
    return q_doc, a_doc

# --- 4. LOGIN PAGE LOGIC ---
if not st.session_state.logged_in:
    st.set_page_config(page_title="Login | SLOG AI", page_icon="🔐", layout="centered")
    
    st.markdown("""
        <style>
        /* Global Background */
        .stApp { background-color: #f8fafc !important; }
        #MainMenu, footer, header {visibility: hidden;}

        /* Main Card Container */
        div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
            background-color: white !important;
            border-radius: 20px !important;
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.05) !important;
            padding: 40px !important;
            max-width: 900px !important;
            margin: 5vh auto !important;
            gap: 3rem !important; /* Forces a safe space between the form and image */
            align-items: center !important;
        }

        /* Responsive Title */
        .main-title {
            font-size: clamp(1.5rem, 4vw, 2rem); /* Shrinks automatically on small screens */
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 2rem;
            line-height: 1.2;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }

        /* Clean Inputs */
        .stTextInput input {
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 14px 16px !important;
            font-size: 1rem !important;
            background-color: #f8fafc !important;
            color: #334155 !important;
        }
        .stTextInput input:focus {
            border-color: #f59e0b !important;
            box-shadow: 0 0 0 2px rgba(245,158,11,0.1) !important;
            background-color: white !important;
        }

        /* Yellow Sign In Button */
        div[data-testid="stFormSubmitButton"] { width: 100% !important; }
        div[data-testid="stFormSubmitButton"] > button {
            width: 100% !important;
            background-color: #f59e0b !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 14px !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            margin-top: 10px !important;
            transition: 0.2s;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #d97706 !important;
            transform: translateY(-1px);
        }

        /* Remove form default borders */
        div[data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background-color: transparent !important;
        }

        /* Checkbox */
        label[data-baseweb="checkbox"] { color: #64748b !important; font-weight: 500 !important; }
        
        /* Forgot Password Link */
        .forgot-pass-link {
            display: block;
            text-align: center;
            color: #0284c7; /* Blue color matching your screenshot */
            font-weight: 600;
            font-size: 0.95rem;
            text-decoration: none;
            margin-top: 20px;
            transition: 0.2s;
        }
        .forgot-pass-link:hover { color: #0369a1; text-decoration: underline; }

        /* Handle stacking cleanly on mobile/narrow windows */
        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
                padding: 25px !important;
                gap: 2rem !important;
            }
            .main-title { text-align: center; }
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1])
    
    with col1:
        st.markdown('<div class="main-title">SIGN IN TO YOUR ACCOUNT</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("<div style='font-weight: 600; color: #475569; margin-bottom: 6px; font-size: 0.95rem;'>Email</div>", unsafe_allow_html=True)
            username = st.text_input("Email", placeholder="example@email.com", label_visibility="collapsed")
            
            st.markdown("<div style='font-weight: 600; color: #475569; margin-bottom: 6px; margin-top: 15px; font-size: 0.95rem;'>Password</div>", unsafe_allow_html=True)
            password = st.text_input("Password", type="password", placeholder="Min. 8 characters", label_visibility="collapsed")
            
            st.write("") 
            remember = st.checkbox("Remember me", value=True)
            
            submit = st.form_submit_button("SIGN IN")
            if submit:
                if username == "admin" and password == "slog2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
                    
        # Placed securely outside the form
        st.markdown("<a href='#' class='forgot-pass-link'>Forgot password?</a>", unsafe_allow_html=True)

    with col2:
        # Responsive image sizing using max-width and aspect-ratio
        html_content = """
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
    <img src="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?q=80&w=600&auto=format&fit=crop" 
         style="width: 100%; max-width: 280px; aspect-ratio: 4/5; object-fit: cover; border-radius: 16px; box-shadow: 0 15px 30px rgba(0,0,0,0.15); margin-bottom: 30px;">
    <p style="font-size: 1.15rem; color: #475569; font-weight: 700; margin-bottom: 4px;">Learn and Grow Every Day</p>
    <p style="font-size: 0.95rem; color: #94a3b8; font-weight: 500; margin: 0;">Powered by SLOG Solutions</p>
</div>
"""
        st.markdown(html_content, unsafe_allow_html=True)

else:
    # --- 5. MAIN APP UI ---
    # (Your generator code)
    st.set_page_config(page_title="Question Gen AI", layout="wide")
    
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.header("📌 Paper Details")
        title = st.text_input("Title", "")
        branch = st.text_input("Branch Name", "")
        b_code = st.text_input("Branch Code", "")
        sem = st.text_input("Semester", "")
        sub_name = st.text_input("Subject Name", "")
        sub_code = st.text_input("Subject Code", "")
        duration = st.text_input("Duration(Hrs)", "")

    st.title("🎓 Question Paper & Answer Key Generator")
    st.subheader("Powered by SLOG Solutions")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Section A/ भाग - क")
        n_a = st.number_input("Questions to Attempt", 1, 30, 10, key="n_a_input")
        m_a = st.number_input("Section Marks", 1, 100, 10, key="m_a_input")
        total_a = st.number_input("Total Questions", n_a, n_a+10, n_a+2, key="t_a_input")
        diff_a = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], key="d_a_input")

    with col2:
        st.markdown("### Section B/ भाग - ख")
        n_b = st.number_input("Questions to Attempt", 1, 30, 5, key="n_b_input")
        m_b = st.number_input("Section Marks", 1, 100, 15, key="m_b_input")
        total_b = st.number_input("Total Questions", n_b, n_b+10, n_b+2, key="t_b_input")
        diff_b = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1, key="d_b_input")

    with col3:
        st.markdown("### Section C/ भाग - ग")
        n_c = st.number_input("Questions to Attempt", 1, 30, 5, key="n_c_input")
        m_c = st.number_input("Section Marks", 1, 100, 25, key="m_c_input")
        total_c = st.number_input("Total Questions", n_c, n_c+10, n_c+2, key="t_c_input")
        diff_c = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=2, key="d_c_input")

    st.divider()
    uploaded_file = st.file_uploader("Upload Study Material (PDF)", type="pdf")

    if st.button("🚀 Generate Question Paper & Answer Key") and uploaded_file:
        with st.status("AI is working...", expanded=True) as status:
            st.write("Reading PDF content...")
            raw_text = extract_text_from_pdf(uploaded_file)
            
            config = {
                "title": title, "branch_name": branch, "branch_code": b_code,
                "sem": sem, "subject_name": sub_name, "subject_code": sub_code,
                "duration": duration, "total_marks": m_a + m_b + m_c,
                "n_a": n_a, "m_a": m_a, "total_a": total_a, "diff_a": diff_a,
                "n_b": n_b, "m_b": m_b, "total_b": total_b, "diff_b": diff_b,
                "n_c": n_c, "m_c": m_c, "total_c": total_c, "diff_c": diff_c
            }
            
            try:
                data = get_llm_response(raw_text, config)
                st.write("Creating Word documents...")
                q_doc, a_doc = create_word_files(data, config)
                
                q_buf, a_buf = io.BytesIO(), io.BytesIO()
                q_doc.save(q_buf)
                a_doc.save(a_buf)
                
                st.session_state.qp_bytes = q_buf.getvalue()
                st.session_state.ak_bytes = a_buf.getvalue()
                st.session_state.current_sub_code = sub_code
                status.update(label="Generation Complete!", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if st.session_state.qp_bytes is not None:
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 Download Question Paper", st.session_state.qp_bytes, f"QP_{st.session_state.current_sub_code}.docx")
        with c2:
            st.download_button("📥 Download Answer Key", st.session_state.ak_bytes, f"AK_{st.session_state.current_sub_code}.docx")
