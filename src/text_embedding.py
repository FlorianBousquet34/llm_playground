import ollama
    
class OllamaEmbeddingModel:
    
    @staticmethod
    def embed_documents(sentences, chunk_size=512, model_name='nomic-embed-text:v1.5'):
        batches = [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]
        embeddings = []
        for batch_sentences in batches:
            response = ollama.embed(
                model=model_name,
                input=batch_sentences
            )
            embeddings.extend(response.embeddings)
        return embeddings