import ollama
    
class OllamaEmbeddingModel:
    
    @staticmethod
    def embed_documents(sentences, chunk_size=512, model_name='nomic-embed-text:v1.5', log_progess=False):
        batches = [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]
        embeddings = []
        tot = len(batches)
        for i_batch, batch_sentences in enumerate(batches):
            if log_progess:
                print(f"Batch {i_batch + 1} / {tot}               ", end="\r")
            response = ollama.embed(
                model=model_name,
                input=batch_sentences
            )
            embeddings.extend(response.embeddings)
        if log_progess:
            print("\n")
        return embeddings