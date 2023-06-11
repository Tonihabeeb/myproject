from transformers import GPT2LMHeadModel, GPT2Tokenizer

model_name = "gpt2-large"

tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

# Save the model and tokenizer to a directory
model.save_pretrained("./trained_model/gpt2-large")
tokenizer.save_pretrained("./trained_model/gpt2-large")
