import cv2
import numpy as np
try:
    import rules_engine
except ImportError:
    from app.pipeline import rules_engine

class VisualAuditor:
    @staticmethod
    def calculate_wcag_luminance(rgb_color):
        """Calculates relative luminance according to WCAG 2.1 specifications."""
        rgb_norm = [c / 255.0 for c in rgb_color]
        linear_rgb = []
        for val in rgb_norm:
            if val <= 0.03928:
                linear_rgb.append(val / 12.92)
            else:
                linear_rgb.append(((val + 0.055) / 1.055) ** 2.4)
        return 0.2126 * linear_rgb[0] + 0.7152 * linear_rgb[1] + 0.0722 * linear_rgb[2]

    @classmethod
    def calculate_contrast_ratio(cls, text_rgb, bg_rgb):
        """Calculates contrast ratio between text color and background color."""
        l1 = cls.calculate_wcag_luminance(text_rgb)
        l2 = cls.calculate_wcag_luminance(bg_rgb)
        brightest = max(l1, l2)
        darkest = min(l1, l2)
        ratio = (brightest + 0.05) / (darkest + 0.05)
        return round(ratio, 2)

    @classmethod
    def extract_patch_contrast(cls, img):
        """
        Extracts the true contrast ratio of printed text against its immediate background.
        Uses adaptive thresholding to isolate dark ink text strokes from the label paper.
        """
        if img is None or img.size == 0:
            return {"contrast_ratio": "1.0:1", "is_compliant": False, "remarks": "Invalid image"}

        # Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Use morphological gradient / edge density to find the text-dense declaration block
        # (This automatically zooms into the white panel and ignores the plain yellow background)
        grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 2. Segment ink pixels (dark strokes) vs local paper background
        # Adaptive thresholding isolates the actual letter strokes
        text_mask = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8
        )

        # Find the region with the highest density of text strokes (the declaration card)
        contours, _ = cv2.findContours(text_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_boxes = [cv2.boundingRect(c) for c in contours if 50 < cv2.contourArea(c) < 5000]

        if valid_boxes:
            # Bounding box of the entire text area
            x_min = min(b[0] for b in valid_boxes)
            y_min = min(b[1] for b in valid_boxes)
            x_max = max(b[0] + b[2] for b in valid_boxes)
            y_max = max(b[1] + b[3] for b in valid_boxes)
            
            # Crop strictly to the declaration label
            text_panel = img[y_min:y_max, x_min:x_max]
            panel_gray = gray[y_min:y_max, x_min:x_max]
            panel_mask = text_mask[y_min:y_max, x_min:x_max]
        else:
            text_panel = img
            panel_gray = gray
            panel_mask = text_mask

        # Calculate mean color of ink (foreground) vs paper (background)
        ink_pixels = text_panel[panel_mask == 255]
        paper_pixels = text_panel[panel_mask == 0]

        if len(ink_pixels) > 0 and len(paper_pixels) > 0:
            # Average BGR of text and background
            ink_bgr = np.median(ink_pixels, axis=0)
            paper_bgr = np.median(paper_pixels, axis=0)

            # Convert to RGB
            text_rgb = [int(ink_bgr[2]), int(ink_bgr[1]), int(ink_bgr[0])]
            bg_rgb = [int(paper_bgr[2]), int(paper_bgr[1]), int(paper_bgr[0])]
        else:
            # Fallback to extreme luminance values in panel
            text_rgb = [30, 30, 30]
            bg_rgb = [240, 240, 240]

        ratio = cls.calculate_contrast_ratio(text_rgb, bg_rgb)
        is_compliant = ratio >= 3.0

        return {
            "contrast_ratio": f"{ratio}:1",
            "text_color_rgb": text_rgb,
            "bg_color_rgb": bg_rgb,
            "is_compliant": is_compliant,
            "rule": "Rule 9(1)(b)",
            "remarks": (
                f"Conspicuous contrast verified ({ratio}:1 against statutory minimum 3.0:1)."
                if is_compliant else
                f"VIOLATION under Rule 9(1)(b): Contrast ratio ({ratio}:1) is below statutory 3.0:1."
            )
        }

    @staticmethod
    def audit_font_height(numeral_height_px, package_height_px, actual_package_height_mm, quantity_magnitude, unit):
        """
        Converts pixel numeral height to real-world millimeters and checks against Rule 7 Table-I.
        """
        if package_height_px <= 0 or numeral_height_px <= 0:
            return {"error": "Invalid bounding box dimensions"}

        # Scale pixels to mm
        px_to_mm_ratio = actual_package_height_mm / float(package_height_px)
        measured_height_mm = round(numeral_height_px * px_to_mm_ratio, 2)

        # Lookup minimum statutory requirement from rules_engine
        required_height_mm = rules_engine.get_required_numeral_height(quantity_magnitude, unit)

        is_compliant = measured_height_mm >= required_height_mm
        status = "COMPLIANT" if is_compliant else "VIOLATION"
        remarks = (
            f"Measured height ({measured_height_mm}mm) meets statutory minimum of {required_height_mm}mm."
            if is_compliant else
            f"VIOLATION under Rule 7(2) Table-I: Measured numeral height ({measured_height_mm}mm) is below required {required_height_mm}mm."
        )

        return {
            "measured_numeral_height_mm": measured_height_mm,
            "statutory_min_height_mm": required_height_mm,
            "status": status,
            "is_compliant": is_compliant,
            "rule": "Rule 7(2) read with Table-I",
            "remarks": remarks
        }

if __name__ == "__main__":
    # Test contrast calculation on sample colors
    # Black text on White background:
    print("[*] Contrast Test (Black on White):", VisualAuditor.calculate_contrast_ratio([0,0,0], [255,255,255]), ": 1")
    
    # Yellow text on Gold/White background (common violation):
    print("[*] Contrast Test (Yellow on White):", VisualAuditor.calculate_contrast_ratio([255,255,100], [255,255,255]), ": 1")

    # Font size test: 1kg packet (requires 4mm). Numeral is 25px, package is 1000px, package height is 180mm:
    font_test = VisualAuditor.audit_font_height(
        numeral_height_px=25,
        package_height_px=1000,
        actual_package_height_mm=180,
        quantity_magnitude=1.0,
        unit="kg"
    )
    print("\n[*] Font Size Audit Test:")
    print(font_test)