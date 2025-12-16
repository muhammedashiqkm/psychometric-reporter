import json
import asyncio
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
    try:
        if model_provider == "gemini":
            if not gemini_model:
                raise ValueError("Gemini API Key missing")
            response = await gemini_model.generate_content_async(
                prompt, generation_config={"response_mime_type": "application/json"}
            )
            return response.text

        elif model_provider == "openai":
            if not openai_client:
                raise ValueError("OpenAI API Key missing")
            response = await openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        elif model_provider == "deepseek":
            if not deepseek_client:
                raise ValueError("DeepSeek API Key missing")
            response = await deepseek_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        else:
            raise ValueError(f"Unknown model provider: {model_provider}")
    except Exception as e:
        app_logger.error(f"LLM Error: {e}")
        raise e


async def _generate_vark_details(test: ProcessedTest, provider: str) -> list[str]:
    """
    Generates VARK descriptions.
    """
    lines = []
    
    if test.description:
        lines.append(f"Context: {test.description}")
        
    for s in test.sections:
        lines.append(f"- {s.section}: {s.score_percentage}%")
        if s.interpretation:
            lines.append(f"  Interpretation: {s.interpretation}")

    score_summary = "\n".join(lines)

    prompt = f"""
You are an expert Educational Psychologist.
VARK RESULTS:
{score_summary}

Generate 4 simple sentences (Visual, Auditory, Read/Write, Kinesthetic) explaining how this student learns best.
Order: [Visual, Auditory, Read/Write, Kinesthetic]
Output JSON: {{ "vark_descriptions": ["string", "string", "string", "string"] }}
"""
    try:
        json_str = await _get_llm_response(prompt, provider)
        result = json.loads(json_str)
        return result.get("vark_descriptions", [])
    except Exception as e:
        app_logger.error(f"VARK Error: {e}")
        return []


async def generate_ai_analysis(
    data: StudentDetailsInput,
    processed_tests: list[ProcessedTest]
) -> AIAnalysisResult:
    
    summary_lines = [
        f"Student Name: {data.student_name}",
        f"Course: {data.course_name}",
        "--- PSYCHOMETRIC TEST RESULTS ---",
    ]

    total_score = 0
    count = 0
    fifth_key_test = None

    if not processed_tests:
        summary_lines.append("No data available.")
    else:
        for test in processed_tests:
            if test.key_name == 'fifth':
                fifth_key_test = test

            summary_lines.append(f"\nTest: {test.test_name}")
            if test.description:
                summary_lines.append(f"Description: {test.description}")
            
            for sec in test.sections:
                summary_lines.append(f"- {sec.section}: {sec.score_percentage}%")
                if sec.interpretation:
                    summary_lines.append(f"  Interpretation: {sec.interpretation}")
                total_score += sec.score_percentage
                count += 1
    
    summary_text = "\n".join(summary_lines)
    raw_avg = int(total_score / max(count, 1))

    main_prompt = f"""
You are a Career Counselor.
PROFILE:
{summary_text}

Analyze the employability.
Output JSON:
{{
  "strengths": ["str"],
  "development_areas": ["str"],
  "recommended_roles": ["str"],
  "certifications": ["str"],
  "employability_score": int,
  "employability_text": "Summary..."
}}
"""

    try:
        provider = getattr(data, 'model', 'gemini').lower()
        
        main_task = _get_llm_response(main_prompt, provider)
        
        vark_task = None
        if fifth_key_test:
            vark_task = _generate_vark_details(fifth_key_test, provider)

        if vark_task:
            main_resp_str, vark_descs = await asyncio.gather(main_task, vark_task)
        else:
            main_resp_str = await main_task
            vark_descs = []

        result_json = json.loads(main_resp_str)
        employability_score = result_json.get("employability_score", raw_avg)

        if fifth_key_test and vark_descs and len(vark_descs) == 4:
            scores = [s.score_percentage for s in fifth_key_test.sections]
            labels = [s.section for s in fifth_key_test.sections]
            updated_vark = ChartFactory.generate_vark_circles(scores, labels, descriptions=vark_descs)
            fifth_key_test.charts['vark_circles'] = updated_vark

    except Exception as e:
        app_logger.error(f"Analysis Failed: {e}")
        raise HTTPException(status_code=502, detail="AI Analysis Failed")

    employability_gauge = ChartFactory.generate_gauge(employability_score)

    return AIAnalysisResult(
        strengths=result_json.get("strengths", []),
        development_areas=result_json.get("development_areas", []),
        recommended_roles=result_json.get("recommended_roles", []),
        certifications=result_json.get("certifications", []),
        employability_score=employability_score,
        employability_text=result_json.get("employability_text", ""),
        employability_chart=employability_gauge
    )