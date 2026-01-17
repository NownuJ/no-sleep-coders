import fitz  # PyMuPDF
import re


def extract_formulas(text):
    """Extract LaTeX formulas from text"""
    if not text:
        return []
    
    patterns = [
        r'\$\$[^\$]+\$\$',  # Display math $$...$$
        r'\$[^\$]+\$',      # Inline math $...$
        r'\\begin\{equation\}.*?\\end\{equation\}',
        r'\\begin\{align\*?\}.*?\\end\{align\*?\}',
        r'\\begin\{matrix\}.*?\\end\{matrix\}',
        r'\\[.*?\\]',       # Display math \[...\]
    ]
    
    formulas = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        formulas.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_formulas = []
    for f in formulas:
        if f not in seen:
            seen.add(f)
            unique_formulas.append(f)
    
    return unique_formulas


def extract_definitions(text):
    """Detect if text contains definition patterns"""
    if not text:
        return False
    
    patterns = [
        r'is defined as',
        r'is called',
        r'^Definition[:\s]',
        r':=',
        r'\\equiv',
        r'\\triangleq',
        r'denote',
        r'let .* be',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
            return True
    
    return False


def parse_pdf_to_pages(pdf_path: str):
    """
    Parse PDF and extract structured content per page
    Returns list of page objects with text, formulas, headings, images
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_num, page in enumerate(doc):
        text_dict = page.get_text("dict")

        # Extract text blocks
        blocks = text_dict.get("blocks", [])
        text_blocks = []
        headings = []

        for b in blocks:
            if b.get("type") != 0:  # 0 = text, 1 = image
                continue
            
            # Collect spans with font size info
            block_text = []
            max_size = 0

            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    s = span.get("text", "")
                    size = span.get("size", 0)
                    max_size = max(max_size, size)
                    if s.strip():
                        block_text.append(s)

            joined = " ".join(block_text).strip()
            
            if joined:
                text_blocks.append({
                    "text": joined,
                    "bbox": b.get("bbox"),
                    "max_font_size": max_size
                })

                # Heading detection (font size >= 14)
                if max_size >= 14:
                    headings.append({
                        "text": joined[:120],  # Truncate long headings
                        "font_size": max_size,
                        "bbox": b.get("bbox")
                    })

        # Combine all text for analysis
        full_page_text = " ".join([b["text"] for b in text_blocks])
        
        # Extract formulas
        formulas = extract_formulas(full_page_text)
        
        # Check for definitions
        has_definition = extract_definitions(full_page_text)
        
        # Extract images (metadata only for now)
        images = []
        for img in page.get_images(full=True):
            xref = img[0]
            images.append({
                "xref": xref,
                "width": img[2],
                "height": img[3]
            })

        # Determine section title (use first heading if available)
        section_title = headings[0]["text"] if headings else f"Page {page_num + 1}"

        pages.append({
            "page": page_num,
            "section_title": section_title,
            "text_blocks": text_blocks,
            "headings": headings,
            "images": images,
            "full_text": full_page_text,
            "formulas": formulas,
            "has_formula": len(formulas) > 0,
            "has_definition": has_definition,
            "word_count": len(full_page_text.split())
        })

    doc.close()
    return pages