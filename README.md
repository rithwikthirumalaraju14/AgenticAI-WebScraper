
# AI-Powered Web Crawler and Visualization Tool

This is a Flask-based web application that crawls websites, processes multimedia content, answers queries using an AI agent, and generates data visualizations. It integrates speech recognition, text-to-speech, and advanced data processing capabilities.

## Features
- **Web Crawling**: Extracts text, links, images, audio, videos, PDFs, and Word documents from a specified URL.
- **Data Storage**: Stores processed data in a Chroma vector database for efficient retrieval.
- **Query Processing**: Uses a Groq-powered AI agent to answer user queries, with optional web search via Searxng.
- **Voice Interaction**: Supports voice input/output with language translation and accent options (ElevenLabs/gTTS).
- **Data Visualization**: Generates Plotly visualizations (e.g., charts, tables) based on user queries.

## Prerequisites
- Python 3.8+
- A Groq API key (set in `.env` as `GROQ_API_KEY`)
- An ElevenLabs API key (hardcoded in code; replace with your own)
- Poppler (for PDF-to-image conversion)
- Tesseract OCR (for text extraction from images/PDFs)

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install System Dependencies**
   - On Ubuntu:
     ```bash
     sudo apt-get install poppler-utils tesseract-ocr
     ```
   - On macOS:
     ```bash
     brew install poppler tesseract
     ```

5. **Set Up Environment Variables**
   Create a `.env` file in the root directory:
   ```plaintext
   GROQ_API_KEY=your_groq_api_key_here
   ```

6. **Directory Setup**
   Ensure the following directories exist or will be created:
   - `media/audio`, `media/video`, `media/pdf`, `media/word` (for downloaded files)
   - `static` (for visualization outputs)
   - `tmp` (for agent storage)

## Usage

1. **Run the Application**
   ```bash
   python app.py
   ```
   The app will start on `http://localhost:5000`.

2. **Access the Web Interface**
   Open a browser and navigate to `http://localhost:5000`. Use the provided forms to:
   - **Crawl a Website**: Enter a URL to scrape and store its content.
   - **Query Data**: Ask questions about the stored data.
   - **Voice Commands**: Select languages and accents, then speak your query.
   - **Generate Plots**: Request visualizations based on stored data.

3. **Example Queries**
   - Text: "What is on this website?"
   - Voice: Select input/output languages, then say, "Show me a chart of the data."
   - Plot: "Create a bar chart from the data."

## Project Structure
```
your-repo/
├── app.py              # Main Flask application
├── static/             # Stores generated plots (images/HTML)
├── media/              # Stores downloaded media files
├── tmp/                # Agent storage (SQLite DB)
├── store/              # Chroma DB storage
├── web_content.json    # Crawled website data
├── translate.mp3       # Generated audio output
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── templates/
    └── index.html      # Web interface template
```

## Dependencies
Key libraries include:
- `flask`: Web framework
- `requests`, `beautifulsoup4`: Web crawling
- `transformers`, `torch`: CLIP model for image embeddings
- `langchain`, `chromadb`: Text processing and storage
- `groq`: AI model integration
- `plotly`: Data visualization
- `speech_recognition`, `pyttsx3`, `elevenlabs`, `gtts`: Voice features
- `pdf2image`, `pytesseract`: PDF processing

Install them via:
```bash
pip install flask requests beautifulsoup4 transformers torch langchain chromadb groq plotly speechrecognition pyttsx3 elevenlabs gtts pdf2image pytesseract
```

## Notes
- Replace the hardcoded ElevenLabs API key (`sk_f1ef8061e07328e06bf11a42cbed2d7b8087a9df7a931153`) with your own.
- Ensure `index.html` exists in the `templates/` directory (not provided in the code snippet).
- The app assumes a local Searxng instance at `http://localhost:53153`; adjust as needed.

## Contributing
Feel free to submit issues or pull requests to improve functionality or fix bugs.

## License
This project is licensed under the MIT License.

---

### Notes for You
- Replace `yourusername/your-repo` with your actual GitHub repository details.
- Create a `requirements.txt` file by running `pip freeze > requirements.txt` after installing dependencies.
- Ensure you have an `index.html` template; if not, you'll need to create one with appropriate form fields and display logic.
- Adjust paths or configurations (e.g., Searxng host) based on your setup.

Let me know if you need help refining this further!


Contact
For any inquiries, contact at rithwik.t2003@gmail.com.
