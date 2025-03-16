import base64
import json
import os
import configparser
from typing import Dict, Any, Optional, List
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from django.conf import settings
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
import uuid
import threading

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiCostTracker:
    def __init__(self):
        self.total_cost = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.api_calls = 0
        self.lock = threading.Lock()
        
        self.input_cost_per_1k = 0.0005
        self.output_cost_per_1k = 0.0015
    
    def add_usage(self, input_tokens, output_tokens):
        with self.lock:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.api_calls += 1
            
            input_cost = (input_tokens / 1000) * self.input_cost_per_1k
            output_cost = (output_tokens / 1000) * self.output_cost_per_1k
            call_cost = input_cost + output_cost
            
            self.total_cost += call_cost
            
            return call_cost
    
    def get_stats(self):
        with self.lock:
            return {
                'total_cost_usd': self.total_cost,
                'input_tokens': self.input_tokens,
                'output_tokens': self.output_tokens,
                'api_calls': self.api_calls
            }

cost_tracker = GeminiCostTracker()

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
    reraise=True
)
def extract_text_from_image(image_input, convert_to_latex=False) -> Dict[str, Any]:
    """
    Extract text from an image using Gemini API.
    
    Args:
        image_input: Can be:
            - A string path to an image file
            - A file-like object with read method
            - Bytes containing the image data
        convert_to_latex: Whether to also convert mathematical notation to LaTeX
        
    Returns:
        Dictionary with extracted_text and optionally latex_text
    """
    result = {}
    
    try:
        # Handle different input types to get file_content
        if isinstance(image_input, str) and os.path.exists(image_input):
            # Path to a file
            with open(image_input, "rb") as f:
                file_content = f.read()
            file_name = os.path.basename(image_input)
        
        elif isinstance(image_input, bytes):
            # Direct bytes content
            file_content = image_input
            file_name = f"image_{uuid.uuid4().hex[:8]}"
            
        elif hasattr(image_input, 'read'):
            # File-like object
            if hasattr(image_input, 'tell'):
                position = image_input.tell()
            
            file_content = image_input.read()
            
            # No need to reset position as the caller should handle this if needed
            
            file_name = getattr(image_input, 'name', f"image_{uuid.uuid4().hex[:8]}")
            
        else:
            raise ValueError(f"Unsupported image_input type: {type(image_input)}")
        
        encoded_image = base64.b64encode(file_content).decode('utf-8')
        
    except Exception as e:
        raise ValueError(f"Could not process image file: {str(e)}")
    
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 0.0,
                "top_p": 0.5,
                "top_k": 10,
                "max_output_tokens": 2048
            }
        )
        
        text_prompt = """
        This is a STRICT OCR task. Look at the image and ONLY transcribe what is written.
        
        CRITICAL:
        - Focus on ONLY extracting text you can clearly see in the image
        - NEVER invent or imagine text that isn't there
        - If no text is visible, respond with "NO READABLE TEXT"
        - DO NOT make guesses about unclear text
        - DO NOT add any code snippets
        - DO NOT generate anything beyond what is visibly written
        
        """
        
        content_parts = [
            {
                "text": text_prompt
            },
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": encoded_image
                }
            }
        ]
        
        response = model.generate_content(content_parts)
        
        extracted_text = response.text.strip()
        result["extracted_text"] = extracted_text
        
        # Handle usage tracking with fallback for different API response structures
        if hasattr(response, 'usage'):
            cost_tracker.add_usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.candidates_tokens
            )
        else:
            # Fallback to estimation if usage data is not available
            estimated_input_tokens = len(json.dumps(content_parts)) // 4
            estimated_output_tokens = len(extracted_text) // 4
            cost_tracker.add_usage(
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens
            )
        
        if convert_to_latex:
            latex_prompt = """
            Extract and convert the equations from this image, paying special attention to vector notation. In physics/math, vectors are often indicated with small bars over letters.
            
            CRITICAL VECTOR NOTATION REQUIREMENTS:
            - In this physics/math notes image, vectors are indicated with small bars over letters
            - USE ONLY \\bar{} NOTATION, NOT \\vec{} FOR VECTORS
            - SPECIFICALLY: Convert ř to $\\bar{r}$ (not $\\vec{r}$)
            - SPECIFICALLY: Convert F̄ to $\\bar{F}$ (not $\\vec{F}$)
            - SPECIFICALLY: Convert dř to $d\\bar{r}$ (not $d\\vec{r}$)
            - Every vector symbol must have a bar in the LaTeX (not an arrow)
            
            OTHER IMPORTANT INSTRUCTIONS:
            - Extract BOTH text and mathematics exactly as shown in the image
            - Maintain the same line breaks and paragraph structure as the original
            - Only convert mathematical notation to LaTeX, leave regular text as plain text
            - For integrals with limits, use \\int_{lower}^{upper} (not \\oint)
            - For subscripts like v₂, use v_2 in LaTeX
            - Use $ symbols to delimit math expressions
            - For arrows between points (like 1→2), use $1 \\to 2$ or $W_{1\\to 2}$
            - For Greek letters: Σ should be \\Sigma, etc.
            
            EXAMPLES FROM PHYSICS/MATH NOTATION:
            - If you see "ř" in the notes, render it as $\\bar{r}$ (not $\\vec{r}$)
            - If you see "dř" in the notes, render it as $d\\bar{r}$ (not $d\\vec{r}$)
            - If you see "ΣF̄", render it as $\\Sigma\\bar{F}$ (not $\\Sigma\\vec{F}$)
            - If you see "v₂" in the notes, render it as $v_2$ (not $v2$)
            
            Go through each equation character by character and ensure every vector has a bar (\\bar{}) notation.
            """
            
            latex_content_parts = [
                {
                    "text": latex_prompt
                },
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
            
            latex_response = model.generate_content(latex_content_parts)
            
            latex_text = latex_response.text.strip()
            if latex_text and latex_text != "NO MATH CONTENT":
                result["latex_text"] = latex_text
                
            
        
        return result
            
    except Exception as e:
        raise ValueError(f"OCR processing failed: {str(e)}")
        
def get_gemini_cost_stats():
    return cost_tracker.get_stats()