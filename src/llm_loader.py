import socket
from urllib3.connection import HTTPConnection
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_llm_model(model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
    local_path = f"./models/{model_name}"
    if os.path.exists(local_path):
        model = AutoModelForCausalLM.from_pretrained(f"{local_path}/model", trust_remote_code=True, torch_dtype=torch.bfloat16)
        tokenizer = AutoTokenizer.from_pretrained(f"{local_path}/tokenizer", trust_remote_code=True)
    else:
        HTTPConnection.default_socket_options = ( 
            HTTPConnection.default_socket_options + [
            (socket.SOL_SOCKET, socket.SO_SNDBUF, 20000000), 
            (socket.SOL_SOCKET, socket.SO_RCVBUF, 20000000)
        ])
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True, torch_dtype=torch.bfloat16)
        model.save_pretrained(f"{local_path}/model")
        tokenizer.save_pretrained(f"{local_path}/tokenizer")
        
    return model, tokenizer

def call_llm_model(user_messages, system_messages, model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
    
    messages = ([ {"role": "user", "content": message} for message in user_messages]
        + [ {"role": "system", "content": message} for message in system_messages])
    
    model, tokenizer = load_llm_model(model_name)
    model.eval()
    with torch.no_grad():
        # Format the chat input
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # Tokenize the formatted input
        inputs = tokenizer(input_text, return_tensors="pt")

        # Generate the response
        outputs = model.generate(inputs, max_new_tokens=512, do_sample=False, top_k=50, top_p=0.95, num_return_sequences=1, eos_token_id=tokenizer.eos_token_id)

        # Decode and display the response
        response = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
    
    return response
    
    