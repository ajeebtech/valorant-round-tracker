# Valorant Round Timer Tracker

This project trains a TensorFlow Lite model to extract round timer values from Valorant screenshots.

## Quick Start

1. **Crop timer regions** from your screenshots (see below)
2. **Organize cropped images** into folders by time value
3. **Train the model** using the notebook
4. **Use the exported model** in your application

## Automatic Timer Cropping

Before organizing your dataset, use the automatic cropping script to extract timer regions from full screenshots.

**Current optimized settings:**
- Crop region: 12% width, 6% height (balanced zoom)
- Output size: 400×200 pixels
- Method: Fixed position (heuristic) - fastest and most reliable

### Command Line Usage

```bash
# Crop a single screenshot
python crop_timer.py screenshot.jpg -o cropped_timer.jpg

# Batch crop all screenshots in a folder
python crop_timer.py screenshots/ -o cropped_timers/

# Use specific detection method
python crop_timer.py screenshots/ -o cropped_timers/ -m heuristic
```

### Detection Methods

- **`auto`** (default): Tries color detection first, falls back to heuristic
- **`color`**: Uses color-based detection to find the dark blue overlay
- **`template`**: Uses template matching (experimental)
- **`heuristic`**: Uses fixed position based on typical Valorant UI layout

### In Jupyter Notebook

The notebook includes cells to crop timer regions interactively:

```python
from crop_timer_notebook import crop_timer_region, batch_crop_timers

# Crop single image with preview
crop_timer_region('screenshot.jpg', show_preview=True)

# Batch crop all screenshots
batch_crop_timers('screenshots/', 'cropped_timers/')
```

## Dataset Preparation

To train the model, you need to organize your timer screenshots in the following structure:

```
data/
  train/
    1_14/          # Images showing timer at 1:14
      image1.jpg
      image2.jpg
      ...
    1_13/          # Images showing timer at 1:13
      image1.jpg
      ...
    0_45/          # Images showing timer at 0:45
      ...
    0_44/
      ...
  test/
    1_14/
      ...
    1_13/
      ...
```

### Important Notes:

1. **Folder naming**: Use underscores instead of colons (e.g., `1_14` instead of `1:14`) because colons can cause issues with file systems.

2. **Image format**: Supported formats include JPG, PNG, etc. Make sure images are cropped to show only the timer region.

3. **Minimum dataset size**: 
   - Aim for at least 10-20 images per time value for training
   - 3-5 images per time value for testing
   - More data = better accuracy

4. **Time values to include**: 
   - Common timer values range from `0:00` to `1:40` (100 seconds)
   - Focus on values you see most frequently in matches
   - You don't need every single second - every 2-3 seconds is usually sufficient

## Training Steps

1. **Collect screenshots**: Take screenshots from Valorant matches showing the timer
2. **Crop timer regions**: Use `crop_timer.py` to automatically extract timer regions
3. **Organize your data**: Manually sort cropped images into folders by time value (see Dataset Preparation above)
4. **Train the model**: Run the notebook to train your model

2. **Run the notebook**: Open `Model_Maker_Text_Classification_Tutorial.ipynb` and run all cells.

3. **Adjust parameters** (if needed):
   - `epochs`: Increase for better accuracy (default: 10)
   - `batch_size`: Adjust based on your GPU memory (default: 32)
   - `DATA_DIR`: Update to your actual data path

4. **Export model**: The trained model will be exported as `valorant_timer_model/model.tflite`

## Using the Model

The exported TensorFlow Lite model can be integrated into:
- Android apps using TensorFlow Lite Task Library
- iOS apps using TensorFlow Lite
- Python applications using TensorFlow Lite interpreter

## Model Architecture

The notebook uses **EfficientNet-Lite0**, which is optimized for mobile devices:
- Small model size (< 5MB)
- Fast inference
- Good accuracy for image classification tasks

## Next Steps

1. Collect timer screenshots from Valorant matches
2. Crop them to show only the timer region
3. Organize them into the folder structure above
4. Run the training notebook
5. Test the exported model on new screenshots

