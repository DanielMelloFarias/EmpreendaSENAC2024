from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import tempfile
import shutil
from pdfminer.high_level import extract_pages, extract_text
from PyPDF2 import PdfReader
from groq import Groq
from typing import Iterable, Any

app = FastAPI()

# Monta a pasta 'static' para servir arquivos estáticos como o index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

def perguntaGroq(textoExtraido):
    clientGroq = Groq(api_key="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")
    
    prompt = f"""
    Incorpore um especialista em verificação de Projetos. Com base no texto fornecido, identifique se estão presentes as seguintes informações:

    1. Título do Projeto: Identifique se há um título que possa ser reconhecido como o nome do projeto.
    2. Categoria Disputada: Determine se há menção a uma categoria como curso técnico, graduação, pós-graduação, ou outras especificadas posteriormente.
    3. Nome da Equipe: Verifique se há um nome que identifica uma equipe.
    4. Nomes dos Integrantes ou Nome do Integrante: Identifique se são listados os nomes dos integrantes ou de um integrante específico.
    5. Cursos que Estão Matriculados: Verifique se há menção aos cursos nos quais os integrantes estão matriculados.

    Instruções adicionais para o modelo:

    - Se um campo não estiver claramente identificado, informe que o campo não foi encontrado.
    - Responda em um formato estruturado, listando cada item como um tópico (checklist) seguido de “Encontrado” ou “Não Encontrado”. Inclua o trecho do texto correspondente, se possível.
    - Utilize ícones de check (✔️) e uncheck (❌) para indicar a presença ou ausência de cada informação.  
    - Responda em pt-br

    Texto extraído:
    {textoExtraido}
    """

    chat_completion = clientGroq.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama3-8b-8192",
    )
    
    return chat_completion.choices[0].message.content

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

def verificar_formato_a4(pdf_reader):
    largura_a4 = 595.28
    altura_a4 = 841.89
    margem = 0.01  # 1% de margem

    largura_min = largura_a4 * (1 - margem)
    largura_max = largura_a4 * (1 + margem)
    altura_min = altura_a4 * (1 - margem)
    altura_max = altura_a4 * (1 + margem)

    for pagina in pdf_reader.pages:
        largura = float(pagina.mediabox[2])
        altura = float(pagina.mediabox[3])
        
        if not (largura_min <= largura <= largura_max and altura_min <= altura <= altura_max):
            return False, largura, altura
    return True, None, None

def extrair_texto_primeira_pagina(caminho_arquivo):
    if not os.path.isfile(caminho_arquivo):
        return f"Arquivo '{caminho_arquivo}' não encontrado ❌."

    if not caminho_arquivo.lower().endswith('.pdf'):
        return "O arquivo não é um PDF ❌."

    try:
        texto_primeira_pagina = extract_text(caminho_arquivo, page_numbers=[0])
        
        if texto_primeira_pagina:
            return perguntaGroq(texto_primeira_pagina)
        else:
            return "Não foi possível extrair o texto da primeira página ou a página está vazia ❌."

    except Exception as e:
        return f"Erro ao tentar extrair o texto da primeira página: {e}"

def verificar_pdf(caminho_arquivo):
    if not os.path.isfile(caminho_arquivo):
        return f"Arquivo '{caminho_arquivo}' não encontrado ❌."

    if not caminho_arquivo.lower().endswith('.pdf'):
        return "O arquivo não é um PDF ❌."

    try:
        with open(caminho_arquivo, 'rb') as arquivo_pdf:
            leitor_pdf = PdfReader(arquivo_pdf)
            numero_paginas = len(leitor_pdf.pages)
            
            if numero_paginas < 22:
                paginas_status = f"O arquivo é um PDF ✔️.\nO Arquivo tem menos de 22 páginas ✔️. Total de páginas: {numero_paginas}."
            else:
                paginas_status = f"O arquivo é um PDF ✔️.\nO Arquivo tem 22 páginas ou mais ❌. Total de páginas: {numero_paginas}."
    
    except Exception as e:
        return f"Erro ao tentar ler o PDF: {e}"

    try:
        is_a4, largura, altura = verificar_formato_a4(leitor_pdf)
        if not is_a4:
            return f"O documento não está no formato A4 ❌. Formato encontrado: {largura} x {altura} pontos."
        else:
            print("O documento está no formato A4 ✔️.")
        
        texto_primeira_pagina = extrair_texto_primeira_pagina(caminho_arquivo)

        erros = []
        for pagina_num, pagina in enumerate(extract_pages(caminho_arquivo), start=1):
            erros += show_ltitem_hierarchy(pagina, page_num=pagina_num)

        if erros:
            print(f"{paginas_status}\nForam encontrados os seguintes ERROS de: fonte/tamanho ❌:\n")
            palavraCompletaAux = []
            palavraCompleta = []
            errors = []
            for erro in erros:
                letra = erro['text']
                palavraCompletaAux.append(letra)
                if letra == '':
                    palavraAdicional = ''.join(palavraCompletaAux).strip()

                    errors.append({
                        'page': erro['page'],
                        'palavra': palavraAdicional,
                        'fontname': erro['fontname'],
                        'size': erro['size'],
                        'error': erro['error']
                    })
                    palavraCompleta.append(palavraAdicional)
                    palavraCompletaAux.clear()

            for erro in errors:
                print(f"Página {erro['page']}: Palavra '{erro['palavra']}' - Fonte: {erro['fontname']} - Tamanho: {erro['size']}pt - Erro: {erro['error']}")                    
                    
        else:
            print(f"{paginas_status} Todas as fontes estão em Arial e o tamanho é 10 ou maior.")

        return texto_primeira_pagina

    except Exception as e:
        return f"Erro ao tentar verificar a fonte e o tamanho: {e}"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as file:
        return file.read()

@app.post("/api/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Formato de arquivo não é PDF")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        resultado = verificar_pdf(file_path)
        if isinstance(resultado, str):
            return JSONResponse(content={"message": resultado})
        else:
            return JSONResponse(content={"message": "Arquivo em conformidade", "analysis": resultado})



@app.post("/api/verificar_capa/")
async def verificar_capa(file: UploadFile = File(...)):
    # Verifica se o arquivo é um PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Formato de arquivo não é PDF")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # Extrai o texto da primeira página
            texto_primeira_pagina = extract_text(file_path, page_numbers=[0])
            
            if texto_primeira_pagina:
                # Chama a API da Groq para verificar o conteúdo da capa
                clientGroq = Groq(api_key="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")
                
                prompt = f"""
                Incorpore um especialista em verificação de Projetos. Com base no texto fornecido, identifique se estão presentes as seguintes informações:

                1. Título do Projeto: Identifique se há um título que possa ser reconhecido como o nome do projeto.
                2. Categoria Disputada: Determine se há menção a uma categoria como curso técnico, graduação, pós-graduação, ou outras especificadas posteriormente.
                3. Nome da Equipe: Verifique se há um nome que identifica uma equipe.
                4. Nomes dos Integrantes ou Nome do Integrante: Identifique se são listados os nomes dos integrantes ou de um integrante específico.
                5. Cursos que Estão Matriculados: Verifique se há menção aos cursos nos quais os integrantes estão matriculados.

                Instruções adicionais para o modelo:

                - Se um campo não estiver claramente identificado, informe que o campo não foi encontrado.
                - Responda em um formato estruturado, listando cada item como um tópico (checklist) seguido de “Encontrado” ou “Não Encontrado”. Inclua o trecho do texto correspondente, se possível.
                - Utilize ícones de check (✔️) e uncheck (❌) para indicar a presença ou ausência de cada informação.  
                - Sempre responda TUDO em pt-br

                Texto extraído:
                {texto_primeira_pagina}
                """

                chat_completion = clientGroq.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model="llama3-8b-8192",
                )
                
                groq_response = chat_completion.choices[0].message.content
                return JSONResponse(content={"message": "Análise da capa concluída", "groq_analysis": groq_response})
            else:
                raise HTTPException(status_code=400, detail="Não foi possível extrair o texto da primeira página ou a página está vazia ❌.")

        except Exception as e:
            return JSONResponse(content={"message": f"Erro ao tentar extrair o texto da primeira página: {e}"})




@app.post("/api/verificar_fontes_tamanhos/")
async def verificar_fontes_tamanhos(file: UploadFile = File(...)):
    # Verifica se o arquivo é um PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Formato de arquivo não é PDF ❌")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # Processamento dos Erros
            erros = []
            for pagina_num, pagina in enumerate(extract_pages(file_path), start=1):            
                erros += show_ltitem_hierarchy(pagina, page_num=pagina_num)

            if erros:
                #print(f"{paginas_status}\nForam encontrados os seguintes ERROS de: fonte/tamanho ❌:\n")
                palavraCompletaAux = []
                palavraCompleta = []
                errors = []
                messages = []  # Lista para armazenar todas as mensagens

                for erro in erros:
                    letra = erro['text']
                    #print (letra)
                    palavraCompletaAux.append(letra)
                    if (letra == ''):
                        palavraAdicional = ''.join(palavraCompletaAux)  # Concatena todos os caracteres em uma string
                        palavraAdicional = palavraAdicional.strip()  # Remove qualquer espaço vazio ou string vazia no final

                        errors.append({
                            'page': erro['page'],
                            'palavra': palavraAdicional,
                            'fontname': erro['fontname'],
                            'size': erro['size'],
                            'error': erro['error']
                        })
                        #print (palavraAdicional)
                        palavraCompleta.append(palavraAdicional)
                        palavraCompletaAux.clear()

                for erro in errors:
                    #print(f"Página {erro['page']}: Palavra '{erro['palavra']}' - Fonte: {erro['fontname']} - Tamanho: {erro['size']}pt - Erro: {erro['error']}")
                    # Gerar as mensagens de erro completas                
                    mensagem = (
                        f"Página {erro['page']}: Palavra '{erro['palavra']}' "
                        f"- Fonte: {erro['fontname']} - Tamanho: {erro['size']}pt "
                        f"- Erro: {erro['error']}"
                    )
                    messages.append(mensagem)
                    # Retorna todas as mensagens em um JSON
                return JSONResponse(content={"message": "Erros encontrados nas fontes e/ou tamanhos de fonte ❌", "details": messages})
                    
                        
            else:
                #print(f"{paginas_status} Todas as fontes estão em Arial e o tamanho é 10 ou maior.")
                print(f"Todas as fontes estão em Arial e o tamanho é 10 ou maior ✔️.")
                return JSONResponse(content={"message": "Todas as fontes estão em Arial e o tamanho é 10 ou maior. ✔️"})
        except Exception as e:
            return JSONResponse(content={"message": f"Erro ao tentar verificar as fontes e tamanhos ❌: {e}"})






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
