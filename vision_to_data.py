import argparse
import base64
import json
import os
import re
import time

import requests

# Ollama configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Use a vision-capable model optimized for OCR:
# - moondream: Fast, lightweight, great for simple text extraction (recommended)
# - qwen2-vl: Excellent OCR accuracy, larger model
# - llava-llama3: Good balance of speed and accuracy
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "moondream")

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def summarize_png(image_path):
    b64 = encode_image(image_path)

    # Prompt to extract timer value
    prompt = "Read the text in the image."

    # Ollama chat API format
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [b64]
            }
        ],
        "stream": False
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        headers=headers,
        json=payload
    )

    # Check for errors
    if response.status_code != 200:
        print(f"❌ API Error: Status {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    
    # Ollama API format
    response_text = None
    if "message" in data and "content" in data["message"]:
        response_text = data["message"]["content"]
    elif "response" in data:
        response_text = data["response"]
    else:
        print(f"❌ Unexpected API response structure:")
        print(json.dumps(data, indent=2))
        return None
    
    # Extract timer value using regex (format: M:SS or MM:SS)
    timer_pattern = r'\b(\d{1,2}:\d{2})\b'
    timer_match = re.search(timer_pattern, response_text)
    
    if timer_match:
        return timer_match.group(1)
    else:
        # If no match found, return the raw response for debugging
        print(f"⚠️  Could not extract timer from response: {response_text}")
        return response_text.strip()

# ---- CLI helper ----
def summarize_with_timing(image_path):
    """Convenience wrapper to time a single inference call."""
    start_time = time.time()
    print(f"Summarizing {image_path}")
    result = summarize_png(image_path)
    print(result)
    print("-" * 100)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Valorant round timer text from screenshots via Ollama vision models."
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="Path to a single image file to analyze. If omitted, process a directory instead.",
    )
    parser.add_argument(
        "--dir",
        default="cropped_timers",
        help="Directory of images to batch process when no single image path is provided.",
    )
    args = parser.parse_args()

    if args.image:
        image_path = os.path.expanduser(args.image)
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        summarize_with_timing(image_path)
    else:
        directory = os.path.expanduser(args.dir)
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        for img in sorted(os.listdir(directory)):
            img_path = os.path.join(directory, img)
            if not os.path.isfile(img_path):
                continue
            summarize_with_timing(img_path)