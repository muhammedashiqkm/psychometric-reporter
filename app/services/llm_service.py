import json
import google.generativeai as genai
from openai import AsyncOpenAI
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging_config import app_logger
from app.models.psychometric import (
    StudentDetailsInput,
    AIAnalysisResult,
    ProcessedTest,
)
from app.services.chart_factory import ChartFactory


if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
else:
    gemini_model = None

openai_client = None
if settings.OPENAI_API_KEY:
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

deepseek_client = None
if settings.DEEPSEEK_API_KEY:
    deepseek_client = AsyncOpenAI(
        api_key=settings.DEEPSEEK_API_KEY, 
        base_url="https://api.deepseek.com"
    )


async def _get_llm_response(prompt: str, model_provider: str) -> str:
    """
    Centralized helper to call the appropriate LLM provider.
    - model_provider: 'gemini', 'openai', or 'deepseek' (from request)
    - model_name: Fetched from settings (env)
    """
    try:
        if model_provider == "gemini":
            if not gemini_model:
                raise ValueError("Gemini API Key missing or client not initialized.")
            
            response = await gemini_model.generate_content_async(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text

        elif model_provider == "openai":
            if not openai_client:
                raise ValueError("OpenAI API Key missing or client not initialized.")
            
            response = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        elif model_provider == "deepseek":
            if not deepseek_client:
                raise ValueError("DeepSeek API Key missing or client not initialized.")
            
            response = await deepseek_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        else:
            raise ValueError(f"Unknown model provider: {model_provider}")
    
    except Exception as e:
        app_logger.error(f"LLM Provider Error ({model_provider}): {str(e)}")
        raise e


async def generate_ai_analysis(
    data: StudentDetailsInput,
    processed_tests: list[ProcessedTest]
) -> AIAnalysisResult:
    """
    Generates AI-based psychometric employability analysis using ONLY 'third' key data.
    Uses the model_provider specified in the input data (default: gemini).
    """

    summary_lines = [
        f"Student Name: {data.student_name}",
        f"Course: {data.course_name}",
        f"Institution: {data.institution or 'N/A'}",
        "--- PSYCHOMETRIC TEST RESULTS (Detailed Breakdown Only) ---",
    ]

    total_score = 0
    count = 0
    third_key_found = False

    if not processed_tests:
        summary_lines.append("No psychometric test data available.")
    else:
        for test in processed_tests:
            if test.key_name == 'third':
                third_key_found = True
                summary_lines.append(f"\nTest: {test.test_name}")
                for sec in test.sections:
                    summary_lines.append(f"- {sec.section}: {sec.score_percentage}%")
                    if sec.interpretation:
                        summary_lines.append(f"  Interpretation: {sec.interpretation}")
                    total_score += sec.score_percentage
                    count += 1
    
    if not third_key_found:
        summary_lines.append("No data found for the 'third' category.")

    summary_text = "\n".join(summary_lines)
    raw_avg = int(total_score / max(count, 1))

    prompt = f"""
You are a Senior Career Counselor, Psychometric Analyst, and Employability Assessor.

========================
STUDENT PROFILE & TEST DATA
========================
{summary_text}

========================
ANALYSIS OBJECTIVES
========================
1. Analyze the specific psychometric results provided above.
2. Identify employability strengths and development areas based ONLY on these results.
3. Assess real-world job readiness from an employer’s perspective.
4. If a Learning Style (VARK / fifth key) test exists, interpret how the student learns best.

========================
EMPLOYABILITY SCORING GUIDELINES
========================
- Generate a single **employability_score (0–100)**.
- Do NOT calculate a simple average.
- Base the score on:
  • Balance of skills across sections  
  • Presence of critical job-impacting strengths or weaknesses  
  • Practical workplace readiness  
  • Risk factors an employer would notice  
- Penalize severe gaps in essential skills even if other scores are high.
- Reward consistency, adaptability, and role-readiness.

========================
VARK LEARNING STYLE INSTRUCTIONS
========================
Provide **one clear, simple sentence** for each learning style explaining:
- How the student learns best
- What type of learning method suits them most

Keep the explanations:
- Direct and student-friendly
- Practical and usage-focused
- Based strictly on the provided VARK scores
- Avoid learning theory or textbook definitions
- If score data is missing, state that the preference cannot be determined


========================
OUTPUT FORMAT (STRICT JSON)
========================
{{
  "strengths": ["string", "string"],
  "development_areas": ["string", "string"],
  "recommended_roles": ["string", "string"],
  "certifications": ["string", "string"],
  "employability_score": integer,
  "employability_text": "Professional summary in max 3 sentences.",
  "vark_descriptions": [
    "Visual: ...",
    "Auditory: ...",
    "Read/Write: ...",
    "Kinesthetic: ..."
  ]
}}
"""


    try:
        provider = getattr(data, 'model', 'gemini').lower()
        
        json_str = await _get_llm_response(prompt, provider)
        result_json = json.loads(json_str)

        employability_score = result_json.get("employability_score", raw_avg)
        nps_score = result_json.get("nps_score", raw_avg)
        
        vark_descs = result_json.get("vark_descriptions", [])
        if vark_descs and len(vark_descs) == 4:
            for test in processed_tests:
                if test.key_name == 'fifth':
                    scores = [s.score_percentage for s in test.sections]
                    labels = [s.section for s in test.sections]
                    updated_vark_chart = ChartFactory.generate_vark_circles(scores, labels, descriptions=vark_descs)
                    test.charts['vark_circles'] = updated_vark_chart

    except Exception as e:
        app_logger.error(f"AI Analysis Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Analysis Failed: {str(e)}",
        )

    nps_chart = ChartFactory.generate_gauge(nps_score)

    return AIAnalysisResult(
        strengths=result_json.get("strengths", []),
        development_areas=result_json.get("development_areas", []),
        recommended_roles=result_json.get("recommended_roles", []),
        certifications=result_json.get("certifications", []),
        employability_score=employability_score,
        employability_text=result_json.get("employability_text", "Analysis complete."),
        nps_score=nps_score,
        nps_chart=nps_chart,
    )