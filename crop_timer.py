#!/usr/bin/env python3
"""
Valorant Timer Region Cropper

This script automatically crops the timer region from Valorant screenshots.
Since the timer is always in the same position, it uses a fixed position (heuristic method).

To adjust the timer position, modify the percentages in detect_timer_region_heuristic():
- timer_width: width of timer overlay (default: 15% of image width)
- timer_height: height of timer overlay (default: 8% of image height)  
- timer_y: distance from top (default: 5% of image height)
"""

import cv2
import numpy as np
import os
from pathlib import Path
from typing import Tuple, Optional
import argparse


class TimerCropper:
    """Detects and crops timer regions from Valorant screenshots."""
    
    def __init__(self, output_size: Tuple[int, int] = (400, 200)):
        """
        Initialize the timer cropper.
        
        Args:
            output_size: (width, height) of the cropped output image
        """
        self.output_size = output_size
        # Dark blue color range for the timer overlay (BGR format for OpenCV)
        # Adjust these values based on your screenshots
        self.lower_blue = np.array([40, 30, 20])   # Lower bound for dark blue
        self.upper_blue = np.array([80, 60, 50])   # Upper bound for dark blue
        
    def detect_timer_region_color(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect timer region using color-based detection.
        Looks for dark blue overlay in the upper central area.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            (x, y, width, height) bounding box or None if not found
        """
        h, w = image.shape[:2]
        
        # Focus on upper central region (where timer typically appears)
        # Top 30% of image, central 60% horizontally
        roi_y_start = 0
        roi_y_end = int(h * 0.3)
        roi_x_start = int(w * 0.2)
        roi_x_end = int(w * 0.8)
        
        roi = image[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Create mask for dark blue regions
        # Adjust these HSV values based on your screenshots
        lower_hsv = np.array([100, 50, 30])  # Dark blue in HSV
        upper_hsv = np.array([130, 255, 100])
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find the largest contour (likely the timer overlay)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding box
        x, y, w_box, h_box = cv2.boundingRect(largest_contour)
        
        # Adjust coordinates to full image
        x += roi_x_start
        y += roi_y_start
        
        # Add padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w_box = min(w - x, w_box + 2 * padding)
        h_box = min(h - y, h_box + 2 * padding)
        
        return (x, y, w_box, h_box)
    
    def detect_timer_region_template(self, image: np.ndarray, 
                                     template: Optional[np.ndarray] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect timer region using template matching.
        Looks for the "ROUND" text pattern.
        
        Args:
            image: Input image (BGR format)
            template: Optional template image to match
            
        Returns:
            (x, y, width, height) bounding box or None if not found
        """
        h, w = image.shape[:2]
        
        # Focus on upper central region
        roi_y_start = 0
        roi_y_end = int(h * 0.3)
        roi_x_start = int(w * 0.2)
        roi_x_end = int(w * 0.8)
        
        roi = image[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # If no template provided, look for text-like regions
        # Apply threshold to find text
        _, thresh = cv2.threshold(gray_roi, 100, 255, cv2.THRESH_BINARY)
        
        # Find horizontal lines (text regions)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        detected_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find the largest horizontal region (likely contains timer text)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w_box, h_box = cv2.boundingRect(largest_contour)
        
        # Adjust coordinates and add padding
        x += roi_x_start
        y += roi_y_start
        padding = 15
        x = max(0, x - padding)
        y = max(0, y - padding)
        w_box = min(w - x, w_box + 2 * padding)
        h_box = min(h - y, h_box + 2 * padding)
        
        return (x, y, w_box, h_box)
    
    def detect_timer_region_heuristic(self, image: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Detect timer region using fixed position (timer is always in the same place).
        This is the primary method since the timer position is consistent.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            (x, y, width, height) bounding box
        """
        h, w = image.shape[:2]
        
        # Timer is in upper central region - adjust these values based on your screenshots
        # These are percentages of image dimensions
        center_x = w // 2
        timer_width = int(w * 0.12)   # Timer overlay width (balanced zoom)
        timer_height = int(h * 0.06)  # Timer overlay height (balanced zoom)
        timer_y = int(h * 0.04)       # Distance from top (adjusted)
        
        x = center_x - timer_width // 2
        y = timer_y
        
        return (x, y, timer_width, timer_height)
    
    def crop_timer(self, image_path: str, method: str = 'heuristic', 
                   output_path: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Crop timer region from a screenshot.
        
        Args:
            image_path: Path to input screenshot
            method: Detection method ('heuristic' is default and recommended since timer is always in same place)
            output_path: Optional path to save cropped image
            
        Returns:
            Cropped image as numpy array, or None if detection failed
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image {image_path}")
            return None
        
        # Since timer is always in the same place, use heuristic method
        # (Other methods kept for compatibility but not recommended)
        if method == 'heuristic' or method == 'auto':
            bbox = self.detect_timer_region_heuristic(image)
        elif method == 'color':
            bbox = self.detect_timer_region_color(image)
            if bbox is None:
                # Fallback to heuristic
                bbox = self.detect_timer_region_heuristic(image)
        elif method == 'template':
            bbox = self.detect_timer_region_template(image)
            if bbox is None:
                # Fallback to heuristic
                bbox = self.detect_timer_region_heuristic(image)
        else:
            bbox = self.detect_timer_region_heuristic(image)
        
        # Crop the region
        x, y, w, h = bbox
        cropped = image[y:y+h, x:x+w]
        
        # Resize to output size
        cropped = cv2.resize(cropped, self.output_size, interpolation=cv2.INTER_AREA)
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(output_path, cropped)
            print(f"Saved cropped timer to: {output_path}")
        
        return cropped
    
    def batch_crop(self, input_dir: str, output_dir: str, 
                   method: str = 'auto', organize_by_time: bool = False):
        """
        Batch crop timer regions from multiple screenshots.
        
        Args:
            input_dir: Directory containing input screenshots
            output_dir: Directory to save cropped images
            method: Detection method to use
            organize_by_time: If True, organize output by detected time values (requires OCR)
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Supported image formats
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # Get all image files
        image_files = [f for f in input_path.iterdir() 
                      if f.suffix.lower() in image_extensions]
        
        print(f"Found {len(image_files)} images to process...")
        
        success_count = 0
        for i, image_file in enumerate(image_files, 1):
            print(f"Processing {i}/{len(image_files)}: {image_file.name}")
            
            output_file = output_path / f"cropped_{image_file.stem}.jpg"
            
            cropped = self.crop_timer(str(image_file), method=method, 
                                     output_path=str(output_file))
            
            if cropped is not None:
                success_count += 1
        
        print(f"\n✓ Successfully cropped {success_count}/{len(image_files)} images")
        print(f"  Output directory: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Crop timer regions from Valorant screenshots'
    )
    parser.add_argument('input', type=str, 
                       help='Input image file or directory')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output file or directory (default: same as input with _cropped suffix)')
    parser.add_argument('-m', '--method', type=str, default='heuristic',
                       choices=['auto', 'color', 'template', 'heuristic'],
                       help='Detection method (default: heuristic - recommended since timer position is fixed)')
    parser.add_argument('--width', type=int, default=200,
                       help='Output width in pixels (default: 200)')
    parser.add_argument('--height', type=int, default=100,
                       help='Output height in pixels (default: 100)')
    
    args = parser.parse_args()
    
    cropper = TimerCropper(output_size=(args.width, args.height))
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input path '{args.input}' does not exist")
        return
    
    # Determine if input is file or directory
    if input_path.is_file():
        # Single file processing
        if args.output is None:
            output_path = input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"
        else:
            output_path = Path(args.output)
        
        cropped = cropper.crop_timer(str(input_path), method=args.method, 
                                    output_path=str(output_path))
        
        if cropped is not None:
            print(f"✓ Successfully cropped timer region")
        else:
            print("✗ Failed to crop timer region")
    
    elif input_path.is_dir():
        # Batch processing
        if args.output is None:
            output_dir = input_path.parent / f"{input_path.name}_cropped"
        else:
            output_dir = Path(args.output)
        
        cropper.batch_crop(str(input_path), str(output_dir), method=args.method)
    
    else:
        print(f"Error: '{args.input}' is not a valid file or directory")


if __name__ == '__main__':
    main()

