from openai import OpenAI
from json import dumps, loads
from pypdf import PdfReader
from pprint import pp
from pydantic import BaseModel, TypeAdapter
from typing import Optional

class Chunk(BaseModel):
    text: str
    footnotes: list[str]

class ChunkingResponse(BaseModel):
    expanded_chunk: Optional[Chunk]
    new_chunks: list[Chunk]


client = OpenAI()

def do_page(page: str, last_chunk: Optional[Chunk]) -> ChunkingResponse:
    system = """
    You are being tasked with chunking a document for ingestion into a database.
    You will receive a page from a PDF document, and optionally the final text chunk from the previous page as `last_chunk`.

    Your task is to:
    1. Divide the body text from thepage into consecutive chunks between 250-1000 words each
    2. Place chunk boundaries at natural semantic breaks (e.g., between sections, paragraphs, or complete ideas)
    3. If the start of the current page continues a thought from `last_chunk`, combine them into `expanded_chunk`, and do not include it in `new_chunks`

    Requirements:
    - Include every word from the document body (no gaps between chunks)
    - Use only verbatim text (no paraphrasing or editorial additions)
    - Exclude author lists and bibliography sections
    - Do not add titles or word counts to chunks
    - Include the text of footnotes in the chunk where they are referenced. Include the text of the footnote, not the number.
    - Do not include citations as footnotes. 
    - Do not include line from the end of regular lines. Include linebreaks where they represent a paragraph break.
    Return a JSON object with this structure:
    {
        "expanded_chunk": {
            "text": "Text combining last_chunk with the start of current page",
            "footnotes": ["Text of footnote 1", "Text of footnote 2", ...]
        } or null,
        "new_chunks": [
            {
                "text": "First complete chunk of text",
                "footnotes": ["Text of footnote 3", "Text of footnote 4", ...]
            },
            {
                "text": "Second chunk of text",
                "footnotes": []
            },
            ...
        ]
    }

    Return only the JSON object, with no additional explanation or commentary.
    """
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": system},
            {"role": "user", "content": dumps({"page": page, "last_chunk": last_chunk})}
        ],
        response_format=ChunkingResponse
    )
    
    return response.choices[0].message.parsed


reader = PdfReader("/home/chandler/software1-3.pdf")
ret: list[Chunk] = []
for page in reader.pages:
    print("doing page")
    response = do_page(page.extract_text(), ret[-1].model_dump() if ret else None)
    if response.expanded_chunk and ret:
        ret[-1] = response.expanded_chunk
    ret += response.new_chunks
   
breakpoint()
with open("/home/chandler/chunked.json", "w") as f:
    f.write(dumps([chunk.model_dump() for chunk in ret]))

# class ChunkingResponse(BaseModel):
#     expanded_chunk: Optional[Chunk]
#     new_chunks: list[Chunk]

# client = genai.Client(api_key="AIzaSyDXj_leg746kNrJIxtnBA_1uL4N-lDKNIM")
# def do_page(page: str, last_chunk: Optional[Chunk]) -> ChunkingResponse:
#     system = """
#     You are being tasked with chunking a document for ingestion into a database.
#     You will receive a page from a PDF document, and optionally the final text chunk from the previous page as `last_chunk`.

#     Your task is to:
#     1. Divide the page's text into consecutive chunks between 250-1000 words each
#     2. Place chunk boundaries at natural semantic breaks (e.g., between sections, paragraphs, or complete ideas)
#     3. If the start of the current page continues a thought from `last_chunk`, combine them into `expanded_chunk`

#     Requirements:
#     - Include every word from the document body (no gaps between chunks)
#     - Use only verbatim text (no paraphrasing or editorial additions)
#     - Exclude author lists and bibliography sections
#     - Do not add titles or word counts to chunks
#     - Include footnotes in the chunk where they are referenced
#     - Do not include line breaks
#     Return a JSON object with this structure:
#     ```json
#     {
#         "expanded_chunk": {
#             "text": "Text combining last_chunk with the start of current page",
#             "footnotes": ["Footnote 1", "Footnote 2", ...]
#         } or null,
#         "new_chunks": [
#             {
#                 "text": "First complete chunk of text",
#                 "footnotes": ["Footnote 3", "Footnote 4", ...]
#             },
#             {
#                 "text": "Second chunk of text",
#                 "footnotes": []
#             },
#             ...
#         ]
#     }
#     ```

#     Return only the JSON object, with no additional explanation or commentary.
#     """
#     response = client.models.generate_content(
#         model="gemini-2.0-flash",  # Replace with your desired model
#         config=genai_types.GenerateContentConfig(
#             system_instruction=system,
#             response_mime_type='application/json',
#             response_schema={'type:': 'OBJECT',
#                              'properties': {
#                                  'expanded_chunk': {'type': 'OBJECT',
#                                                     'nullable': True,
#                                                     'properties': {
#                                                         'text': {'type': 'STRING'},
#                                                         'footnotes': {'type': 'ARRAY', 'items': {'type': 'STRING'}}
#                                                     },
#                                                     'required': ['text', 'footnotes']
#                                                     },
#                                  'new_chunks': {'type': 'ARRAY',
#                                                 'items': {'type': 'OBJECT',
#                                                           'properties': {
#                                                               'text': {'type': 'STRING'},
#                                                               'footnotes': {'type': 'ARRAY', 'items': {'type': 'STRING'}}
#                                                             },
#                                                             'required': ['text', 'footnotes']
#                                                             },

#                              },
#                              'required': ['new_chunks', 'expanded_chunk']
#                              }}
#         ),
#         contents= [dumps({"page": page, "last_chunk": last_chunk})]
#     )
    
#     # The response object contains a list of choices. Each choice has a message.
#     # Here we parse the content of the first choice.
#     return ChunkingResponse.model_validate_json(response.text)

