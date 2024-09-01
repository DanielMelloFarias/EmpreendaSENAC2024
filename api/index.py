from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Monta a pasta 'static' para servir arquivos estáticos como o index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    with open("static/index.html", "r") as file:
        return file.read()

@app.get("/teste", response_class=HTMLResponse)
async def read_root():
    # Carrega o arquivo index.html que estará na pasta 'static'
    with open("static/index.html", "r") as file:
        return file.read()
    
@app.get("/testh")
async def read_root():
    return {"message": "OI"}

# Importando os endpoints de cada API
from verificar_pdf_a4_paginas import verificar_pdf_a4_paginas
from verificar_capa import verificar_capa
from verificar_fontes_tamanhos import verificar_fontes_tamanhos

# Monta as rotas para as APIs
app.include_router(verificar_pdf_a4_paginas.router)
app.include_router(verificar_capa.router)
app.include_router(verificar_fontes_tamanhos.router)
