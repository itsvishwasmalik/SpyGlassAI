import pickle
from pathlib import Path
from time import perf_counter as timer
import textwrap
import re
from typing import List, Dict, Union, Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Import model loader
from model_loader import get_model_loader

# Initialize model loader
print("[INFO] Initializing model loader...")
loader = get_model_loader()
model, tokenizer = loader.get_model()
print("[INFO] Model initialization complete")

class TextRetriever:
    def __init__(self, vector_store_dir='vector_store', model_name='all-mpnet-base-v2', device='cpu', use_gpu=False):
        """Initialize the TextRetriever with vector store and model settings."""
        # Get language model and tokenizer
        self.llm_loader = get_model_loader()
        self.llm_model, self.tokenizer = self.llm_loader.get_model()
        self.device = device
        self.vector_store_dir = Path(vector_store_dir)
        self.embedding_model = SentenceTransformer(model_name_or_path=model_name, device=device)
        self.query_cache = {}
        
        # Load FAISS index and metadata
        self.use_gpu = use_gpu
        self.load_vector_store()
        
        # Common question patterns for query expansion
        self.question_patterns = {
            'where': ['location of', 'place where', 'source of', 'originates from'],
            'what': ['describe', 'explain', 'tell me about'],
            'how': ['method of', 'process of', 'way to'],
            'why': ['reason for', 'cause of', 'explain why'],
            'when': ['time when', 'period when', 'date when']
        }
    
    def load_vector_store(self) -> None:
        """Load the FAISS index and metadata from disk."""
        # Load FAISS index
        self.index = faiss.read_index(str(self.vector_store_dir / 'embeddings.faiss'))
        
        # Use GPU if requested and available
        if self.use_gpu and faiss.get_num_gpus() > 0:
            self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
        
        # Load metadata
        with open(self.vector_store_dir / 'metadata.pkl', 'rb') as f:
            self.metadata = pickle.load(f)
            
        print(f"Loaded {self.index.ntotal} embeddings of dimension {self.index.d}")
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode query text to embedding vector, with caching."""
        if query in self.query_cache:
            return self.query_cache[query]
            
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=False, normalize_embeddings=True)
        self.query_cache[query] = query_embedding
        return query_embedding
    
    def preprocess_query(self, query: str) -> List[str]:
        """Preprocess and expand the query for better matching."""
        # Clean the query
        query = query.lower().strip()
        query = re.sub(r'[^\w\s?]', ' ', query)
        query = re.sub(r'\s+', ' ', query)
        
        # Generate query variations
        queries = [query]
        
        # Expand based on question words
        for question_word, variations in self.question_patterns.items():
            if query.startswith(question_word):
                rest_of_query = query[len(question_word):].strip()
                for variation in variations:
                    expanded_query = f"{variation} {rest_of_query}"
                    queries.append(expanded_query)
        
        return queries
    
    def batch_search(self, queries: List[str], top_k: int = 5) -> List[List[Dict]]:
        """Perform batch search for multiple queries efficiently.
        
        Args:
            queries (List[str]): List of query strings
            top_k (int): Number of results to return per query
            
        Returns:
            List[List[Dict]]: List of results for each query
        """
        # Encode all queries
        query_embeddings = np.vstack([self.encode_query(q) for q in queries])
        
        # Perform batch search
        start_time = timer()
        scores, indices = self.index.search(query_embeddings, top_k)
        end_time = timer()
        
        # Format results for each query
        all_results = []
        for query_scores, query_indices in zip(scores, indices):
            results = [
                {
                    'score': float(score),
                    'metadata': self.metadata[idx],
                    'text': self.metadata[idx]['sentence_chunk'],
                    'page': self.metadata[idx]['page_number']
                }
                for score, idx in zip(query_scores, query_indices)
                if idx != -1  # Filter out invalid indices
            ]
            all_results.append(results)
            
        print(f"Batch search completed in {end_time-start_time:.5f} seconds")
        return all_results
    
    def search(self, query: str, top_k: int = 5, similarity_metric: str = 'cosine', 
              min_score: float = 0.1, print_results: bool = True, return_context: bool = False) -> Union[List[Dict], str]:
        """Search for relevant text chunks using a query."""
        # Preprocess and expand query
        queries = self.preprocess_query(query)
        
        # Search with all query variations
        all_results = []
        for q in queries:
            # Encode query
            query_embedding = self.encode_query(q)
            
            # Perform search
            start_time = timer()
            if similarity_metric == 'cosine':
                query_embedding = query_embedding.reshape(1, -1)
                distances, indices = self.index.search(query_embedding, top_k)
                scores = 1 - distances[0]  # Convert distance to similarity
                indices = indices[0]
            else:
                distances, indices = self.index.search(query_embedding.reshape(1, -1), top_k)
                scores = distances[0]
                indices = indices[0]
            
            # Collect results
            for score, idx in zip(scores, indices):
                if idx == -1 or score < min_score:
                    continue
                    
                result = {
                    'score': float(score),
                    'metadata': self.metadata[idx],
                    'text': self.metadata[idx]['sentence_chunk'],
                    'page': self.metadata[idx]['page_number'],
                    'query_variation': q
                }
                all_results.append(result)
        
        # Remove duplicates and sort by score
        unique_results = []
        seen_texts = set()
        for result in sorted(all_results, key=lambda x: x['score'], reverse=True):
            text = result['text']
            if text not in seen_texts:
                seen_texts.add(text)
                unique_results.append(result)
        
        # Take top k unique results
        unique_results = unique_results[:top_k]
        
        if print_results:
            print(f"\nResults for query: '{query}'")
            for result in unique_results:
                print(f"\nScore: {result['score']:.4f}")
                print(f"Query variation: {result['query_variation']}")
                print("Text:")
                self._print_wrapped(result['text'])
                print(f"Page number: {result['page']}")
        
        if return_context:
            # Combine all retrieved texts into a single context
            context = "\n\n".join([r['text'] for r in unique_results])
            return context
        return unique_results
    
    def retrieve_context(self, query: str, top_k: int = 1) -> List[Dict]:
        """Step 1: Retrieve relevant context from the knowledge base."""
        results = self.search(query, top_k=top_k, print_results=False)
        if not results:
            return []
        return results
    
    def augment_query(self, query: str, context: str, confidence: float) -> str:
        """Step 2: Augment the query with retrieved context."""
        # Create prompt template with context and confidence information
        dialogue_template = [
            {"role": "system", 
             "content": f"You are a helpful assistant. Using the provided context, give a direct and concise answer without repeating the question. Context: {context}"}, 
            {"role": "user", 
             "content": query}
        ]
        
        # Apply chat template to create the augmented query
        augmented_query = self.tokenizer.apply_chat_template(
            conversation=dialogue_template,
            tokenize=False,
            add_generation_prompt=True
        )
        return augmented_query
    
    def generate_answer(self, augmented_query: str, max_length: int = 256) -> str:
        """Step 3: Generate answer using the language model."""
        # Tokenize and generate
        inputs = self.tokenizer(augmented_query, return_tensors="pt", truncation=True)
        outputs = self.llm_model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True  # Enable sampling for more natural responses
        )
        
        # Decode the response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    
    def generate_response(self, query: str, max_length: int = 256) -> str:
        """Execute the full RAG pipeline: Retrieve -> Augment -> Generate."""
        # Step 1: Retrieve relevant context
        results = self.retrieve_context(query)
        if not results:
            return "I couldn't find any relevant information to answer your question."
        
        # Get the top result
        top_result = results[0]
        context = top_result['text']
        confidence = top_result['score']
        
        # Step 2: Augment the query with context
        augmented_query = self.augment_query(query, context, confidence)
        # Step 3: Generate the answer
        response = self.generate_answer(augmented_query, max_length)
        # Clean up the response by removing any system prompts
        cleaned_response = self._clean_response(response)
        # Format final response with confidence
        final_response = f"Answer (Confidence: {confidence:.2f}):\n{cleaned_response}"
        return final_response
    
    @staticmethod
    def _print_wrapped(text: str, wrap_length: int = 80) -> None:
        """Utility method to print text with wrapping."""
        wrapped_text = textwrap.fill(text, wrap_length)
        print(wrapped_text)
        
    @staticmethod
    def _clean_response(response: str) -> str:
        """Clean up the response by removing system prompts and other artifacts."""
        # First remove the complete system and user messages
        response = re.sub(r'<\|system\|>.*?(?=<\|assistant\|>)', '', response, flags=re.DOTALL)
        response = re.sub(r'<\|user\|>.*?(?=<\|assistant\|>)', '', response, flags=re.DOTALL)
        
        # Remove any remaining special tokens
        response = re.sub(r'<\|assistant\|>', '', response)
        response = re.sub(r'<\|system\|>', '', response)
        response = re.sub(r'<\|user\|>', '', response)
        response = re.sub(r'<\|.*?\|>', '', response)
        
        # Clean up any question repetition at the start
        response = re.sub(r'^[^.?!]*\?\s*', '', response)
        
        # Clean up whitespace
        response = re.sub(r'\s+', ' ', response)
        response = response.strip()
        
        return response

def main():
    # Example usage
    retriever = TextRetriever(use_gpu=False)  # Use CPU only
    
    # Example RAG query
    query = "Where does ganga river originates from ?"
    print("\nQuestion:")
    print(f"{query}")
    
    # Get response using RAG
    response = retriever.generate_response(query)
    print("\nResponse:")
    print(response)

if __name__ == '__main__':
    main()