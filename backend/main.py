from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List
import os
import uuid
import json
from dotenv import load_dotenv

from services.parser import parse_pdf_to_pages
from services.ranking import rank_pages_by_importance, select_top_chunks
from services.gemini_client import generate_cheatsheet
from services.output_generator import generate_markdown, generate_pdf

# Load environment variables
load_dotenv()

app = FastAPI(title="Cheatsheet Generator API")

# CORS - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
UPLOAD_DIR = "storage/uploads"
PARSED_DIR = "storage/parsed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "Cheatsheet Generator API",
        "version": "1.0.0"
    }


@app.post("/parse")
async def parse(
    files: List[UploadFile] = File(...),
    doc_type: str = Form("cheatsheet")
):
    """
    Step 1: Upload and parse PDFs
    Returns job_id for tracking
    """
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files allowed")
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    for f in files:
        if not f.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {f.filename}. Only PDFs allowed.")

    # Create job
    job_id = str(uuid.uuid4())
    job_out_dir = os.path.join(PARSED_DIR, job_id)
    os.makedirs(job_out_dir, exist_ok=True)

    total_pages = 0
    outputs = []

    # Process each PDF in order
    for i, f in enumerate(files):
        filename = f"{i:02d}_{f.filename}"
        save_path = os.path.join(UPLOAD_DIR, f"{job_id}_{filename}")

        # Save uploaded file
        with open(save_path, "wb") as out:
            content = await f.read()
            out.write(content)

        # Parse PDF
        try:
            pages = parse_pdf_to_pages(save_path)
            total_pages += len(pages)

            # Save parsed data
            out_json = {
                "job_id": job_id,
                "doc_type": doc_type,
                "pdf_index": i,
                "pdf_name": f.filename,
                "pages": pages
            }

            out_path = os.path.join(job_out_dir, f"pdf_{i:02d}.json")
            with open(out_path, "w", encoding="utf-8") as fp:
                json.dump(out_json, fp, ensure_ascii=False, indent=2)

            outputs.append({
                "pdf_index": i,
                "pdf_name": f.filename,
                "pages": len(pages)
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing {f.filename}: {str(e)}")

    return {
        "job_id": job_id,
        "doc_type": doc_type,
        "pdfs": outputs,
        "pages_total": total_pages,
        "status": "parsed"
    }


@app.post("/generate")
async def generate(job_id: str = Form(...)):
    """
    Step 2: Generate cheatsheet from parsed PDFs
    Uses Gemini API with moderate compression
    """
    job_dir = os.path.join(PARSED_DIR, job_id)
    
    if not os.path.exists(job_dir):
        raise HTTPException(status_code=404, detail="Job not found. Please upload PDFs first.")
    
    # Check if Gemini API key is set
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY in .env file"
        )
    
    # Load all parsed pages
    all_pages = []
    doc_type = "cheatsheet"
    
    json_files = sorted([f for f in os.listdir(job_dir) if f.endswith(".json") and f.startswith("pdf_")])
    
    if not json_files:
        raise HTTPException(status_code=404, detail="No parsed data found for this job")
    
    for filename in json_files:
        with open(os.path.join(job_dir, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            doc_type = data.get("doc_type", "cheatsheet")
            # Add metadata to each page
            for page in data["pages"]:
                page["pdf_name"] = data["pdf_name"]
                page["pdf_index"] = data["pdf_index"]
            all_pages.extend(data["pages"])
    
    if not all_pages:
        raise HTTPException(status_code=404, detail="No pages found in parsed data")
    
    try:
        # Rank pages by importance
        ranked_pages = rank_pages_by_importance(all_pages)
        
        # Select top chunks (moderate approach - ~80-100 pages)
        top_pages = select_top_chunks(ranked_pages, max_pages=80)
        
        # Generate with Gemini API
        result = generate_cheatsheet(top_pages, doc_type)
        
        # Check for errors
        if "error" in result:
            raise HTTPException(status_code=500, detail=f"Gemini API error: {result['error']}")
        
        # Save result
        output_path = os.path.join(job_dir, "cheatsheet.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save metadata
        meta_path = os.path.join(job_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "pages_total": len(all_pages),
                "pages_selected": len(top_pages),
                "doc_type": doc_type,
                "sections": len(result.get("sections", []))
            }, f, indent=2)
        
        return {
            "job_id": job_id,
            "status": "success",
            "pages_processed": len(all_pages),
            "pages_selected": len(top_pages),
            "sections_generated": len(result.get("sections", [])),
            "preview": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.get("/download/{job_id}")
async def download(job_id: str, format: str = "markdown"):
    """
    Step 3: Download generated cheatsheet
    Formats: markdown, json, pdf
    """
    result_path = os.path.join(PARSED_DIR, job_id, "cheatsheet.json")
    
    if not os.path.exists(result_path):
        raise HTTPException(
            status_code=404,
            detail="Cheatsheet not found. Please generate it first using /generate endpoint."
        )
    
    # Load cheatsheet data
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Generate requested format
    if format == "markdown":
        md_content = generate_markdown(data)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=cheatsheet.md"}
        )
    
    elif format == "json":
        return Response(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=cheatsheet.json"}
        )
    
    elif format == "pdf":
        try:
            pdf_bytes = generate_pdf(data)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=cheatsheet.pdf"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: markdown, json, or pdf")


@app.get("/status/{job_id}")
async def status(job_id: str):
    """Check status of a job"""
    job_dir = os.path.join(PARSED_DIR, job_id)
    
    if not os.path.exists(job_dir):
        return {"status": "not_found"}
    
    has_parsed = any(f.startswith("pdf_") and f.endswith(".json") for f in os.listdir(job_dir))
    has_cheatsheet = os.path.exists(os.path.join(job_dir, "cheatsheet.json"))
    
    meta_path = os.path.join(job_dir, "metadata.json")
    metadata = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            metadata = json.load(f)
    
    return {
        "job_id": job_id,
        "parsed": has_parsed,
        "generated": has_cheatsheet,
        "metadata": metadata
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)