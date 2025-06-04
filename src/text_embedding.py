import gc
import torch
from transformers import AutoModel, AutoTokenizer
import socket
from urllib3.connection import HTTPConnection
import os

def load_text_embedding_model(model_name='thenlper/gte-small'): #'Alibaba-NLP/gte-large-en-v1.5'
    local_path = f"./models/{model_name}"
    if os.path.exists(local_path):
        model = AutoModel.from_pretrained(f"{local_path}/model")
        tokenizer = AutoTokenizer.from_pretrained(f"{local_path}/tokenizer")
    else:
        HTTPConnection.default_socket_options = ( 
            HTTPConnection.default_socket_options + [
            (socket.SOL_SOCKET, socket.SO_SNDBUF, 20000000), 
            (socket.SOL_SOCKET, socket.SO_RCVBUF, 20000000)
        ])
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        model.save_pretrained(f"{local_path}/model")
        tokenizer.save_pretrained(f"{local_path}/tokenizer")
        
    return model, tokenizer

def embed_documents(sentences, chunk_size=512, model_name='thenlper/gte-small'):

    model, tokenizer = load_text_embedding_model(model_name)
    model.eval()
    with torch.no_grad():
        batches = [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]
        embeddings = []
        
        for batch_sentences in batches:

            # Tokenize the input texts
            batch_dict = tokenizer(batch_sentences, max_length=8192, padding=True, truncation=True, return_tensors='pt')

            # Apply model
            bacth_outputs = model(**batch_dict)
            bacth_embeddings = bacth_outputs.last_hidden_state[:, 0]
            embeddings.extend(bacth_embeddings)
    
    return embeddings