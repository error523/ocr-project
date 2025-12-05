# server.py
import os
import tempfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from paddleocr import PaddleOCR
import fitz  # PyMuPDF

app = FastAPI(title="PaddleOCR OCR Service")


def _make_ocr_engine() -> PaddleOCR:
    """Initialize OCR engine based on env; cached at module load."""
    use_gpu = os.getenv("USE_GPU", "false").lower() in {"1", "true", "yes"}
    lang = os.getenv("OCR_LANG", "ch")
    device = "gpu" if use_gpu else "cpu"
    return PaddleOCR(use_angle_cls=True, lang=lang, device=device)


ocr_engine = _make_ocr_engine()


def _extract_image_results(image_path: str) -> List[dict]:
    # In PaddleOCR >=3.3, angle classification is controlled by init (use_angle_cls=True)
    result = ocr_engine.ocr(image_path)
    items = []
    for line in result:
        for box, (text, score) in line:
            items.append({
                "text": text,
                "score": float(score),
                "box": box,
            })
    return items


def _ocr_pdf(pdf_path: str) -> List[dict]:
    pages_output = []
    doc = fitz.open(pdf_path)
    try:
        for page_idx, page in enumerate(doc, start=1):
            # 渲染为图片后送入 OCR；Matrix(2,2) 提升分辨率
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp:
                img_tmp.write(pix.tobytes())
                img_path = img_tmp.name
            try:
                items = _extract_image_results(img_path)
                pages_output.append({"page": page_idx, "items": items})
            finally:
                if os.path.exists(img_path):
                    os.remove(img_path)
    finally:
        doc.close()
    return pages_output


def _ocr_file(file_path: str, content_type: str) -> dict:
    if content_type == "application/pdf" or file_path.lower().endswith(".pdf"):
        return {"pages": _ocr_pdf(file_path)}
    return {"pages": [{"page": 1, "items": _extract_image_results(file_path)}]}

@app.post("/ocr")
async def ocr_file(file: UploadFile = File(...)):
    if not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported content_type: {file.content_type}"}
        )

    suffix = os.path.splitext(file.filename)[1] or (
        ".pdf" if file.content_type == "application/pdf" else ".jpg"
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        result = _ocr_file(tmp_path, file.content_type)
        return {"code": 0, **result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    index_path = Path(__file__).parent / "static" / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>Frontend missing</h1>", status_code=500)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
