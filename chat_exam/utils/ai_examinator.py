import google.generativeai as genai
from chat_exam.config import AI_KEY
import json
import re

genai.configure(api_key=AI_KEY)


class AIExaminator:
    def __init__(self, question_count: int):
        # === GENAI SETUP ===
        genai.configure(api_key=AI_KEY)
        self.model = genai.GenerativeModel("models/gemini-2.5-flash")

        # === SETTINGS ===
        self.max_words = 12
        self.max_questions = 6
        self.question_count = min(question_count, self.max_questions)

        # === QUESTION PROMPT ===
        self.question_prompt = f"""
        Respond ONLY with valid JSON.
        No text outside JSON.
        Write exactly {self.question_count} short exam questions (max {self.max_words} words each)
        Return ONLY this format:
        {{"q1": "Question 1","q2": "Question 2","q3": "Question 3"}}
        """

        self.verdict_prompt = """
        Evaluate how well the student understands their own code based on their written answers. 
        Rate the understanding from 1 to 5, where 1 = poor and 5 = excellent. 
        Respond only with a JSON object: {"rating": number (int), "verdict": "short explanation max (≈ 20w) (str)"}.
        """

    # === CREATE QUESTIONS ===
    def create_questions(self, content: str) -> dict:
        """
        Create questions based on code and prompt with GenAI
        :param content: the code (str)
        :return: dict like {"q1": "...", "q2": "..."}
        """
        ask_ai_text = f"{self.question_prompt}\n{content}"
        response = self.model.generate_content(ask_ai_text)
        response_text = response.text.strip()

        # === LOG THE RESPONSE AND TOKEN USAGE ===
        print("\n\n=== AI CREATED QUESTIONS ===")
        print("Questions Prompt:")
        print(self.question_prompt)
        print("\n--- Content Preview ---")
        print(content[:200])
        print("\n--- Raw Response ---")
        print(response_text)

        if response.usage_metadata:
            print("\n=== TOKEN USAGE ===")
            print(f"Prompt Tokens: {response.usage_metadata.prompt_token_count}")
            print(f"Response Tokens: {response.usage_metadata.candidates_token_count}")
            print(f"Total Tokens: {response.usage_metadata.total_token_count}")

        # === CLEAN AND PARSE JSON ===
        try:
            clean_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()
            data = json.loads(clean_text)
            print("\n=== PARSED QUESTIONS DICT ===")
            print(data)
            return data
        except json.JSONDecodeError as e:
            print(f"\n### ERROR PARSING JSON QUESTIONS: {e} ###")
            print("Response text:", response_text)
            return {"error": "Invalid JSON from model"}

    # === CREATE VERDICT ===
    def create_verdict(self, code: str, questions: dict, answers: dict) -> tuple[str, int]:
        """
        Create verdict based on code, questions, and answers using GenAI

        :param code: the code (str)
        :param questions: the questions (dict)
        :param answers: the answers (dict)

        :return: (feedback (str), grading (int))
        """
        ask_ai_text = f"{self.verdict_prompt}\nCode:{code}\nQuestions:{questions}\nAnswers:{answers}"
        response = self.model.generate_content(ask_ai_text)
        response_text = response.text.strip()

        print("\n\n=== AI CREATED VERDICT ===")
        print("Prompt:\n", self.verdict_prompt)
        print("\n--- Raw Response ---")
        print(response_text)

        if response.usage_metadata:
            print("\n=== TOKEN USAGE ===")
            print(f"Prompt Tokens: {response.usage_metadata.prompt_token_count}")
            print(f"Response Tokens: {response.usage_metadata.candidates_token_count}")
            print(f"Total Tokens: {response.usage_metadata.total_token_count}")

        try:
            clean_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()
            data = json.loads(clean_text)
            verdict = data.get("verdict", "No verdict generated.")
            rating = data.get("rating", 0)
            print("\n=== PARSED VERDICT ===")
            print(f"Verdict: {verdict}")
            print(f"Rating: {rating}")
            return verdict, rating
        except json.JSONDecodeError as e:
            print(f"\n### ERROR PARSING VERDICT JSON: {e} ###")
            print("Response text:", response_text)
            return "Error parsing AI response", 0


# === DEBUG TEST RUN ===
if __name__ == "__main__":
    examinator = AIExaminator(3)
    questions = examinator.create_questions("print('Hello, World!')")
    print("\n=== QUESTIONS OUTPUT ===")
    for key, val in questions.items():
        print(f"{key}: {val}")
