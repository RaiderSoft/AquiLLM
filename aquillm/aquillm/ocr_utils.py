import base64
import json
import os
import configparser
from anthropic import Anthropic
from typing import Dict, Any, Optional, List
import logging
###added
from PIL import Image
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import anthropic.types
import time

logger = logging.getLogger(__name__)

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    reraise=True
)
def extract_text_from_image(image_file, convert_to_latex=False) -> Dict[str, Any]:
    """
    Extract text from an image using Claude 3.5 Sonnet API, with optional LaTeX conversion.
    
    This function utilizes Claude's vision capabilities to perform OCR (Optical Character Recognition)
    on images containing handwritten notes. When LaTeX conversion is requested, it will also
    convert mathematical expressions to proper LaTeX format with delimiters.
    
    Args:
        image_file: The image file to process (file-like object opened in binary mode).
        convert_to_latex (bool): Whether to convert mathematical content to LaTeX format.
                                This is useful for rendering equations properly.

    Returns:
        Dict[str, Any]: Dictionary containing:
            - "extracted_text": The plain text extracted from the image
            - "latex_text": The LaTeX version (only if convert_to_latex=True)
            
    Note:
        This function includes retry logic to handle rate limits and server overload errors
        from the Claude API. It will retry up to 5 times with exponential backoff.
    """
    # Get API key from environment variable
    api_key = os.getenv('ANTHROPIC_API_KEY')
    anthropic = Anthropic(api_key=api_key)

    # Convert the image to base64 format for API transmission
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Customize the prompt based on whether LaTeX conversion is requested
    if convert_to_latex:
        # When converting to LaTeX, we need to ask Claude to:
        # 1. Extract the plain text
        # 2. Convert mathematical expressions to LaTeX
        # 3. Format the response in a structured way
        prompt = (
            "This image contains handwritten notes with mathematical content. "
            "First, extract the text content. Then, convert it to proper LaTeX format. "
            "Pay special attention to mathematical expressions, equations, and symbols. "
            "For mathematical expressions, use dollar signs like $y = mx + b$ for inline math. "
            "Return both versions in this format:\n\n"
            "PLAIN TEXT: [extracted text]\n\n"
            "LATEX: [latex formatted text]"
        )
    else:
        # For plain text extraction, a simpler prompt is sufficient
        prompt = "This image is handwritten notes. Just extract what is written on the page, no extra comments please."

    try:
        # Send the image to Claude for processing
        response = anthropic.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,  
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

        # Log the response for debugging purposes
        logger.debug(f"OCR API response: {response.content}")

        # Process the API response
        response_text = response.content[0].text if response.content else ""
        
        if convert_to_latex:
            # When LaTeX conversion was requested, we need to parse the structured response
            if "PLAIN TEXT:" in response_text and "LATEX:" in response_text:
                # Split the response to extract each section
                parts = response_text.split("LATEX:", 1)
                plain_text_part = parts[0].split("PLAIN TEXT:", 1)[1].strip()
                latex_text = parts[1].strip()
                
                return {
                    "extracted_text": plain_text_part,
                    "latex_text": latex_text
                }
            else:
                # Fallback if Claude's response doesn't follow the expected format
                logger.warning("LaTeX conversion requested but response format is unexpected")
                return {
                    "extracted_text": response_text,
                    "latex_text": response_text  # Use the same text as fallback
                }
        else:
            # For plain text extraction, return the entire response
            return {"extracted_text": response_text}
            
    except anthropic.RateLimitError as e:
        logger.warning(f"Rate limit exceeded from Claude API: {str(e)}")
        raise  # Will be caught by retry decorator
    except anthropic.APIStatusError as e:
        if e.status_code == 529:  # Overloaded error
            logger.warning(f"Claude API is overloaded: {str(e)}")
        else:
            logger.error(f"API error from Claude: {str(e)}")
        raise  # Will be caught by retry decorator
    except Exception as e:
        # Detailed error logging to help diagnose issues
        logger.error("Error processing OCR API response", exc_info=True)
        raise ValueError("Error processing OCR API response") from e
        
