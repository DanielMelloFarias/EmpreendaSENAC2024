from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from PIL import Image
import io
import base64
import requests
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

genai.configure(api_key="AIzaSyD9XWKW-zJa05wr6r3SFCX8EllUDl-w4C8")
model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

# Configurar CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

class Base64Request(BaseModel):
    base64: str

def gemini_pro_vision_api(image, prompt="Descreva a img e extraia a informação de texto (caso necessário, complete o texto da forma q achar necessário), responta em pt-br."):
    response = model.generate_content([prompt, image])
    return response.text

@app.get("/")
async def read_root():
    return {"message": "OI"}

@app.post("/api/url")
async def analyze_image_url(request: URLRequest):
    response = requests.get(request.url)
    image = Image.open(io.BytesIO(response.content))
    return {"description": gemini_pro_vision_api(image)}

@app.post("/api/base64")
async def analyze_image_base64(request: Base64Request):
    image_data = base64.b64decode(request.base64)
    image = Image.open(io.BytesIO(image_data))
    return {"description": gemini_pro_vision_api(image)}

@app.post("/api/upload")
async def analyze_uploaded_image(file: UploadFile = File(...)):
    image = Image.open(file.file)
    return {"description": gemini_pro_vision_api(image)}
