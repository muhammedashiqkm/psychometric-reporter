from app.models.psychometric import RawPsychometricTest, ProcessedSection, ProcessedTest
from app.services.chart_factory import ChartFactory
import json

class TestProcessor:
    @staticmethod
    def parse_score(score_str: str) -> float:
        try:
            if "/" in score_str:
                num, den = map(float, score_str.split('/'))
                if den == 0: return 0.0
                return round((num / den) * 100, 1)
            return float(score_str)
        except:
            return 0.0

    @staticmethod
    def get_benchmark(score: float) -> str:
        if score >= 75: return "High"
        if score >= 60: return "Above Average"
        if score >= 40: return "Average"
        return "Below Average"

    @classmethod
    def process_raw(cls, raw_test: RawPsychometricTest) -> ProcessedTest:
        processed_sections = []
        labels = []
        scores = []

        sections = raw_test.parsed_sections
        
        test_name = raw_test.category
        if raw_test.json_result:
            try:
                data = json.loads(raw_test.json_result)
                test_name = data.get("test_name", raw_test.category)
            except:
                pass

        for section in sections:
            pct = cls.parse_score(section.section_score)
            labels.append(section.section)
            scores.append(pct)
            
            benchmark = cls.get_benchmark(pct)
            
            if section.interpretation:
                interp = section.interpretation
            elif section.representation:
                interp = section.representation
            else:
                interp = section.description

            processed_sections.append(ProcessedSection(
                section=section.section,
                score_percentage=pct,
                original_score=section.section_score,
                interpretation=interp,
                benchmark=benchmark
            ))

        charts = {}
        if scores:
            charts['bar'] = ChartFactory.generate_bar_chart(labels, scores, color="#4a90e2")

            if raw_test.key_name == "first":
                charts['radar'] = ChartFactory.generate_radar_chart(labels, scores)
            
            elif raw_test.key_name == "third":
                charts['donut'] = ChartFactory.generate_radial_bar_chart(labels, scores)
            
            elif raw_test.key_name == "fourth":
                charts['bar'] = ChartFactory.generate_seven_segment_chart(labels, scores)

            elif raw_test.key_name == "fifth":
                charts['vark_circles'] = ChartFactory.generate_vark_circles(scores, labels)
                
        return ProcessedTest(
            test_name=test_name,
            key_name=raw_test.key_name,
            sections=processed_sections,
            charts=charts
        )