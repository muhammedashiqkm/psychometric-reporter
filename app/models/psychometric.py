from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal
import json


class SectionData(BaseModel):
    section: str
    description: Optional[str] = ""
    representation: Optional[str] = ""
    interpretation: Optional[str] = "" 
    section_score: str

class ProcessedData(BaseModel):
    test_name: str
    key_name: str
    sections: List[SectionData]

class RawPsychometricTest(BaseModel):
    key_name: str = Field(..., alias="KeyName")
    category: str = Field(..., alias="PsychometricTestCategory")
    json_result: Optional[str] = Field(None, alias="JsonResult")

    @property
    def parsed_sections(self) -> List[SectionData]:
        if not self.json_result:
            return []
        try:
            data = json.loads(self.json_result)
            if not isinstance(data, dict): return []
            raw_sections = data.get("sections", [])
            return [SectionData(**s) for s in raw_sections]
        except json.JSONDecodeError:
            return []

class StudentDetailsInput(BaseModel):
    student_name: str = Field(..., alias="StudentName")
    register_no: str = Field(..., alias="RegisterNo")
    institution: str = Field(..., alias="InstitutionName")
    
    course_name: Optional[str] = Field(None, alias="CourseName")
    email: Optional[str] = Field(None, alias="Email")
    batch: Optional[str] = Field(None, alias="Batch")
    psychometric_data: List[RawPsychometricTest] = Field(..., alias="StudentPsychometricCategoryDetailsForPortfolioData")
    
    model: Literal["gemini", "openai", "deepseek"] = "gemini" 

class ReportRequest(BaseModel):
    model: Literal["gemini", "openai", "deepseek"] = "gemini"
    profile_url: HttpUrl = Field(..., alias="ProfileURL")

class ProcessedSection(BaseModel):
    section: str
    score_percentage: float
    original_score: str
    interpretation: str
    benchmark: Optional[str] = None

class ProcessedTest(BaseModel):
    test_name: str
    description: Optional[str] = None
    key_name: str
    sections: List[ProcessedSection]
    charts: dict

class AIAnalysisResult(BaseModel):
    strengths: List[str]
    development_areas: List[str]
    recommended_roles: List[str]
    certifications: List[str]
    employability_score: int
    employability_text: str
    employability_chart: Optional[str] = None