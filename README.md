# 🎓 SLOG Solutions - AI Question Paper Generator

A robust, AI-powered web application built with Streamlit and Groq. This tool allows academic professionals to upload PDF study materials and automatically generate perfectly formatted, bilingual (English/Hindi) examination papers and answer keys.

## ✨ Features

* **Secure Authentication Portal:** A fully responsive, custom-styled login page to secure access to the generator.
* **Intelligent PDF Parsing:** Fast and accurate text extraction from uploaded study materials using `PyMuPDF`.
* **Advanced AI Generation:** Utilizes Groq's `llama-3.3-70b-versatile` model to generate context-aware academic questions.
* **Bilingual Output:** Automatically translates and formats questions in both English and Hindi.
* **Strict Section Ratios:** Enforces exact mathematical ratios for objective sections (e.g., exactly 30% MCQs, 30% True/False, 40% Fill-in-the-blanks).
* **Automated Word Document Creation:** Dynamically builds `.docx` files using `python-docx` complete with:
    * Custom headers (Max Marks, Subject Code, Branch, Semester).
    * Centered section headings.
    * Dynamic footers (Subject Code, dynamic Page Numbers, "P.T.O").
* **One-Click Downloads:** Instantly download both the Question Paper and Answer Key.

## 🛠️ Tech Stack

* **Frontend:** Streamlit, Custom CSS/HTML
* **Backend:** Python 3.11
* **AI/LLM Provider:** Groq API
* **PDF Processing:** PyMuPDF (`fitz`)
* **Document Generation:** `python-docx`
* **Deployment:** Render

## 🚀 Live Demo
*([](https://question-paper-generator-guxz.onrender.com/#e6df8a39))*
   Username : slogsolutions 
   Password : slog2026

---

## 💻 Local Setup & Installation

To run this project on your local machine, follow these steps:

**1. Clone the repository**
```bash
git clone [https://github.com/yourusername/slog-exam-generator.git](https://github.com/yourusername/slog-exam-generator.git)
cd slog-exam-generator

**2. Install dependencies**
Ensure you have Python 3.11+ installed. Run the following command:

Bash
pip install -r requirements.txt

**3. Set up Environment Variables**
Create a hidden folder and file for your API key:
Bash
mkdir .streamlit
touch .streamlit/secrets.toml
Open secrets.toml and add your Groq API Key:
Ini, TOML
GROQ_API_KEY = "gsk_your_api_key_here"

**4. Run the Application**
Bash
streamlit run app.py
☁️ Deployment on Render
This application is optimized for deployment on Render.

Create a new Web Service on Render and connect your GitHub repository.

Configure the following build settings:

Runtime: Python 3

Build Command: pip install -r requirements.txt

Start Command: streamlit run app.py --server.port $PORT --server.address 0.0.0.0

Under Environment Variables, add the following:

GROQ_API_KEY : Your actual Groq API Key

PYTHON_VERSION : 3.11.8 (Crucial to prevent PyMuPDF build errors)

Click Deploy.

📝 Usage Guide
Log in using the designated administrator credentials.

Fill out the "Paper Details" in the sidebar (Title, Branch, Semester, Subject Codes, etc.).

Configure the difficulty, total marks, and total questions for Sections A, B, and C.

Upload the source material as a .pdf file.

Click Generate Question Paper & Answer Key.

Wait for the AI to process and compile the documents.

Download your .docx files!
