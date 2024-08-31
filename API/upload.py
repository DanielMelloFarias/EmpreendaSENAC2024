from flask import Flask, request, jsonify
import os
import PyPDF2
import pdfplumber

app = Flask(__name__)

# Função para verificar se a extensão do arquivo é PDF
def check_extension(file_path):
    return file_path.lower().endswith('.pdf')

# Função para verificar se as páginas estão no formato A4
def check_page_format(file_path):
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            width, height = page.width, page.height
            if not (590 < width < 595 and 840 < height < 845):
                return False
    return True

# Função para verificar a fonte e o tamanho da fonte
def check_font_and_size(file_path):
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                font_data = page.extract_words()
                for word in font_data:
                    if word['fontname'].lower() != 'arial' or int(word['size']) < 10:
                        return False
    return True

# Função para contar o número de páginas
def check_page_count(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfFileReader(file)
        return reader.getNumPages() <= 22

# Função para extrair o texto da capa
def extract_cover_text(file_path):
    with pdfplumber.open(file_path) as pdf:
        if len(pdf.pages) > 0:
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            return text

    return None

@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "Oi"}), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and check_extension(file.filename):
        file_path = os.path.join('/tmp', file.filename)
        file.save(file_path)

        # Verificações
        if not check_page_format(file_path):
            return jsonify({"error": "Páginas não estão no formato A4"}), 400
        if not check_font_and_size(file_path):
            return jsonify({"error": "Fonte incorreta ou tamanho inferior a 10"}), 400
        if not check_page_count(file_path):
            return jsonify({"error": "Número de páginas excede o limite de 22"}), 400

        cover_text = extract_cover_text(file_path)
        if cover_text:
            return jsonify({"message": "Arquivo em conformidade", "cover_text": cover_text}), 200
        else:
            return jsonify({"error": "Não foi possível extrair o texto da capa"}), 400

    else:
        return jsonify({"error": "Formato de arquivo não é PDF"}), 400

# Handler Vercel
def handler(event, context):
    return app(event, context)
