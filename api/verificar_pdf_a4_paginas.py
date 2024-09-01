from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
import tempfile
import os
import shutil

app = FastAPI()

@app.post("/api/verificar_pdf_a4_paginas/")
async def verificar_pdf_a4_paginas(file: UploadFile = File(...)):
    # Verifica se o arquivo é um PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Formato de arquivo não é PDF")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            with open(file_path, 'rb') as arquivo_pdf:
                leitor_pdf = PdfReader(arquivo_pdf)
                numero_paginas = len(leitor_pdf.pages)
                
                # Verificação do número de páginas
                if numero_paginas < 22:
                    paginas_status = f"O arquivo é um PDF ✔️.\nO Arquivo tem menos de 22 páginas ✔️. Total de páginas: {numero_paginas}."
                else:
                    paginas_status = f"O arquivo é um PDF ✔️.\nO Arquivo tem 22 páginas ou mais ❌. Total de páginas: {numero_paginas}."
                
                # Verificação do formato A4
                largura_a4 = 595.28
                altura_a4 = 841.89
                margem = 0.01  # 1% de margem

                largura_min = largura_a4 * (1 - margem)
                largura_max = largura_a4 * (1 + margem)
                altura_min = altura_a4 * (1 - margem)
                altura_max = altura_a4 * (1 + margem)

                for pagina in leitor_pdf.pages:
                    largura = float(pagina.mediabox[2])
                    altura = float(pagina.mediabox[3])
                    
                    if not (largura_min <= largura <= largura_max and altura_min <= altura <= altura_max):
                        return JSONResponse(content={"message": f"O documento não está no formato A4 ❌. Formato encontrado: {largura} x {altura} pontos."})

                return JSONResponse(content={"message": f"{paginas_status}\nO documento está no formato A4 ✔️."})

        except Exception as e:
            return JSONResponse(content={"message": f"Erro ao tentar ler o PDF: {e}"})
