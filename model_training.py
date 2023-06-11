import os
from pymongo import MongoClient
import gridfs
from transformers import GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling, Trainer, TrainingArguments, GPT2LMHeadModel
from database import Database  # Import Database class

# Tokenize the text data
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
tokenizer.pad_token = tokenizer.eos_token

# Function to fetch text data from MongoDB
def fetch_text_data(task_id):
    # Use 'db' object from Database class
    db = Database()
    data = db.find_one('SearchResults', {"task_id": task_id})
    
    # Check if data exists and 'results' field is in data
    if data and 'results' in data:
        return [item['text'] for item in data['results']]
    else:
        return []
    
# Function to save trained model to MongoDB using GridFS
def save_model_to_db(model_path, task_id):
    db = Database().db
    fs = gridfs.GridFS(db)
    with open(model_path, "rb") as f:
        model_data = f.read()
    model_id = fs.put(model_data, filename="pytorch_model.bin", ModelID="GPT-2", task_id=task_id)
    print(f"Model stored with file id {model_id}.")

# Function to train model
def train_model(task_id):
    # Fetch the data from the SearchResults collection based on the task_id
    texts = fetch_text_data(task_id)
    if not texts:
        print(f"No data found for task_id {task_id}. Aborting training.")
        return

    # Save texts to a file as the TextDataset requires a file as input
    with open('train_tmp.txt', 'w', encoding='utf-8') as f:   # Use 'utf-8' encoding here
        for text in texts:
            f.write(text + '\n')

    # Prepare the dataset and the data collator
    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path="train_tmp.txt",
        block_size=128,
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=False,
    )

    # Prepare the training arguments
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=1,
        per_device_train_batch_size=1,
        save_steps=10_000,
        save_total_limit=2,
    )

    # Initialize the GPT2 model
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # Initialize the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=dataset,
    )

    # Train the model
    trainer.train()
    
    def safe_filename(filename):
        keepcharacters = ('.', '_', '-')
        return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()

    # Save the trained model locally
    safe_task_id = safe_filename(task_id)
    model_path = f"./trained_model/{safe_task_id}/pytorch_model.bin"
    trainer.save_model(f"./trained_model/{safe_task_id}")
    
    # Store the trained model in MongoDB using GridFS
    save_model_to_db(model_path, task_id)

    print("Model training completed and saved to MongoDB.")
