import base64
import json
import os
import configparser
from typing import Dict, Any, Optional, List
import logging
###added
from dotenv import load_dotenv
import google.generativeai as genai
from django.conf import settings  # Import Django settings

load_dotenv()

logger = logging.getLogger(__name__)

def extract_text_from_image(image_file) -> Dict[str, Any]:
    """
    Extract text from an image using Gemini API.

    Args:
        image_file (file): Image file object.

    Returns:
        Dict[str, Any]: JSON response containing extracted text and metadata.
    """
    # Get the API key from environment variables
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")

    # Configure the generative AI with the API key
    genai.configure(api_key=api_key)

   # Get the temporary image path from Django settings or use a default
    temp_image_path = getattr(settings, 'TEMP_IMAGE_PATH', os.path.join(settings.BASE_DIR, 'tmp', 'temp_image.jpg'))
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)
    
    with open(temp_image_path, "wb") as temp_image_file:
        temp_image_file.write(image_file.read())
    # Upload the file to Gemini
    sample_file = genai.upload_file(path=temp_image_path, display_name="Uploaded Image")
    logger.debug(f"Uploaded file '{sample_file.display_name}' as: {sample_file.uri}")

    # Choose a Gemini model
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")

    # Prompt the model with text and the previously uploaded image
    prompt = "Extract the exact text from the image, nothing else"
    response = model.generate_content([sample_file.uri, prompt])

    # Log the response content for debugging
    logger.debug(f"OCR API response: {response.text}")

    # Parse and return the JSON response
    try:
        extracted_text = json.loads(response.text)
        return extracted_text
    except json.JSONDecodeError as e:
        logger.error("Invalid response from OCR API", exc_info=True)
        raise ValueError("Invalid response from OCR API") from e