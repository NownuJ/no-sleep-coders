import google.generativeai as genai
import json
import os
import re


def configure_gemini():
    """Configure Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment variables")
    genai.configure(api_key=api_key)


def fix_json_escaping(text):
    """
    Fix common JSON escaping issues with LaTeX formulas
    """
    # This is a safer approach - find strings and properly escape backslashes
    try:
        # First attempt: try to parse as-is
        return json.loads(text)
    except json.JSONDecodeError:
        # If that fails, manually escape backslashes in formula-like contexts
        # Replace single backslash with double backslash, but be careful not to double-escape
        fixed = text.replace('\\', '\\\\')
        # Fix over-escaping of already escaped characters
        fixed = fixed.replace('\\\\\\\\', '\\\\')
        fixed = fixed.replace('\\\\"', '\\"')
        fixed = fixed.replace('\\\\n', '\\n')
        fixed = fixed.replace('\\\\t', '\\t')
        return json.loads(fixed)


def generate_cheatsheet(pages, doc_type="cheatsheet"):
    """
    Generate cheatsheet from selected pages using Gemini API
    Uses moderate compression approach (full text sent)
    """
    configure_gemini()
    
    model = genai.GenerativeModel(
        'gemini-2.5-flash-lite',
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 8192,
        }
    )
    
    # Prepare content blocks (limit text per page to avoid token overflow)
    content_blocks = []
    for p in pages[:60]:  # Process max 60 pages per call
        section = p.get("section_title", "Section")
        content_blocks.append({
            "page": p.get("page", 0),
            "pdf_name": p.get("pdf_name", "unknown.pdf"),
            "section": section,
            "text": p.get("full_text", "")[:2500],  # Limit to ~2500 chars per page
            "formulas": p.get("formulas", [])[:10],  # Limit formulas
            "has_definition": p.get("has_definition", False)
        })
    
    # Create prompt based on doc_type
    if doc_type == "cheatsheet":
        instructions = """
You are creating a CONCISE exam cheatsheet (1-2 pages).

PRIORITIES:
1. Formulas and equations (CRITICAL - include ALL)
2. Key definitions
3. Important algorithms/procedures
4. Core concepts

EXCLUDE:
- Verbose explanations
- Examples (unless absolutely essential)
- Background information
"""
    else:  # notes
        instructions = """
You are creating comprehensive study notes (3-5 pages).

INCLUDE:
- All formulas and equations
- Detailed definitions
- Key examples
- Important concepts
- Brief explanations
"""

    prompt = f"""
{instructions}

STRICT RULES:
1. When including LaTeX formulas, you MUST escape backslashes for JSON (use \\\\ instead of \\)
   CORRECT: "$\\\\frac{{x}}{{y}}$" or "\\\\[x = y\\\\]"
   WRONG: "$\\frac{{x}}{{y}}$" or "\\[x = y\\]"
2. For each bullet point, include the source page number
3. Output ONLY valid JSON (no markdown, no preamble, no explanation)
4. Group related concepts under section headings

Content from {len(content_blocks)} lecture pages:
{json.dumps(content_blocks, indent=2, ensure_ascii=False)}

Output Schema (STRICT):
{{
  "title": "Module Cheatsheet",
  "sections": [
    {{
      "heading": "Section Name",
      "bullets": [
        {{
          "text": "Key point here",
          "page": 5,
          "formulas": ["$\\\\alpha = \\\\beta$"],
          "type": "definition"
        }}
      ]
    }}
  ]
}}

CRITICAL: Escape all backslashes in formulas with double backslashes (\\\\) for valid JSON.

Generate the cheatsheet now (pure JSON only):
"""
    
    try:
        response = model.generate_content(prompt)
        
        # Parse JSON response
        raw_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        
        raw_text = raw_text.strip()
        
        # Use the fixing function to handle escaping issues
        result = fix_json_escaping(raw_text)
        return result
    
    except json.JSONDecodeError as e:
        # Save the problematic response for debugging
        error_details = {
            "error": f"Failed to parse Gemini response as JSON: {str(e)}",
            "raw_response": raw_text if 'raw_text' in locals() else None,
            "error_position": f"line {e.lineno} column {e.colno}" if hasattr(e, 'lineno') else None
        }
        print("JSON Parse Error:", error_details)  # Log to console
        return error_details
    
    except Exception as e:
        error_details = {
            "error": f"Gemini API error: {str(e)}",
            "raw_response": getattr(response, 'text', None) if 'response' in locals() else None
        }
        print("General Error:", error_details)  # Log to console
        return error_details