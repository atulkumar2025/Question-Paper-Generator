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
   [Link](https://question-paper-generator-guxz.onrender.com/#e6df8a39)
   
   Username : slogsolutions 
   
   Password : slog2026
