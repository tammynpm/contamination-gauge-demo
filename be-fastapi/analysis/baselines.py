from typing import Dict
from models.schemas import Baseline

class BaselineManager:
    def __init__(self):
        self.baselines: Dict[str, Baseline]={
            "clean_surface": Baseline(
                id="clean_surface",
                name="Clean Surface",
                description="freshly cleaned lab bench or cutting board",
                expected_score=15.0
            ),
            "light_use": Baseline(
                id="light_use",
                name= "Ligh Use",
                description="surface after light use, minimal contamination",
                expected_score=35.0
            ),
            "moderate_use": Baseline(
                id="moderate_use",
                name="Moderate Use",
                description="surface after moderate contamination",
                expected_score=55.0
            ),
            "heavy_use": Baseline(
                id="heavy_use",
                name="Heavy Use",
                description="surface after heavy contamination",
                expected_score=75.0
            )
        }
    def get_baseline(self, baseline_id: str) -> Baseline:
        return self.baselines.get(
            baseline_id,
            self.baselines["clean_surface"] # get baseline by ID return default if not found 
        )
    
    def list_baselines(self) -> Dict[str, Baseline]:
        return self.baselines
    