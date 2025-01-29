from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import PyPDF2
from docx import Document
from g4f.client import Client

app = Flask(__name__)

# Initialize g4f client
client = Client()

# File Uploads Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Conversation history storage
conversation_history = []

# Function to generate images using DALL·E (g4f)
def generate_dalle_image(image_prompt):
    """Generate an image using DALL·E 3 via g4f"""
    response = client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        response_format="url"
    )
    return response.data[0].url  # Return image URL

# Function to get chatbot response using g4f
def get_chat_response(user_input):
    """Generate chatbot response using g4f"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history + [{"role": "user", "content": user_input}]
    )
    return response.choices[0].message.content

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDF files
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

# Function to extract text from DOCX files
def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to check if the uploaded file is a resume
def is_resume(text):
    resume_keywords = ["experience", "education", "skills", "projects", "certifications", "summary", "work history"]
    found_keywords = sum(1 for keyword in resume_keywords if keyword in text.lower())
    return found_keywords >= 2

# Function to analyze resume content
def analyze_resume(text):
    keywords = ["education", "experience", "skills", "projects", "certifications"]
    score = sum(1 for keyword in keywords if keyword in text.lower()) * 20
    feedback = []

    if "education" not in text.lower():
        feedback.append("Add an education section.")
    if "experience" not in text.lower():
        feedback.append("Include your work experience.")
    if "skills" not in text.lower():
        feedback.append("Mention relevant skills.")
    if "projects" not in text.lower():
        feedback.append("List relevant projects.")
    if "certifications" not in text.lower():
        feedback.append("Highlight certifications to add credibility.")
    
    return score, feedback

# Routes
@app.route('/')
def index():
    """Render the chatbot UI and file upload form"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    data = request.json
    user_input = data.get("message", "").strip().lower()
    
    # List of common greetings
    greetings = ["hi", "hello", "hey", "hola", "namaste", "howdy"]
    
    # Default response for greetings
    if user_input in greetings:
        bot_response = "❓ I'm here to help! Ask me about career advice or request an image."
    
    # Check if the user is asking for an image
    elif user_input.startswith("/image"):
        image_prompt = user_input.replace("/image", "").strip()
        if not image_prompt:
            bot_response = "⚠️ Please provide a prompt for the image!"
        else:
            image_url = generate_dalle_image(image_prompt)
            bot_response = f"🖼️ Here is your image: {image_url}"
    
    # Check if the user asks about past inputs or outputs
    elif "previous" in user_input or "last response" in user_input:
        bot_response = "Here is our conversation history:\n" + "\n".join([f"You: {msg['content']}\nBot: {res}" for msg, res in zip(conversation_history[1:], conversation_history[2:])])
    
    else:
        bot_response = get_chat_response(user_input)
    
    # Save conversation history
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": bot_response})
    
    return jsonify({"response": bot_response})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads (PDF/DOCX resumes)"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Only resume (PDF/DOCX) files are accepted."})
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    # Extract text from the uploaded file
    if file.filename.endswith('.pdf'):
        resume_text = extract_text_from_pdf(file_path)
    elif file.filename.endswith('.docx'):
        resume_text = extract_text_from_docx(file_path)
    else:
        return jsonify({"error": "Unsupported file format."})
    
    if not is_resume(resume_text):
        return jsonify({"error": "Only resumes are accepted."})
    
    # Analyze the resume and generate score and feedback
    score, feedback = analyze_resume(resume_text)
    
    return jsonify({
        "filename": file.filename,
        "score": score,
        "feedback": feedback,
        "resume_content": resume_text,
        "file_url": f"/uploads/{file.filename}"
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
