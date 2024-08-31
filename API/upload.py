from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pdfplumber
import PyPDF2
import os

app = FastAPI()

# Função para verificar se a extensão do arquivo é PDF
def check_extension(file_name):
    return file_name.lower().endswith('.pdf')

# Função para verificar se as páginas estão no formato A4
def check_page_format(pdf):
    for page in pdf.pages:
        width, height = page.width, page.height
        if not (590 < width < 595 and 840 < height < 845):
            return False
    return True

# Função para verificar a fonte e o tamanho da fonte
def check_font_and_size(pdf):
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            font_data = page.extract_words()
            for word in font_data:
                if word['fontname'].lower() != 'arial' or int(word['size']) < 10:
                    return False
    return True

# Função para contar o número de páginas
def check_page_count(file):
    reader = PyPDF2.PdfFileReader(file)
    return reader.getNumPages() <= 22

# Função para extrair o texto da capa
def extract_cover_text(pdf):
    if len(pdf.pages) > 0:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        return text
    return None

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not check_extension(file.filename):
        raise HTTPException(status_code=400, detail="Formato de arquivo não é PDF")

    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    with pdfplumber.open(file_path) as pdf:
        if not check_page_format(pdf):
            raise HTTPException(status_code=400, detail="Páginas não estão no formato A4")
        if not check_font_and_size(pdf):
            raise HTTPException(status_code=400, detail="Fonte incorreta ou tamanho inferior a 10")
        if not check_page_count(open(file_path, "rb")):
            raise HTTPException(status_code=400, detail="Número de páginas excede o limite de 22")

        cover_text = extract_cover_text(pdf)
        if cover_text:
            return JSONResponse(content={"message": "Arquivo em conformidade", "cover_text": cover_text})
        else:
            raise HTTPException(status_code=400, detail="Não foi possível extrair o texto da capa")

@app.get("/")
async def root():
    return {"message": "Oi"}

