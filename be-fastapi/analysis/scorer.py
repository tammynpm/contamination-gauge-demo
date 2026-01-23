import cv2
import numpy as np
from PIL import Image
from typing import Tuple
from models.schemas import AnalysisMetrics

"""
spot dark regions on light background
edge density
intensity variance 
"""

class ContaminationScorer:
    def __init__(self, target_size=(800,600)):
        self.target_size = target_size

    def analyze (self, image: Image.Image) -> Tuple[float, AnalysisMetrics]:
        img_array = np.array(image) #pil image -> np array in rgb format
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR) #opencv default format is bgr
        img_cv = cv2.resize(img_cv, self.target_size)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        spot_coverage = self._calculate_spot_coverage(gray)
        edge_density = self._calculate_edge_density(gray)
        texture_variance = self._calculate_texture_variance(gray)
        mean_intensity = float(np.mean(gray))

        score = (
            spot_coverage * 0.5 * 100 + edge_density * 0.35 * 100 + (texture_variance / 128) * 0.15 * 100
        )

        score = max(0, min(100, score))
        metrics = AnalysisMetrics(
            spot_coverage=round(spot_coverage, 4),
            edge_density=round(edge_density,4),
            texture_variance= round(texture_variance, 2),
            mean_intensity=round(mean_intensity,2)
        )
        return score, metrics

    def _calculate_spot_coverage(self, gray: np.ndarray) -> float:
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, #dark spots become white
            blockSize=11,
            C=2
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        coverage = np.sum(binary>0) / binary.size
        return float(coverage)

    def _calculate_edge_density(self, gray:np.ndarray) -> float:
        blurred = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

        density = np.sum(edges>0) /edges.size
        return float(density)

    def _calculate_texture_variance(self,gray:np.ndarray) -> float:
        return float(np.std(gray))


