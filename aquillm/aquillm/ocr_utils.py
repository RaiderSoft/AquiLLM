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
                        "text": "This image is handwritten notes. Just extract what is written on the page, no extra comments please."
                    }
                ]
            }
        ]
    )

    # Log the response content for debugging
    logger.debug(f"OCR API response: {response.content}")

    # Process the response
    try:
        # Claude returns plain text, not JSON
        extracted_text = response.content[0].text if response.content else ""
        return {"extracted_text": extracted_text}
    except Exception as e:
        logger.error("Error processing OCR API response", exc_info=True)
        raise ValueError("Error processing OCR API response") from e
        
