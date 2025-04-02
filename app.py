import os
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
from PIL import Image
from io import BytesIO
# from pdfminer.high_level import extract_text
import docx
from transformers import CLIPProcessor, CLIPModel
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
import sys
import io
import shutil
from pdf2image import convert_from_path
import pytesseract
from agno.agent import Agent
from agno.tools.searxng import Searxng
from agno.models.groq import Groq as G
import json
from playsound import playsound
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from agno.agent import Agent
from agno.storage.agent.sqlite import SqliteAgentStorage
from flask import Flask, render_template, request
from rich.pretty import pprint
import glob
import os
import tempfile
import time
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64
from elevenlabs.client import ElevenLabs
from datetime import datetime
import re
import pyttsx3
import jsonify
import speech_recognition as sr
import pyttsx3
import plotly.graph_objects as go
import plotly.offline as po
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime
import os
import re
import textwrap
from plotly.subplots import make_subplots
import os
from groq import Groq
import plotly.express as px
import plotly.figure_factory as ff
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)

app = Flask(__name__)
# Set the encoding for standard output to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Call this function before inserting new data
i = 0
url=""


def language(text):

    languages = ["telugu", "english", "hindi","british","german","american","korean","indian"]  # List of languages to check

        # Create regex pattern
    pattern = r'\b(' + '|'.join(languages) + r')\b'

    match = re.findall(pattern, text)  # Find matches

    if match:
        detected_language = match[0]  # Store the first found language
    else:
        detected_language = None

    return detected_language
  # Setting to female voice

def speak(text):
    engine = pyttsx3.init()  # Object creation
    # Set TTS properties
    engine.setProperty('rate', 150)     # Setting up speaking rate
    engine.setProperty('volume', 1.0)  # Setting up volume
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.say(text)
    engine.runAndWait()  # Ensures it completes before moving forward
    time.sleep(1)  

def get_validated_language(word):
    """Validate language code input against supported languages"""
    supported_languages = GoogleTranslator().get_supported_languages(as_dict=True)
    while True:
        lang = word
        if lang in supported_languages or lang in supported_languages.values():
            return supported_languages.get(lang, lang)
        print("Invalid language code. Available codes:", ", ".join(supported_languages.keys()))

def listen_to_user(source_lang):
    """Handle listening and speech-to-text conversion"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("Listening")
        audio = recognizer.listen(source, phrase_time_limit=30)
        
    try:
        print(recognizer.recognize_google(audio, language=source_lang),flush=True)
        return recognizer.recognize_google(audio, language=source_lang)
        
    except:
        return "english"

def translate_text(text, target_lang):
    """Translate detected text and handle errors"""
    translator = GoogleTranslator(source='auto', target=target_lang)
    try:
        return translator.translate(text) or "Translation failed"
    except Exception as e:
        print(f"Translation failed: {e}")
        return ""

def generate_elevenlabs_speech(text, accent):
    """Generate voice preview using ElevenLabs with specified accent and save it"""
    client = ElevenLabs(
        api_key="sk_f1ef8061e07328e06bf11a42cbed2d7b8087a9df7a931153"
    )
    
    description = f"A warm and friendly male voice with a slight {accent} accent, speaking clearly and professionally"
    if len(text) < 100:
        text += " " + "This is additional text to meet the minimum length requirement."[:100-len(text)]
    
    try:
        previews = client.text_to_voice.create_previews(voice_description=description, text=text)
        if hasattr(previews, "previews") and len(previews.previews) > 0:
            first_preview = previews.previews[0]
            audio_data = base64.b64decode(first_preview.audio_base_64)
            
            # Generate a unique filename with timestamp
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = "translate.mp3"
            
            # Save the audio file permanently
            with open(output_file, "wb") as audio_file:
                audio_file.write(audio_data)
            
            return output_file
        else:
            print("❌ No voice previews generated.")
            return None
    except Exception as e:
        print(f"ElevenLabs speech generation failed: {e}")
        return None

def generate_gtts_speech(text, target_lang):
    """Fallback: Convert translated text to speech using gTTS and save it"""
    try:
        output_file = "translate.mp3"
        
        tts = gTTS(text, lang=target_lang)
        tts.save(output_file)
        return output_file
    except Exception as e:
        print(f"gTTS speech generation failed: {e}")
        return None

# def play_audio(audio_file):
#     """Cross-platform audio playback"""
#     try:
#         if os.name == "nt":  # Windows
#             os.system(f'start /min {audio_file}')
#         elif os.name == "posix":
#             os.system(f"afplay {audio_file}" if "Darwin" in os.uname().sysname else f"mpg321 {audio_file}")
#         else:
#             print("Audio playback not supported on this OS.")
#         time.sleep(2)  # Allow time for playback to start
#     except Exception as e:
#         print(f"Audio playback failed: {e}")

def translate(source_lang):
    """Main function to handle speech translation, playback, and saving"""
    detected_text = listen_to_user(source_lang)
    if not detected_text:
        print("❌ No speech detected.")
        return 
    
    print(f"📝 Detected Text: {detected_text}")
    translated_text = translate_text(detected_text, "en")
    return translated_text
        # Note: File is not deleted here since we want to keep it

def translate_and_speak(target_lang, accent, detected_text):
    """Main function to handle speech translation, playback, and saving"""

    translated_text = translate_text(detected_text, target_lang)
    
    
    # Try ElevenLabs first, fall back to gTTS if it fails
    audio_file = generate_elevenlabs_speech(translated_text, accent)
    if not audio_file:
        print("Falling back to gTTS...")
        audio_file = generate_gtts_speech(translated_text, target_lang)
    
    if audio_file:
        print(f"💾 Audio saved as: {audio_file}")
        print("🔊 Playing Translated Audio...")
        playsound("translate.mp3")


def clear_chroma_storage():
    folder_path = "./store"  # Path to the Chroma DB storage

    # Delete only database files (e.g., SQLite, index files, etc.)
    files_to_remove = glob.glob(os.path.join(folder_path, "*"))
    
    for file in files_to_remove:
        try:
            os.remove(file)
        except PermissionError:
            print(f"Cannot delete {file}, it's in use.")

# Initialize CLIP Model and Processor
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

db = Chroma(persist_directory="./store", collection_name="storage", embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"))

# Function to crawl website and collect content
def crawl_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract text
    text = ' '.join([p.get_text() for p in soup.find_all('p')])
    
    # Extract links (URLs)
    links = [a['href'] for a in soup.find_all('a', href=True)]
    
    # Extract audio files
    audio_files = [audio['src'] for audio in soup.find_all('audio', src=True)]
    
    # Extract image URLs
    images = [img['src'] for img in soup.find_all('img', src=True)]
    
    # Extract video files
    video_files = [video['src'] for video in soup.find_all('video', src=True)]
    
    # Extract PDF files
    pdf_files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]
    
    # Extract Word files
    word_files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.docx')]
    
    # Prepare data to save
    data = {
        "text": text,
        "links": links,
        "audio_files": audio_files,
        "images": images,
        "video_files": video_files,
        "pdf_files": pdf_files,
        "word_files": word_files
    }
    
    # Save crawled data to a JSON file
    with open("web_content.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return data

# Function to download and process media files (images, PDFs, and Word files)
def download_media_files(media_urls, file_type,main_url):
    downloaded_files = []
    
    for url in media_urls:
        try:
            # Handle relative URLs
            if not url.startswith('http'):
                url = urllib.parse.urljoin(main_url, url)
            
            response = requests.get(url)
            if response.status_code == 200:
                filename = url.split("/")[-1]
                if file_type == "audio":
                    file_path = os.path.join("media", "audio", filename)
                elif file_type == "video":
                    file_path = os.path.join("media", "video", filename)
                elif file_type == "pdf":
                    file_path = os.path.join("media", "pdf", filename)
                elif file_type == "word":
                    file_path = os.path.join("media", "word", filename)
                else:
                    continue
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                downloaded_files.append(file_path)
            else:
                print(f"Failed to download {url}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    
    return downloaded_files

# Function to process PDF files and extract text

# Function to extract text using OCR from a PDF
def extract_pdf_text_with_ocr(pdf_path):
    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path)
        
        # Extract text from each image using OCR
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

# Function to process Word files and extract text
def extract_word_text(word_path):
    try:
        doc = docx.Document(word_path)
        text = '\n'.join([p.text for p in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error extracting text from Word file {word_path}: {e}")
        return ""

# Function to get image embeddings using CLIP
def get_clip_image_embeddings(image_urls):
    image_embeddings = []
    for img_url in image_urls:
        try:
            image = Image.open(requests.get(img_url, stream=True).raw).convert("RGB")
            inputs = clip_processor(images=image, return_tensors="pt")
            with torch.no_grad():
                img_embedding = clip_model.get_image_features(**inputs)
            image_embeddings.append({"url": img_url, "embedding": img_embedding.squeeze().tolist()})
        except Exception as e:
            print(f"Error processing image {img_url}: {e}")
    return image_embeddings

# Function to process the crawled data
def process_data(data,main_url):
    text = data["text"]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.create_documents([text])
    text_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Process text and add embeddings
    for doc in split_docs:
        embedding = text_embeddings.embed_query(doc.page_content)
        db.add_texts(texts=[doc.page_content], metadatas=[{"type": "text"}], embeddings=[embedding])
    
    # Process images and add embeddings
    image_embeddings = get_clip_image_embeddings(data["images"])
    for img in image_embeddings:
        db.add_texts(texts=[img["url"]], metadatas=[{"type": "image"}], embeddings=[img["embedding"]])
    
    # Process media files (audio, pdf, word, and video)
    media_files = {
        "audio": download_media_files(data["audio_files"], "audio",main_url),
        "video": download_media_files(data["video_files"], "video",main_url),
        "pdf": download_media_files(data["pdf_files"], "pdf",main_url),
        "word": download_media_files(data["word_files"], "word",main_url)
    }
    
    for file_type, files in media_files.items():
        for file in files:
            if file.endswith(".pdf"):
                text = extract_pdf_text_with_ocr(file)
                # Add extracted PDF text to db
                db.add_texts(texts=[text], metadatas=[{"type": "pdf"}])
            elif file.endswith(".docx"):
                text = extract_word_text(file)
                # Add extracted Word text to db
                db.add_texts(texts=[text], metadatas=[{"type": "word"}])
            else:
                # Store media file URLs
                db.add_texts(texts=[file], metadatas=[{"type": file_type}])
    
    return db

def generate_ai_response(user_text,data):
        print("Generating response for:", user_text)

        data = data
        
        try:
            chat_completion = client.chat.completions.create(
                model="qwen-2.5-coder-32b",
                messages=[
                    {  
                        "role": "system",
                        "content": (
                            
                            "You are a Data Visualization Assistant. Your task is to generate only Python code for Plotly visualizations. The below Rules to Follow "
                            f"based on above user query :{user_text} from our data {data}. The output must be pure Python code, without any text, imports, explanations."

                            "### Rules to Follow"
                            f"1. Generate a working visualization code for {user_text} data using the exact format and structure from the provided examples."
                            "2. Ensure the final visualization uses fig.write_image('static/plot.png'), output_file = os.path.join(output_dir, 'plot.html') and  po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn'). Do not use .show() or return statements."
                            "3. After generating the code, verify it thoroughly to ensure there are no errors and that it functions as expected."

                            "### Examples "

                            "**Example 1: System Performance Dashboard (Gauges)** "
                            "**User Query:** 'Show system performance in a dashboard.' "
                            "**Expected Model Output:** "

                            "```python "
                            "try: "
                            "    cpu_usage = psutil.cpu_percent(interval=1) "
                            "    ram_usage = psutil.virtual_memory().percent "
                            "    storage_usage = psutil.disk_usage('/').percent "
                                "fig = go.Figure() "
                                "fig.add_trace(go.Indicator( "
                                "    mode='gauge+number', "
                                "    value=cpu_usage, "
                                "    title={'text': 'CPU Usage'}, "
                                "    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': 'blue'} }, "
                                "    domain={'x': [0, 0.3], 'y': [0, 1]} "
                                ")) "
                                "fig.add_trace(go.Indicator( "
                                "    mode='gauge+number', "
                                "    value=ram_usage, "
                                "    title={'text': 'RAM Usage'}, "
                                "    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': 'green'} }, "
                                "    domain={'x': [0.35, 0.65], 'y': [0, 1]} "
                                ")) "
                                "fig.add_trace(go.Indicator( "
                                "    mode='gauge+number', "
                                "    value=storage_usage, "
                                "    title={'text': 'Storage Usage'}, "
                                "    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': 'red'} }, "
                                "    domain={'x': [0.7, 1], 'y': [0, 1]} "
                                ")) "
                                "fig.update_layout(title='System Performance Dashboard', height=400, width=1200) "
                                "fig.write_image('static/plot.png')"
                                "output_dir = os.path.join(os.getcwd(), 'static')"
                                "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"
                                "output_file = os.path.join(output_dir, 'plot.html')"
                                "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"
                            "except Exception: "
                            "    cpu_usage = ram_usage = storage_usage = 0.0  # Fallback values "
                            "``` "

                            "**Example 2: describe the Sales Distribution**"  
                            "**User Query:** 'describe sales distribution by region, sector, and vendor.'"  
                            "**Expected Model Output:**"  

                            "```python"  
                            "import plotly.express as px"  
                            "import pandas as pd"  
                            "vendors = ['A', 'B', 'C', 'D', None, 'E', 'F', 'G', 'H', None]"  
                            "sectors = ['Tech', 'Tech', 'Finance', 'Finance', 'Other',"  
                            "           'Tech', 'Tech', 'Finance', 'Finance', 'Other']"  
                            "regions = ['North', 'North', 'North', 'North', 'North',"  
                            "           'South', 'South', 'South', 'South', 'South']"  
                            "sales = [1, 3, 2, 4, 1, 2, 2, 1, 4, 1]"  
                            "df = pd.DataFrame(dict(vendors=vendors, sectors=sectors, regions=regions, sales=sales))"  
                            "print(df)"  
                            "fig = px.sunburst(df, path=['regions', 'sectors', 'vendors'], values='sales')"
                            "fig.write_image('static/plot.png')"  
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```"  

                            "**Example 3: Bar Chart for Monthly Product Sales**"  
                            "**User Query:** 'Show monthly sales data for primary and secondary products using a bar chart.'"  
                            "**Expected Model Output:**"

                            "```python"  
                            "import plotly.graph_objects as go"  
                            "months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',"  
                            "          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']"  
                            "fig = go.Figure()"  
                            "fig.add_trace(go.Bar("  
                            "    x=months,"  
                            "    y=[20, 14, 25, 16, 18, 22, 19, 15, 12, 16, 14, 17],"  
                            "    name='Primary Product',"  
                            "    marker_color='indianred'"  
                            "))"  
                            "fig.add_trace(go.Bar("  
                            "    x=months,"  
                            "    y=[19, 14, 22, 14, 16, 19, 15, 14, 10, 12, 12, 16],"  
                            "    name='Secondary Product',"  
                            "    marker_color='lightsalmon'"  
                            "))"  
                            "# Modify the tick angle of the x-axis for better readability"  
                            "fig.update_layout(barmode='group', xaxis_tickangle=-45)"
                            "fig.write_image('static/plot.png')"  
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```" 

                            "**Example 4: Describe Sports Categories**"  
                            "**User Query:** 'Create a sunburst chart displaying the hierarchy of sports categories by region.'"  
                            "**Expected Model Output:**"  

                            "```python"  
                            "import plotly.graph_objects as go"  
                            "fig = go.Figure(go.Sunburst("  
                            "  ids=["  
                            "    'North America', 'Europe', 'Australia', 'North America - Football', 'Soccer',"  
                            "    'North America - Rugby', 'Europe - Football', 'Rugby',"  
                            "    'Europe - American Football', 'Australia - Football', 'Association',"  
                            "    'Australian Rules', 'Australia - American Football', 'Australia - Rugby',"  
                            "    'Rugby League', 'Rugby Union'"  
                            "  ],"  
                            "  labels=["  
                            "    'North<br>America', 'Europe', 'Australia', 'Football', 'Soccer', 'Rugby',"  
                            "    'Football', 'Rugby', 'American<br>Football', 'Football', 'Association',"  
                            "    'Australian<br>Rules', 'American<br>Football', 'Rugby', 'Rugby<br>League',"  
                            "    'Rugby<br>Union'"  
                            "  ],"  
                            "  parents=["  
                            "    '', '', '', 'North America', 'North America', 'North America', 'Europe',"  
                            "    'Europe', 'Europe', 'Australia', 'Australia - Football', 'Australia - Football',"  
                            "    'Australia - Football', 'Australia - Football', 'Australia - Rugby',"  
                            "    'Australia - Rugby'"  
                            "  ],"  
                            "))"  
                            "fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))"
                            "fig.write_image('static/plot.png')"  
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```"  

                            "**Example 5: Pie Chart for World GDP Distribution**"  
                            "**User Query:** 'Compare the distribution of world GDP across continents for the years 1980 and 2007 using pie charts.'"  
                            "**Expected Model Output:**"

                            "```python"  
                            "import plotly.graph_objects as go"  
                            "from plotly.subplots import make_subplots"  
                            "labels = ['Asia', 'Europe', 'Africa', 'Americas', 'Oceania']"  
                            "fig = make_subplots(1, 2, specs=[[{'type':'domain'}, {'type':'domain'}]],"  
                            "                    subplot_titles=['1980', '2007'])"  
                            "fig.add_trace(go.Pie(labels=labels, values=[4, 7, 1, 7, 0.5], scalegroup='one',"  
                            "                     name='World GDP 1980'), 1, 1)"  
                            "fig.add_trace(go.Pie(labels=labels, values=[21, 15, 3, 19, 1], scalegroup='one',"  
                            "                     name='World GDP 2007'), 1, 2)"  
                            "fig.update_layout(title_text='World GDP')"
                            "fig.write_image('static/plot.png')"  
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```"  

                            "**Example 6: Donut Chart for Global Emissions Comparison**"  
                            "**User Query:** 'Compare the distribution of GHG and CO2 emissions among major contributors using donut charts.'"  
                            "**Expected Model Output:**"

                            "```python"  
                            "import plotly.graph_objects as go"  
                            "from plotly.subplots import make_subplots"  
                            "labels = ['US', 'China', 'European Union', 'Russian Federation', 'Brazil', 'India',"  
                            "          'Rest of World']"  
                            "# Create subplots: use 'domain' type for Pie subplot"  
                            "fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])"  
                            "fig.add_trace(go.Pie(labels=labels, values=[16, 15, 12, 6, 5, 4, 42], name='GHG Emissions'),"  
                            "              1, 1)"  
                            "fig.add_trace(go.Pie(labels=labels, values=[27, 11, 25, 8, 1, 3, 25], name='CO2 Emissions'),"  
                            "              1, 2)"  
                            "# Use `hole` to create a donut-like pie chart"  
                            "fig.update_traces(hole=.4, hoverinfo='label+percent+name')"  
                            "fig.update_layout("  
                            "    title_text='Global Emissions 1990-2011',"  
                            "    # Add annotations in the center of the donut pies."  
                            "    annotations=[dict(text='GHG', x=0.2, y=0.5, font_size=20, showarrow=False, xanchor='center'),"  
                            "                 dict(text='CO2', x=0.8, y=0.5, font_size=20, showarrow=False, xanchor='center')]"  
                            ")" 
                            "fig.write_image('static/plot.png')" 
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```"

                            "**Example 7: Line Chart for Google Stock Prices**"  
                            "**User Query:** 'Plot a line chart showing Google stock prices over time.'"  
                            "**Expected Model Output:**"

                            "```python"  
                            "import plotly.express as px"  
                            "df = px.data.stocks()"  
                            "fig = px.line(df, x='date', y='GOOG')"
                            "fig.write_image('static/plot.png')"  
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```" 

                            "**Example 8: Area Chart for Stock Performance**"  
                            "**User Query:** 'Generate an area chart showing stock performance trends over time for different companies.'"  
                            "**Expected Model Output:**"

                            "```python"  
                            "import plotly.express as px"  
                            "df = px.data.stocks(indexed=True) - 1"  
                            "fig = px.area(df, facet_col='company', facet_col_wrap=2)" 
                            "fig.write_image('static/plot.png')" 
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```"  

                            "**Example 10: Table for Quarterly Expense Breakdown**"  
                            "**User Query:** 'Create a table to display expenses over four quarters with alternating row colors.'"  
                            "**Expected Model Output:**"

                            "```python"  
                            "import plotly.graph_objects as go"   
                            "fig = go.Figure(data=[go.Table("  
                            "  header=dict("  
                            "    values=['<b>EXPENSES</b>', '<b>Q1</b>', '<b>Q2</b>', '<b>Q3</b>', '<b>Q4</b>'],"  
                            "    line_color='darkslategray',"  
                            "    fill_color='grey',"  
                            "    align=['left','center'],"  
                            "    font=dict(color='white', size=12)"  
                            "  ),"  
                            "  cells=dict("  
                            "    values=["  
                            "      ['Salaries', 'Office', 'Merchandise', 'Legal', '<b>TOTAL</b>'],"  
                            "      [1200000, 20000, 80000, 2000, 12120000],"  
                            "      [1300000, 20000, 70000, 2000, 130902000],"  
                            "      [1300000, 20000, 120000, 2000, 131222000],"  
                            "      [1400000, 20000, 90000, 2000, 14102000] ],"  
                            "    line_color='darkslategray',"  
                            "    # 2-D list of colors for alternating rows"  
                            "    fill_color=[['white', 'lightgrey', 'white','lightgrey', 'white'] * 5],"  
                            "    align=['left', 'center'],"  
                            "    font=dict(color='darkslategray', size=11)"  
                            "  )"  
                            ")])" 
                            "fig.write_image('static/plot.png')" 
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```" 

                            "**Example 11: Hockey Team Stats Table with Goals Per Game**"  
                            "**User Query:** 'Create a table showing hockey team statistics along with a scatter plot for goals per game.'"  
                            "**Expected Model Output:**"
                              
                            "```python"  
                            "import plotly.graph_objects as go"  
                            "import plotly.figure_factory as ff"  
                            "table_data = [['Team', 'Wins', 'Losses', 'Ties'],"  
                            "              ['Montréal Canadiens', 18, 4, 0],"  
                            "              ['Dallas Stars', 18, 5, 0],"  
                            "              ['NY Rangers', 16, 5, 0],"  
                            "              ['Boston Bruins', 13, 8, 0],"  
                            "              ['Chicago Blackhawks', 13, 8, 0],"  
                            "              ['LA Kings', 13, 8, 0],"  
                            "              ['Ottawa Senators', 12, 5, 0]]"  
                            "fig = ff.create_table(table_data, height_constant=60)"  
                            "teams = ['Montréal Canadiens', 'Dallas Stars', 'NY Rangers',"  
                            "         'Boston Bruins', 'Chicago Blackhawks', 'LA Kings', 'Ottawa Senators']"  
                            "GFPG = [3.54, 3.48, 3.0, 3.27, 2.83, 2.45, 3.18]"  
                            "GAPG = [2.17, 2.57, 2.0, 2.91, 2.57, 2.14, 2.77]"  
                            "trace1 = go.Scatter(x=teams, y=GFPG,"  
                            "                    marker=dict(color='#0099ff'),"  
                            "                    name='Goals For Per Game',"  
                            "                    xaxis='x2', yaxis='y2')"  
                            "trace2 = go.Scatter(x=teams, y=GAPG,"  
                            "                    marker=dict(color='#404040'),"  
                            "                    name='Goals Against Per Game',"  
                            "                    xaxis='x2', yaxis='y2')"  
                            "fig.add_traces([trace1, trace2])"  
                            "# Set layout for subplots"  
                            "fig.layout.xaxis.update({'domain': [0, .5]})"  
                            "fig.layout.xaxis2.update({'domain': [0.6, 1.]})"  
                            "fig.layout.yaxis2.update({'anchor': 'x2', 'title': 'Goals'})"  
                            "fig.layout.margin.update({'t':50, 'b':100})"  
                            "fig.layout.update({'title': '2016 Hockey Stats'})" 
                            "fig.write_image('static/plot.png')" 
                            "output_dir = os.path.join(os.getcwd(), 'static')"  
                            "os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn’t exist"  
                            "output_file = os.path.join(output_dir, 'plot.html')"  
                            "po.plot(fig, filename=output_file, auto_open=False, include_plotlyjs='cdn')"  
                            "```" 

                            "**Follow the same pattern for any other visualization requests.**"
                        
                        ),
                    }
                    
                ]
            )
            ai_text = chat_completion.choices[0].message.content
            # ai_text = ollama_response["message"]["content"]
        except Exception as e:
            print(f"Ollama error: {str(e)}")
            ai_text = "How can I assist with your request? Would you like a performance dashboard or network map?"

        print("Tech_Support_Agent:", ai_text,flush=True)
        # self.text_to_speech(ai_text)

        # Enhanced keyword checking with debugging
        trigger_keywords = ['dashboard', 'network', 'topology','chat', 'performance', 'charts','plots','plot','graph','chart','tables','graphs','table','map','temperature', 'system','pie','bar','animated','animate','describe']
        found_keywords = [kw for kw in trigger_keywords if kw in user_text]
        print(f"Checking for keywords: {trigger_keywords}")
        print(f"Found keywords in user input: {found_keywords}")

        if found_keywords:  # If any keyword is found
            print("Triggering visualization...")
            print(ai_text)
            pattern = r"python\s*(.*?)\s*```"
            match = re.search(pattern, ai_text, re.DOTALL)

            if match:
                extracted_text = match.group(1).strip()
                print(extracted_text)  # Output only the extracted code
            else:
                print("No match found")

            try:
                exec(textwrap.dedent(extracted_text))
            except:
                print("try again", flush=True)

# Query Knowledge Base
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html",message="")


@app.route("/crawl", methods=["POST"])
def crawl():
    # clear_chroma_storage()
    global i, url 
    url = request.form["url"]
    data = crawl_website(url)
    process_data(data,url)
    i += 1
    return render_template("index.html", message="Website data stored successfully!")
        

# Query stored data
@app.route("/query", methods=["POST"])
def query():
    global i, url
    query_text = request.form['query']
    # Retrieve stored documents
    chrom = db.get()
    stored_texts = chrom['documents']
    if i > 1:
        previous_texts = stored_texts
        stored_texts = chrom['documens']
        stored_texts.replace(previous_texts, "").strip()
    else:
        stored_texts = chrom['documents']
    searxng = Searxng(
                host="http://localhost:53153",
                engines=["openverse"],
                fixed_max_results=5,
                news=True,
                science=True,
                images=True,
                videos=True,
                map=True,
                music=True,
                it=True   
            )

    agent = Agent(
        model=G(id="qwen-2.5-32b"),
        tools=[searxng],
        storage=SqliteAgentStorage(table_name="agent_sessions", db_file="tmp/agent_storage.db"),
        add_history_to_messages=True,
        num_history_responses=3,
        description="You are an AI assistant with full access to analyze and retrieve all available data, including text, images, audio, videos, PDFs, and Word documents.",
        instructions=[
            f"1. Search your ChromaDB {stored_texts} for relevant information related to the user's query.",
            f"2. If the query requires additional or more up-to-date information, search the web {url} to fill in any gaps.",
            "3. Always prioritize the information available in your ChromaDB over web results, unless the web results are more recent, accurate, or comprehensive.",
            "4. Ensure your responses are clear, concise, and directly address the user's question.",
            "5. If the query involves complex data or multiple sources, synthesize the information to provide a well-rounded and accurate answer.",
            "6. Double-check your responses for accuracy and relevance before delivering them to the user."
        ],   
    )
    response = agent.run(query_text)
    print(type(response))
    return render_template("index.html", response=response.content)

@app.route('/voice', methods=['POST'])
def voice_command():
    global i, url
    txt = request.form['input']
    if txt == "None":
        speak("How can I help you")
        speak("Select input language")
        
        text = listen_to_user("en")
        text = text.strip().lower()
        txt = language(text)
        s_txt = get_validated_language(txt)
    # input_lang = get_validated_language(txt)
    else:
        s_txt = get_validated_language(txt)
    
    txt = request.form['output']
    if txt == "None":
        speak("Select output language")
        text = listen_to_user("en")
        text = text.strip().lower()
        txt = language(text)
        t_txt = get_validated_language(txt)
    else:
        t_txt = get_validated_language(txt)
    
    txt = request.form['accent']
    if txt == "None":
        speak("select accent")
        text = listen_to_user("en")
        text = text.strip().lower()
        accent = language(text)

    else:
        accent = txt
     
    speak("what is your query")
    query_text=translate(s_txt)
    chrom = db.get()
    stored_texts = chrom['documents']
    if i > 1:
        previous_texts = stored_texts
        stored_texts = chrom['documens']
        stored_texts.replace(previous_texts, "").strip()
    else:
        stored_texts = chrom['documents']

    searxng = Searxng(
                host="http://localhost:53153",
                engines=["openverse"],
                fixed_max_results=5,
                news=True,
                science=True,
                images=True,
                videos=True,
                map=True,
                music=True,
                it=True   
            )

    agent = Agent(
        model=G(id="qwen-2.5-32b"),
        tools=[searxng],
        storage=SqliteAgentStorage(table_name="agent_sessions", db_file="tmp/agent_storage.db"),
        add_history_to_messages=True,
        num_history_responses=3,
        description="You are an AI assistant with full access to analyze and retrieve all available data, including text, images, audio, videos, PDFs, and Word documents.",
        instructions=[
            f"1. Search your ChromaDB {stored_texts} for relevant information related to the user's query.",
            f"2. If the query requires additional or more up-to-date information, search the web {url} to fill in any gaps.",
            "3. Always prioritize the information available in your ChromaDB over web results, unless the web results are more recent, accurate, or comprehensive.",
            "4. Ensure your responses are clear, concise, and directly address the user's question.",
            "5. If the query involves complex data or multiple sources, synthesize the information to provide a well-rounded and accurate answer.",
            "6. Double-check your responses for accuracy and relevance before delivering them to the user."
        ], 
    )
    response = agent.run(query_text)
    translate_and_speak(t_txt, accent, response.content)
    return render_template("index.html", response=response.content)

@app.route('/plot', methods=['POST'])
def plot():
    user = request.form['input']
    chrom = db.get()
    data = chrom['documents']
    generate_ai_response(user,data)
    image_path = "static/plot.png"  # Change this path accordingly
    image_exists = os.path.exists(image_path)
    return render_template("index.html", image_exists=image_exists, image_path=image_path)
    


if __name__ == "__main__":
    app.run(debug=True)
        

