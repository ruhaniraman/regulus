import numpy as np
import cv2
import tensorflow as tf
from tqdm import tqdm

# --- 1. CONFIGURATION & MODEL LOADING ---

# Define the input size for the model. Must match the training TILE_SIZE.
IMAGE_SIZE = 256

# Load the trained model. This is done once when the script is imported.
print("Loading trained model...")
MODEL = tf.keras.models.load_model('mining_detector.h5')
print("Model loaded successfully!")


def detect_mines(image_path):
    """
    Detects mining areas in a large satellite image.

    Args:
        image_path (str): The file path to the satellite image to be analyzed.

    Returns:
        numpy.ndarray: A full-size black and white mask image where white pixels
                       indicate detected mining areas. The array is of type uint8.
    """
    
    # --- 2. READ AND PREPARE THE INPUT IMAGE ---
    
    # Read the image using OpenCV
    large_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    
    if large_image is None:
        raise IOError(f"Could not read the image file at: {image_path}")
        
    # Normalize the image to the [0, 1] range, same as training data.
    large_image = large_image / 255.0
    
    # Get the original image dimensions
    original_height, original_width, _ = large_image.shape
    
    # Create an empty canvas to stitch the predicted tiles back together.
    predicted_mask = np.zeros((original_height, original_width), dtype=np.float32)

    print(f"\nAnalyzing '{image_path}'...")
    
    # --- 3. PREDICT ON TILES AND STITCH RESULTS ---
    
    # Iterate over the large image in steps of TILE_SIZE.
    # The tqdm wrapper will show a nice progress bar.
    for y in tqdm(range(0, original_height, IMAGE_SIZE)):
        for x in range(0, original_width, IMAGE_SIZE):
            # Define the boundaries of the tile.
            y_end = y + IMAGE_SIZE
            x_end = x + IMAGE_SIZE
            
            # Extract the tile from the large image.
            # Handle edge cases where the tile might be smaller than IMAGE_SIZE.
            tile = large_image[y:y_end, x:x_end]
            tile_height, tile_width, _ = tile.shape

            # If the tile is smaller than the required size, pad it with zeros.
            if tile_height != IMAGE_SIZE or tile_width != IMAGE_SIZE:
                padded_tile = np.zeros((IMAGE_SIZE, IMAGE_SIZE, 3), dtype=np.float32)
                padded_tile[:tile_height, :tile_width, :] = tile
                tile = padded_tile

            # The model expects a batch of images, so we add an extra dimension.
            # Shape changes from (256, 256, 3) to (1, 256, 256, 3).
            tile_for_prediction = np.expand_dims(tile, axis=0)

            # Run the prediction on the tile.
            predicted_tile = MODEL.predict(tile_for_prediction, verbose=0)[0]
            
            # Squeeze the extra dimensions from the prediction.
            predicted_tile = np.squeeze(predicted_tile)
            
            # Place the predicted tile onto our full-size mask canvas.
            # Make sure to only place the valid part of the tile if it was padded.
            predicted_mask[y:y_end, x:x_end] = predicted_tile[:tile_height, :tile_width]

    # --- 4. POST-PROCESS THE MASK ---

    # Apply a threshold and scale the mask to the 0-255 range.
    binary_mask = (predicted_mask > 0.45).astype(np.uint8) * 255
    
    # --- 5. CLEAN UP THE MASK (NEW STEP) ---
    
    print("Cleaning up the mask with morphological operations...")
    
    # Define a kernel (a small matrix for the filter). 5x5 is a good size.
    kernel = np.ones((5, 5), np.uint8)
    
    # 1. Opening: Removes small white noise points from the background.
    opening = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # 2. Closing: Fills in small black holes inside the main white areas.
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    final_mask = closing # This is now our cleaned-up mask
    
    print("\nAnalysis complete! ✨")
    return final_mask