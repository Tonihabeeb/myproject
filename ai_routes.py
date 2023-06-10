from flask import Blueprint, request, jsonify
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import openai
import os
import dotenv
from datetime import datetime
import uuid
from database import Database

dotenv.load_dotenv()

# Create a Database object
db = Database()

# Load API key from the .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load the fine-tuned model and tokenizer
model_path = "./trained_model/gpt2-large"
model = GPT2LMHeadModel.from_pretrained(model_path)
tokenizer = GPT2Tokenizer.from_pretrained("gpt2-large")
ai_routes = Blueprint('ai_routes', __name__)

MODEL_NAME = "text-davinci-003"

@ai_routes.route('/start_conversation', methods=['POST'])
def start_conversation():
    data = request.get_json()
    user_id = data.get('userId')
    task_id = data.get('task_id')

    # create new session
    session_id = str(uuid.uuid4())

    # save the session to your database with an associated user and task_id
    db.insert_one('ChatSessions', {
        'userId': user_id,
        'sessionId': session_id,
        'task_id': task_id,  
        'time': datetime.utcnow(),  
    })

    # start the conversation with the AI
    start_message = "Hello, how can I assist you today?"

    # save AI's message
    db.insert_one('ChatMessages', {
        'message': start_message,
        'userId': None,  # userId is None for AI messages
        'sessionId': session_id,
        'task_id': task_id,  
        'time': datetime.utcnow(),  
    })

    return jsonify({'message': start_message, 'sessionId': session_id})

@ai_routes.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    user_id = data.get('userId')
    session_id = data.get('sessionId')
    task_id = data.get('task_id')

    # save user's message
    db.insert_one('ChatMessages', {
        'message': user_message,
        'userId': user_id,
        'sessionId': session_id,
        'task_id': task_id,  
        'time': datetime.utcnow(),  
    })

    # fetch conversation history
    conversation_history = db.fetch_conversation(session_id)

    # concatenate the conversation history and the user's new message to form the AI's prompt
    ai_prompt = conversation_history + "\nUser: " + user_message

    # get AI's response
    response = openai.Completion.create(
        engine=MODEL_NAME,
        prompt=ai_prompt,
        max_tokens=1000,
        temperature=0.7,
    )

    ai_message = response.choices[0].text.strip()

    # save AI's message
    db.insert_one('ChatMessages', {
        'message': ai_message,
        'userId': None,  # userId is None for AI messages
        'sessionId': session_id,
        'task_id': task_id,  
        'time': datetime.utcnow(),  
    })

    return jsonify({'message': ai_message})

@ai_routes.route("/generate", methods=["POST"])
def generate_text_v1():
    prompt = request.form["prompt"]
    response = openai.Completion.create(
        engine=MODEL_NAME,
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=1.0,
    )

    generated_text = response.choices[0].text.strip()
    return jsonify({"generated_text": generated_text})

@ai_routes.route('/generate-text', methods=['POST'])
def generate_text_v2():
    data = request.get_json()
    user_input = data.get('input')
    max_length = data.get('max_length', 100)  # Set a default max_length of 100 tokens

    # Generate text using the fine-tuned model
    input_ids = tokenizer.encode(user_input, return_tensors="pt")
    output = model.generate(input_ids, max_length=max_length, num_return_sequences=1)

    # Decode the generated text
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

    return jsonify({'generated_text': generated_text})
