# models/analysis_result.py

from dataclasses import dataclass

@dataclass
class AnalysisResult:
    odg_score: float
    quality_rating: str
    plot_path: str = None
