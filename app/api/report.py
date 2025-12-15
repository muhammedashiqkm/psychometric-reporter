from fastapi import APIRouter, Depends, HTTPException
from app.models.psychometric import StudentDetailsInput
from app.services import test_logic, llm_service, pdf_service
from app.core.security import verify_token
from app.core.logging_config import app_logger

router = APIRouter()

@router.post("/generate")
async def generate_report(
    request: StudentDetailsInput,
    current_user: str = Depends(verify_token)
):
    app_logger.info(f"Report generation started for {request.register_no}")
    
    try:
        processed_tests = []
        for raw_test in request.psychometric_data:
            if not raw_test.json_result or raw_test.json_result == "":
                continue
                
            processed = test_logic.TestProcessor.process_raw(raw_test)
            if processed.sections:
                processed_tests.append(processed)
            
        ai_result = await llm_service.generate_ai_analysis(request, processed_tests)
        
        filename, report_url = pdf_service.generate_pdf(
            request, 
            processed_tests,
            ai_result
        )
        
        return {
            "filename": filename,
            "report_url": report_url
        }
        
    except Exception as e:
        app_logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))