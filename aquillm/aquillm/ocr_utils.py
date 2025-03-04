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

def extract_text_from_image(image_file, convert_to_latex=False) -> Dict[str, Any]:
    """
    Extract text from an image using Claude 3.5 Sonnet API, with optional LaTeX conversion.

    Args:
        image_file: The image file to process.
        convert_to_latex (bool): Whether to convert the text to LaTeX format.

    Returns:
        Dict[str, Any]: Dictionary containing extracted text and LaTeX if requested.
    """
    # Read API key from config file
    api_key = os.getenv('ANTHROPIC_API_KEY')
    anthropic = Anthropic(api_key=api_key)

    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Customize prompt based on whether LaTeX conversion is requested
    if convert_to_latex:
        prompt = "This image contains handwritten notes with mathematical content. First, extract the text content. Then, convert it to proper LaTeX format. Pay special attention to mathematical expressions, equations, and symbols. For mathematical expressions, use dollar signs like $y = mx + b$. Return both versions as: PLAIN TEXT: [text] LATEX: [latex]"
    else:
        prompt = "This image is handwritten notes. Just extract what is written on the page, no extra comments please."

    response = anthropic.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1500,  # Increased for LaTeX conversion
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
                        "text": prompt
                    }
                ]
            }
        ]
    )

    # Log the response content for debugging
    logger.debug(f"OCR API response: {response.content}")

    # Process the response
    try:
        response_text = response.content[0].text if response.content else ""
        
        if convert_to_latex:
            # Parse the response to extract plain text and LaTeX
            if "PLAIN TEXT:" in response_text and "LATEX:" in response_text:
                parts = response_text.split("LATEX:", 1)
                plain_text_part = parts[0].split("PLAIN TEXT:", 1)[1].strip()
                latex_text = parts[1].strip()
                return {
                    "extracted_text": plain_text_part,
                    "latex_text": latex_text
                }
            else:
                # Fallback if the response doesn't follow the expected format
                return {
                    "extracted_text": response_text,
                    "latex_text": response_text  # Use the same text as fallback
                }
        else:
            return {"extracted_text": response_text}
    except Exception as e:
        logger.error("Error processing OCR API response", exc_info=True)
        raise ValueError("Error processing OCR API response") from e
        
