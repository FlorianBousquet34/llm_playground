import socket
from urllib3.connection import HTTPConnection
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_llm_model(model_name="deepseek-ai/deepseek-coder-1.3b-instruct"):
    local_path = f"models/{model_name}"
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

def call_llm_model(messages, model_name="deepseek-ai/deepseek-coder-1.3b-instruct", tools = None):
        
    model, tokenizer = load_llm_model(model_name)
    
    with open("resources/chat_templates/tool_use_chat_template.jinja", "r", encoding="utf-8") as use_chat_template_file:
        with open("resources/chat_templates/chat_template.jinja", "r", encoding="utf-8") as default_template_file:
            tokenizer.chat_template = {
                "tool_use": use_chat_template_file.read(),
                "default": default_template_file.read()
            }
            
    model.eval()
    with torch.no_grad():
        # Format the chat input
        inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tools=tools, return_dict=True)

        # Generate the response
        outputs = model.generate(torch.Tensor([inputs['input_ids']]).to(torch.int32), max_new_tokens=128, top_k=50, top_p=0.95, num_return_sequences=1, eos_token_id=tokenizer.eos_token_id)

        # Decode and display the response
        question = tokenizer.decode(inputs['input_ids'])
        response = tokenizer.decode(outputs[0][len(inputs["input_ids"]):])
    
    return question, response.replace("<|im_end|>", "")
    
    