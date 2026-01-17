import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT
from io import BytesIO


def generate_markdown(cheatsheet_data):
    """Convert JSON cheatsheet to Markdown format"""
    md = f"# {cheatsheet_data.get('title', 'Cheatsheet')}\n\n"
    md += "---\n\n"
    
    for section in cheatsheet_data.get("sections", []):
        md += f"## {section.get('heading', 'Section')}\n\n"
        
        for bullet in section.get("bullets", []):
            page = bullet.get("page", "?")
            text = bullet.get("text", "")
            bullet_type = bullet.get("type", "concept")
            formulas = bullet.get("formulas", [])
            
            # Add bullet with page reference
            md += f"- **{text}** *(p.{page})*\n"
            
            # Add formulas if present
            if formulas:
                for formula in formulas:
                    md += f"  - {formula}\n"
            
            md += "\n"
        
        md += "---\n\n"
    
    return md


def generate_pdf(cheatsheet_data):
    """
    Generate PDF from cheatsheet data
    Returns PDF as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1a1a1a',
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#2c3e50',
        spaceAfter=6,
        spaceBefore=12,
        alignment=TA_LEFT
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    formula_style = ParagraphStyle(
        'Formula',
        parent=styles['Code'],
        fontSize=9,
        leftIndent=40,
        spaceAfter=4,
        textColor='#c0392b'
    )
    
    # Build PDF content
    story = []
    
    # Title
    title = cheatsheet_data.get('title', 'Cheatsheet')
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # Sections
    for section in cheatsheet_data.get("sections", []):
        # Section heading
        heading = section.get('heading', 'Section')
        story.append(Paragraph(heading, heading_style))
        story.append(Spacer(1, 6))
        
        # Bullets
        for bullet in section.get("bullets", []):
            page = bullet.get("page", "?")
            text = bullet.get("text", "")
            formulas = bullet.get("formulas", [])
            
            # Escape special characters for ReportLab
            text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Bullet text with page reference
            bullet_text = f"• {text_escaped} <i>(p.{page})</i>"
            story.append(Paragraph(bullet_text, bullet_style))
            
            # Formulas
            for formula in formulas:
                formula_escaped = formula.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"  {formula_escaped}", formula_style))
            
            story.append(Spacer(1, 3))
        
        story.append(Spacer(1, 12))
    
    # Build PDF
    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")
