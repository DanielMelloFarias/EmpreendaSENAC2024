from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pdfminer.high_level import extract_text
import tempfile
import os
import shutil
from groq import Groq

app = FastAPI()

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
                - Responda em pt-br

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
