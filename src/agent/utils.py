import re
import json
import os
from typing import Optional, Dict, Any

def read_markdown_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_json(json_str: str) -> dict:
    json_match = re.search(r"```json\n(.*?)\n```", json_str, re.DOTALL)
    raw_json_string = json_match.group(1) if json_match else json_str

    try:
        return json.loads(raw_json_string)
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from LLM: {e}")
        return None

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), '../prompts/scraper') 

def build_scraper_prompt(scraper_output_json_schema: Optional[Dict[str, Any]] = None) -> str:
    """
    Dynamically assembles the scraper system prompt from template files
    based on whether a JSON schema is provided.
    """
    base_template = read_markdown_file(os.path.join(PROMPTS_DIR, "scraper.md"))

    if scraper_output_json_schema:
        instruction_template = read_markdown_file(os.path.join(PROMPTS_DIR, "scraper_schema.md"))
        schema_as_string = json.dumps(scraper_output_json_schema, indent=2)
        instructions = instruction_template.replace("[JSON_SCHEMA_HERE]", schema_as_string)
    else:
        instructions = read_markdown_file(os.path.join(PROMPTS_DIR, "scraper_non_schema.md"))

    final_prompt = base_template.replace("[OUTPUT_FORMAT_INSTRUCTIONS]", instructions)
    return final_prompt