import os
import dotenv
from pymongo import MongoClient
import openai

dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

GPT3_5Turbo = 'text-davinci-003.5'
GPT4 = 'gpt-4-0314'
MODEL_NAME_GPT3_5Turbo = GPT3_5Turbo
MODEL_NAME_GPT4 = GPT4

client = MongoClient(os.getenv("mongodb://localhost:27017/"))
db = client.get_database('ai_app_db')
tasks = db.get_collection('Tasks')

def generate_document_content(session_id, messages):
    # Fetch task for the session
    task = tasks.find_one({"sessionId": session_id})['task']

    # Get format suggestion from GPT-3.5 Turbo
    format_suggestion = GPT3_5Turbo.Completion.create(
        model=MODEL_NAME_GPT3_5Turbo,
        prompt=f"Please suggest an appropriate format for a {task} document.",
        temperature=0.5,
        max_tokens=100
    ).choices[0].text.strip()

    # Convert the list of messages into a single string
    messages_str = ' '.join([msg['message'] for msg in messages])

    # Create the prompt for GPT-4
    prompt = f"Please generate content for a {task} document in the following format:\n{format_suggestion}\nBased on the following data:\n{messages_str}"

    # Get the AI's response
    response = GPT4.Completion.create(
        model=MODEL_NAME_GPT4,
        prompt=prompt,
        temperature=0.5,
        max_tokens=1000
    )

    # Extract the generated content
    content = response.choices[0].text.strip()

    return content
