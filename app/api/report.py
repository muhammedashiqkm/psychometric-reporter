from fastapi import APIRouter, Depends, HTTPException
import httpx  # You might need to install this: pip install httpx
from typing import List

from app.models.psychometric import StudentDetailsInput, ReportRequest
from app.services import test_logic, llm_service, pdf_service
from app.core.security import verify_token
from app.core.logging_config import app_logger

router = APIRouter()

@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    current_user: str = Depends(verify_token)
):
    """
    1. Accepts ProfileURL.
    2. Fetches the JSON data from that URL.
    3. Parses it into the StudentDetailsInput model.
    4. Generates the report.
    """
    app_logger.info(f"Report generation requested for URL: {request.profile_url}")
    
    try:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(str(request.profile_url))
                response.raise_for_status()
                external_data_list = response.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=400, detail=f"Failed to fetch profile: {e}")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid URL or non-JSON response: {e}")

        if isinstance(external_data_list, list) and len(external_data_list) > 0:
            student_data = external_data_list[0] 
        elif isinstance(external_data_list, dict):
            student_data = external_data_list
        else:
            raise HTTPException(status_code=400, detail="Invalid JSON structure from ProfileURL")

        student_data['model'] = request.model

        try:
            student_input = StudentDetailsInput(**student_data)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Data validation failed: {str(e)}")

        app_logger.info(f"Processing report for Student: {student_input.student_name}")

        processed_tests = []
        for raw_test in student_input.psychometric_data:
            if not raw_test.json_result or raw_test.json_result == "":
                continue
                
            processed = test_logic.TestProcessor.process_raw(raw_test)
            if processed.sections:
                processed_tests.append(processed)
            
        ai_result = await llm_service.generate_ai_analysis(student_input, processed_tests)
        
        filename, report_url = pdf_service.generate_pdf(
            student_input, 
            processed_tests,
            ai_result
        )
        
        return {
            "filename": filename,
            "report_url": report_url
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        app_logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))