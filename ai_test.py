import google.generativeai as genai
from chat_exam.config import AI_KEY

genai.configure(api_key=AI_KEY)

# välj modell (snabb och billig för test)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# din prompt
prompt = """
Respond ONLY with valid JSON.
No text outside JSON.
Write exactly 5 short exam questions (max 12 words each).
Return in this format:
{"questions":[
 {"id":1,"q":"Q1"},
 {"id":2,"q":"Q2"},
 {"id":3,"q":"Q3"},
 {"id":4,"q":"Q4"},
 {"id":5,"q":"Q5"}]}
"""


# kör modellen
response = model.generate_content(prompt)

# printa AI-svaret
print("Response text:\n", response.text)

# printa tokenanvändning (om metadata finns)
if response.usage_metadata:
    print("\nToken usage:")
    print("  Prompt tokens:    ", response.usage_metadata.prompt_token_count)
    print("  Response tokens:  ", response.usage_metadata.candidates_token_count)
    print("  Total tokens:     ", response.usage_metadata.total_token_count)
