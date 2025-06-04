CREATE VECTOR INDEX `document-embeddings`
FOR (n: DocumentNode) ON (n.vector)
OPTIONS {indexConfig: {
 `vector.dimensions`: 512,
 `vector.similarity_function`: 'cosine'
}};