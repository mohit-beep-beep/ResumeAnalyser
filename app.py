import os
import re
import json
import ast
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import resume_parser
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Load env vars (optional if using .env)
from dotenv import load_dotenv
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Initialize Nebius OpenAI-compatible client
client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.environ.get("OPENAI_API_KEY")  # Use your Nebius key here
)

# Serve front.html
@app.route('/')
def index():
    return render_template('front.html')

# Resume upload endpoint
@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        text = resume_parser.extract_text_from_pdf(file)
        if not text.strip():
            return jsonify({"error": "Failed to extract text from resume"}), 400
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": f"Failed to parse resume: {str(e)}"}), 500

# Resume analysis endpoint
@app.route('/api/analyze-resume', methods=['POST'])
def analyze_resume():
    data = request.get_json()
    resume_text = data.get("resume", "")
    job_description = data.get("jobDescription", "")
    requirements = data.get("requirements", "")

    if not resume_text:
        return jsonify({"error": "Resume text is required."}), 400

    try:
        # Prompt the model
        prompt = f"""
You are a professional resume evaluator.
please go through the work experience, skills, and education sections of the resume see what the projects is and wheater it matches the job description and requirements.
analyze the projects and you check if the projects match the job description and requirements.
also score the resume out of 100 if the projects don't match the job description and requirements decrease the score,always give a harsh score only if projects are complicated give a good score, point out key improvements, and suggest how to tailor it.
Strictly check whether the uploaded text is a resume or not give a score of 0 if it is not a resume.
Analyze the resume below for the job description provided.
Respond ONLY in this exact JSON format (no extra commentary):

{{
  "score": <int>, 
  "matchingSkills": [<skill1>, <skill2>, ...], 
  "missingSkills": [<skill1>, <skill2>, ...], 
  "suggestions": [<suggestion1>, <suggestion2>, ...]
}}

Resume:
{resume_text}

Job Description:
{job_description}

Requirements:
{requirements}
"""

        # Call Nebius model (LLaMA 3)
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )

        output_text = completion.choices[0].message.content
        app.logger.info("Model output:\n%s", output_text)

        # Extract JSON-like structure from model output
        json_match = re.search(r"\{(?:[^{}]|(?:\{.*?\}))*\}", output_text, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON found in model output.")

        json_str = json_match.group()
        json_str = (
            json_str.replace("“", "\"")
                    .replace("”", "\"")
                    .replace("‘", "'")
                    .replace("’", "'")
                    .replace("\n", " ")
                    .strip()
        )

        # Try standard JSON parsing first, then fallback
        try:
            parsed_json = json.loads(json_str)
        except json.JSONDecodeError:
            parsed_json = ast.literal_eval(json_str)

        return jsonify(parsed_json)

    except Exception as e:
        app.logger.exception("Resume analysis failed.")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
