import base64
import json
import os
import configparser
from anthropic import Anthropic
from typing import Dict, Any, Optional, List
import logging
###added
from PIL import Image

logger = logging.getLogger(__name__)

def extract_text_from_image(image_file) -> Dict[str, Any]:
    """
    Extract text from an image using Claude 3.5 Sonnet API.

    Args:
        image_path (str): Path to the image file.

    Returns:
        Dict[str, Any]: JSON response containing extracted text and metadata.
    """
    # Read API key from config file
    api_key = os.getenv('ANTHROPIC_API_KEY')

    anthropic = Anthropic(api_key=api_key)

    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": encoded_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "This image is handwritten notes. Extract notes in JSON format."
                    }
                ]
            }
        ]
    )

    # Log the response content for debugging
    logger.debug(f"OCR API response: {response.content}")

    # Parse and return the JSON response
    try:
        # Check if the response content is a list and has at least one element
        if isinstance(response.content, list) and len(response.content) > 0:
            extracted_text = json.loads(response.content[0].text)
            return extracted_text
        else:
            logger.error("Unexpected response format from OCR API")
            raise ValueError("Unexpected response format from OCR API")
    except (json.JSONDecodeError, IndexError) as e:
        logger.error("Invalid response from OCR API", exc_info=True)
        raise ValueError("Invalid response from OCR API") from e
        
'''
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
        print(f"Image preprocessing error: {e}")
        return None

def extract_text_from_image(api_key: str, image_path: str) -> Optional[str]:
    """
    Extract text from an image using Claude 3.5 Sonnet.
    
    :param api_key: Anthropic API key
    :param image_path: Path to the image file
    :return: Extracted text or None if extraction fails
    """
    # Initialize the Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Preprocess the image
    base64_image = validate_and_preprocess_image(image_path)
    
    if not base64_image:
        print("Image preprocessing failed.")
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
        
        # Return the extracted text
        return response.content[0].text
    
    except Exception as e:
        print(f"Text extraction error: {e}")
        return None

def save_extracted_text(text: str, output_path: Optional[str] = None) -> None:
    """
    Save extracted text to a file or print to console.
    
    :param text: Extracted text
    :param output_path: Optional path to save the text file
    """
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Text saved to {output_path}")
        except Exception as e:
            print(f"Error saving text file: {e}")
    else:
        print("Extracted Text:\n", text)

        '''