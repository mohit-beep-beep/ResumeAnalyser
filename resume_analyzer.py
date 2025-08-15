import google.generativeai as genai
import os
import resume_parser
 
genai.configure(api_key='AIzaSyDHL1SgCIUkeJqAPf1HIEqljozIuJ2oCss')
def analyze_resume(resume_text):
    if not resume_text:
        return {"error": "Resume text is required for analysis."}
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    base_prompt = f"""
    You are a professional resume evaluator."Here's my resume:{resume_text}\nPlease score it out of 100, point out key improvements, and suggest how to tailor it for a software engineer role.:
    """

    response = model.generate_content(base_prompt)
    analysis = response.text.strip()
    return analysis

print(analyze_resume(resume_parser.extract_text_from_pdf(r"C:\Users\anime\Downloads\cv(resume).pdf")))
