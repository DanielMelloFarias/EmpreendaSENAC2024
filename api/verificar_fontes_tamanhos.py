from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_pages
from typing import Iterable, Any
import tempfile
import os
import shutil

app = FastAPI()

def show_ltitem_hierarchy(o: Any, depth=0, page_num=0, errors=None):
    if errors is None:
        errors = []

    if hasattr(o, 'fontname') and hasattr(o, 'size'):
        if 'Arial' not in o.fontname or o.size < 9.:
            errors.append({
                'page': page_num,
                'text': get_optional_text(o),
                'fontname': o.fontname,
                'size': o.size,
                'error': 'Fonte diferente de Arial' if 'Arial' not in o.fontname else 'Tamanho inferior a 10'
            })

    if isinstance(o, Iterable):
        for i in o:
            show_ltitem_hierarchy(i, depth=depth + 1, page_num=page_num, errors=errors)

    return errors

def get_optional_text(o: Any) -> str:
    if hasattr(o, 'get_text'):
        return o.get_text().strip()
    return ''

@app.post("/api/verificar_fontes_tamanhos/")
async def verificar_fontes_tamanhos(file: UploadFile = File(...)):
    # Verifica se o arquivo é um PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Formato de arquivo não é PDF")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            erros = []
            for pagina_num, pagina in enumerate(extract_pages(file_path), start=1):
                erros += show_ltitem_hierarchy(pagina, page_num=pagina_num)

            if erros:
                return JSONResponse(content={"message": "Erros encontrados nas fontes e tamanhos", "errors": erros})
            else:
                return JSONResponse(content={"message": "Todas as fontes estão em Arial e o tamanho é 10 ou maior ✔️."})

        except Exception as e:
            return JSONResponse(content={"message": f"Erro ao tentar verificar as fontes e tamanhos: {e}"})
