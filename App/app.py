
import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
import textwrap
from PyPDF2 import PdfReader
from openai import OpenAI
import json
from fuzzywuzzy import fuzz
import numpy as np
import textwrap
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import webbrowser
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import HashingVectorizer
from itertools import combinations
import itertools

# from dotenv import load_dotenv
client = OpenAI(api_key='')
# load_dotenv(".env")

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DOWNLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/downloads/'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}

app = Flask(__name__, static_url_path="/static")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024

json_objects = []
def normalize_phone(phone):
    # Normalize phone number if needed
    return phone.replace(" ", "").replace("-", "")
def is_duplicate(text1, text2, threshold=0.5):
    strtext1 = str(text1)
    strtext2 = str(text2)
    tokenized_text1 = strtext1.split()
    tokenized_text2 = strtext2.split()

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([strtext1, strtext2])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    print(cosine_sim)
    return cosine_sim[0][0] > threshold

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file attached in request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            files = request.files.getlist("file") 
            for file in files:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                reader = PdfReader(file)
                page = reader.pages[0]
            # print(page.extract_text())
            
                completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
    {"role": "system", "content": page.extract_text() + "From the above text, extract Name, Email Mobile Number, Gender, Highest Qualification, College(Only get the heading), Specialization Branch, Year of Graduation, Linkedin Profile,and Recent Work Experience(Summarize the experience to 10 words for each item. limit the number of experience to the latest two). give response as json object. there should be nothing else in the answer. After this json has been created, hash this json file. only output the "},
  ]
)
                response_json = json.loads(completion.choices[0].message.content)
                json_objects.append(f"""{response_json}""")
        
        duplicates = []
        hash_vectorizer = HashingVectorizer(n_features=1000)
        print(len(json_objects))
        # hashed_vectors = hash_vectorizer.fit_transform(json_objects)
        # nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(hashed_vectors)
        # for text1, text2 in set(itertools.combinations(json_objects, 2)):
        #     distances, indices = nbrs.kneighbors(hash_vectorizer.transform([text1, text2]))
        #     print(f"\nSimilarity between resume 'text1' and 'text2': {1 - distances[0][1]}")
        #     if 1 - distances[0][1] > 0.1:
        #         duplicates.append((text1, text2))
            
        
    
        for i in range(len(json_objects)):
            for j in range(i+1, len(json_objects)):
                print("_________________________________________")
                if is_duplicate(json_objects[i],json_objects[j]):
                    duplicates.append((i, j))
        print(len(duplicates))
        return redirect(url_for('result', duplicates=duplicates))
    return render_template('index.html')

@app.route('/result')
def booking():
    duplicates = request.args.get('duplicates', None)
    return render_template('main/result.html', duplicates=duplicates)    

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
