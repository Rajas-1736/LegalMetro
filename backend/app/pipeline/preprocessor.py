import os
import cv2
import numpy as np
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    Stage A: OpenCV Preprocessing
    - Auto-deskew and orientation correction
    - CLAHE contrast enhancement for glare / low-contrast labels
    - Bilateral / Gaussian denoising
    - Bicubic sharpening & super-resolution upscaling for small declaration text
    """

    def process(self, image_bytes: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
        # Decode bytes to OpenCV BGR image
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Failed to decode image data into OpenCV format")

        orig_h, orig_w = img.shape[:2]
        metadata = {
            "original_width": orig_w,
            "original_height": orig_h,
            "deskew_angle": 0.0,
            "clahe_applied": True,
            "denoised": True,
            "upscaled": False,
        }

        # 1. Auto-deskew
        img, deskew_angle = self._deskew_image(img)
        metadata["deskew_angle"] = round(deskew_angle, 2)

        # 2. Glare reduction & CLAHE contrast enhancement on Luminance channel
        img = self._apply_clahe(img)

        # 3. Denoising
        img = cv2.bilateralFilter(img, d=7, sigmaColor=50, sigmaSpace=50)

        # 4. Super-resolution / sharpening for small text if resolution is low
        if orig_w < 1200 or orig_h < 1200:
            img = self._upscale_and_sharpen(img)
            metadata["upscaled"] = True

        return img, metadata

    def _deskew_image(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Calculates skew angle from edges and rotates image to upright position."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=20)
            
            angle = 0.0
            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    deg = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    # Focus on near horizontal lines (-45 to 45 deg)
                    if -45 < deg < 45:
                        angles.append(deg)
                if angles:
                    angle = float(np.median(angles))

            if abs(angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                return rotated, angle
        except Exception as e:
            logger.warning(f"Deskew failed: {e}. Keeping original orientation.")

        return image, 0.0

    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Applies Contrast Limited Adaptive Histogram Equalization to LAB L-channel."""
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        except Exception as e:
            logger.warning(f"CLAHE contrast enhancement failed: {e}")
            return image

    def _upscale_and_sharpen(self, image: np.ndarray) -> np.ndarray:
        """Upscales 1.5x with bicubic interpolation and applies unsharp mask to restore crisp edges."""
        try:
            h, w = image.shape[:2]
            scaled = cv2.resize(image, (int(w * 1.5), int(h * 1.5)), interpolation=cv2.INTER_CUBIC)
            
            # Unsharp masking
            gaussian = cv2.GaussianBlur(scaled, (0, 0), 2.0)
            sharpened = cv2.addWeighted(scaled, 1.5, gaussian, -0.5, 0)
            return sharpened
        except Exception as e:
            logger.warning(f"Upscaling failed: {e}")
            return image

preprocessor = ImagePreprocessor()
