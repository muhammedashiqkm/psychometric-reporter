import pdfkit
import os
import re
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings
from app.models.psychometric import StudentDetailsInput, AIAnalysisResult, ProcessedTest

REPORTS_DIR = "media/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

env = Environment(loader=FileSystemLoader("app/templates"))

def sanitize_filename_part(text: str) -> str:
    """Removes special characters and replaces spaces with underscores."""
    if not text:
        return "Unknown"
    return re.sub(r'[^a-zA-Z0-9]', '_', text.strip().replace(' ', '_'))

def generate_pdf(student: StudentDetailsInput, tests: list[ProcessedTest], ai_result: AIAnalysisResult) -> tuple[str, str]:
    """
    Renders the HTML template and converts it to PDF.
    Returns: (filename, report_url)
    """
    template = env.get_template("report_template.html")

    student_context = {
        "student_name": student.student_name,
        "register_no": student.register_no,
        "programme": student.course_name if student.course_name else "N/A",
        "institution": student.institution,
        "batch": student.batch if student.batch else "N/A",
        "career_goal": "Software Professional" 
    }
    
    html_out = template.render(
        student=student_context,
        tests=tests,
        ai=ai_result,
        base_url=settings.BASE_URL
    )
    
    safe_name = sanitize_filename_part(student.student_name)
    safe_inst = sanitize_filename_part(student.institution)
    safe_reg = sanitize_filename_part(student.register_no)
    
    filename = f"{safe_name}_{safe_inst}_{safe_reg}.pdf"
    file_path = os.path.join(REPORTS_DIR, filename)
    
    options = {
        "page-size": "A4",
        "margin-top": "0.4in",
        "margin-right": "0.4in",
        "margin-bottom": "0.4in",
        "margin-left": "0.4in",
        "enable-local-file-access": ""
    }
    
    try:
        pdfkit.from_string(html_out, file_path, options=options)
    except OSError as e:
        if not os.path.exists(file_path):
            raise e
    
    report_url = f"{settings.BASE_URL}/media/reports/{filename}"
    
    return filename, report_url