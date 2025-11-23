"""
Notebook-friendly version of the timer cropper.
Use this in Jupyter notebooks for interactive cropping and visualization.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple, Optional, List
import os


class TimerCropper:
    """Detects and crops timer regions from Valorant screenshots."""
    
    def __init__(self, output_size: Tuple[int, int] = (400, 200)):
        """
        Initialize the timer cropper.
        
        Args:
            output_size: (width, height) of the cropped output image
        """
        self.output_size = output_size
        
    def detect_timer_region_color(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detect timer region using color-based detection."""
        h, w = image.shape[:2]
        
        # Focus on upper central region
        roi_y_start = 0
        roi_y_end = int(h * 0.3)
        roi_x_start = int(w * 0.2)
        roi_x_end = int(w * 0.8)
        
        roi = image[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Dark blue color range in HSV
        lower_hsv = np.array([100, 50, 30])
        upper_hsv = np.array([130, 255, 100])
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w_box, h_box = cv2.boundingRect(largest_contour)
        
        x += roi_x_start
        y += roi_y_start
        
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w_box = min(w - x, w_box + 2 * padding)
        h_box = min(h - y, h_box + 2 * padding)
        
        return (x, y, w_box, h_box)
    
    def detect_timer_region_heuristic(self, image: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Detect timer region using fixed position (timer is always in the same place).
        Adjust the percentages below if needed for your specific screenshots.
        """
        h, w = image.shape[:2]
        
        # Timer position - adjust these percentages if needed
        center_x = w // 2
        timer_width = int(w * 0.12)   # Width of timer overlay (balanced zoom)
        timer_height = int(h * 0.06)  # Height of timer overlay (balanced zoom)
        timer_y = int(h * 0.04)       # Distance from top (adjusted)
        
        x = center_x - timer_width // 2
        y = timer_y
        
        return (x, y, timer_width, timer_height)
    
    def crop_timer(self, image_path: str, method: str = 'heuristic', 
                   output_path: Optional[str] = None, 
                   show_preview: bool = False) -> Optional[np.ndarray]:
        """
        Crop timer region from a screenshot.
        
        Since the timer is always in the same place, 'heuristic' method is recommended.
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image {image_path}")
            return None
        
        # Use heuristic method (fixed position) since timer is always in same place
        if method == 'heuristic' or method == 'auto':
            bbox = self.detect_timer_region_heuristic(image)
        elif method == 'color':
            bbox = self.detect_timer_region_color(image)
            if bbox is None:
                bbox = self.detect_timer_region_heuristic(image)
        else:
            bbox = self.detect_timer_region_heuristic(image)
        
        # Crop and resize
        x, y, w, h = bbox
        cropped = image[y:y+h, x:x+w]
        cropped = cv2.resize(cropped, self.output_size, interpolation=cv2.INTER_AREA)
        
        # Show preview if requested
        if show_preview:
            fig, axes = plt.subplots(1, 2, figsize=(12, 6))
            
            # Original with bounding box
            img_with_box = image.copy()
            cv2.rectangle(img_with_box, (x, y), (x+w, y+h), (0, 255, 0), 2)
            axes[0].imshow(cv2.cvtColor(img_with_box, cv2.COLOR_BGR2RGB))
            axes[0].set_title('Original with Detection Box')
            axes[0].axis('off')
            
            # Cropped region
            axes[1].imshow(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
            axes[1].set_title('Cropped Timer Region')
            axes[1].axis('off')
            
            plt.tight_layout()
            plt.show()
        
        if output_path:
            cv2.imwrite(output_path, cropped)
            print(f"Saved to: {output_path}")
        
        return cropped
    
    def batch_crop(self, input_dir: str, output_dir: str, method: str = 'auto'):
        """Batch crop timer regions from multiple screenshots."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [f for f in input_path.iterdir() 
                      if f.suffix.lower() in image_extensions]
        
        print(f"Processing {len(image_files)} images...")
        
        success_count = 0
        for i, image_file in enumerate(image_files, 1):
            output_file = output_path / f"cropped_{image_file.stem}.jpg"
            cropped = self.crop_timer(str(image_file), method=method, 
                                     output_path=str(output_file))
            if cropped is not None:
                success_count += 1
            if i % 10 == 0:
                print(f"  Processed {i}/{len(image_files)}...")
        
        print(f"\n✓ Cropped {success_count}/{len(image_files)} images")
        return success_count


# Convenience function for notebook use
def crop_timer_region(image_path: str, output_path: str = None, 
                     show_preview: bool = True, method: str = 'heuristic'):
    """
    Quick function to crop a timer region from a screenshot.
    
    Since the timer is always in the same place, 'heuristic' method is used by default.
    
    Usage in notebook:
        crop_timer_region('screenshot.jpg', show_preview=True)
    """
    cropper = TimerCropper()
    return cropper.crop_timer(image_path, method=method, 
                             output_path=output_path, show_preview=show_preview)


def batch_crop_timers(input_dir: str, output_dir: str, method: str = 'heuristic'):
    """
    Batch crop timer regions from a directory of screenshots.
    
    Since the timer is always in the same place, 'heuristic' method is used by default.
    
    Usage in notebook:
        batch_crop_timers('screenshots/', 'cropped_timers/')
    """
    cropper = TimerCropper()
    return cropper.batch_crop(input_dir, output_dir, method=method)

