import base64
import os
from pathlib import Path
from typing import Optional
from anthropic import Anthropic
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def validate_and_preprocess_image(image_path: str) -> Optional[str]:
    """
    Validate and preprocess the image before OCR.
    
    :param image_path: Path to the image file
    :return: Base64 encoded image or None if invalid
    """
    try:
        # Open and validate image
        with Image.open(image_path) as img:
            # Check image size and convert to optimal format
            max_size = 5 * 1024 * 1024  # 5MB max
            
            # Resize if image is too large
            if os.path.getsize(image_path) > max_size:
                img.thumbnail((2048, 2048), Image.LANCZOS)
                
                # Save to a bytes buffer
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_data = buffer.getvalue()
            else:
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
            
            # Encode to base64
            return base64.b64encode(image_data).decode('utf-8')
    
    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        return None

def extract_text_from_image(api_key: str, image_path: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Extract text from an image using Claude 3.5 Sonnet and save to a text file.
    
    :param api_key: Anthropic API key
    :param image_path: Path to the image file
    :param output_path: Optional path to save the text file
    :return: Extracted text or None if extraction fails
    """
    logger.debug(f"Extracting text from image: {image_path}")
    
    # Initialize the Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Preprocess the image
    base64_image = validate_and_preprocess_image(image_path)
    
    if not base64_image:
        logger.error("Image preprocessing failed.")
        return None
    
    try:
        # Send request to Claude 3.5 Sonnet
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Please perform a comprehensive text extraction from this image. "
                                "I want you to:\n"
                                "1. Extract ALL visible text, including headers, captions, labels\n"
                                "2. Preserve the original formatting and layout as much as possible\n"
                                "3. If text is in multiple columns or sections, clearly indicate this\n"
                                "4. Note any special formatting like bold, italics, or different font sizes\n"
                                "5. If some text is unclear, mention 'Partially legible' or 'Text partially obscured'"
                            )
                        }
                    ]
                }
            ]
        )
        
        # Extracted text
        extracted_text = response.content[0].text
        
        # Save the extracted text to a file if output_path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            logger.debug(f"Text saved to {output_path}")
        
        return extracted_text
    
    except Exception as e:
        logger.error(f"Text extraction error: {e}")
        return None