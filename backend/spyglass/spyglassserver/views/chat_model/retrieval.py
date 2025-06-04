import pickle
from pathlib import Path
from time import perf_counter as timer
from typing import List, Dict, Union, Optional
import numpy as np
import faiss
import re
import textwrap
from django.conf import settings
from sentence_transformers import SentenceTransformer

from spyglassserver.views.chat_model.model_loader import get_model_loader
from sentence_transformers import SentenceTransformer

loader = get_model_loader()
model_llm, tokenizer_llm = loader.get_model()

class TextRetriever:
    def __init__(self, user_id=None, doc_id=None, vector_store_dir='vector_store', model_name='all-mpnet-base-v2', device='cpu', use_gpu=False):
        """Initialize the TextRetriever with vector store and model settings.
        
        Args:
            user_id (str, optional): User ID to filter documents by owner
            doc_id (str, optional): Specific document ID to query against. If None, queries all user's documents.
            vector_store_dir (str): Base directory containing vector stores
            model_name (str): Name of the sentence transformer model to use
            device (str): Device to run model on ('cpu' or 'cuda')
            use_gpu (bool): Whether to use GPU for FAISS indexing
        """
            
        # Get language model and tokenizer
        self.llm_model = model_llm
        self.tokenizer = tokenizer_llm
        self.device = device
        self.user_id = user_id
        self.doc_id = doc_id
        
        print(vector_store_dir,"==============")
        
        self.vector_store_dir = Path(vector_store_dir)
            
        # Create directory if it doesn't exist
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(model_name_or_path=model_name, device=device)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize sentence transformer: {str(e)}")

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
        try:
            # Check if index exists for this user
            index_path = self.vector_store_dir / 'embeddings.faiss'
            print(index_path,"======yolo======")
            metadata_path = self.vector_store_dir / 'metadata.pkl'
            
            if not index_path.exists() or not metadata_path.exists():
                # Create empty index if it doesn't exist - use IP (Inner Product) similarity
                dimension = 768  # Default dimension for 'all-mpnet-base-v2'
                self.index = faiss.IndexFlatIP(dimension)  # Changed from IndexFlatL2 to IndexFlatIP
                self.metadata = []
                return
                
            # Load existing FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Use GPU if requested and available
            if self.use_gpu and faiss.get_num_gpus() > 0:
                self.index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, self.index)
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            print(f"Loaded {self.index.ntotal} embeddings of dimension {self.index.d}")
            print(f"Number of metadata entries: {len(self.metadata)}")
            if self.index.ntotal == 0:
                print("Warning: FAISS index is empty!")
            if len(self.metadata) == 0:
                print("Warning: No metadata loaded!")
            
            # Debug metadata format
            if self.metadata:
                print(f"\nMetadata type: {type(self.metadata[0])}")
                print(f"Metadata dir: {dir(self.metadata[0]) if hasattr(self.metadata[0], '__dir__') else None}")
                print(f"Metadata vars: {vars(self.metadata[0]) if hasattr(self.metadata[0], '__dict__') else None}")
                print(f"First metadata item: {self.metadata[0]}")
            
        except Exception as e:
            print(f"Error loading vector store: {e}")
            # Initialize empty index and metadata
            dimension = 768  # Default dimension for 'all-mpnet-base-v2'
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata = []
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode query text to embedding vector, with caching."""
        if query in self.query_cache:
            return self.query_cache[query]
            
        # Changed normalize_embeddings to False to get raw embeddings
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=False, normalize_embeddings=False)
        
        # Manual L2 normalization if needed
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        self.query_cache[query] = query_embedding
        return query_embedding
    
    def _classify_question_type(self, query: str) -> str:
        """Classify the type of question to better handle the query.
        
        Args:
            query (str): The user's question
            
        Returns:
            str: Question type ('factoid', 'descriptive', 'causal', 'comparative', or 'other')
        """
        query = query.lower()
        
        # Define patterns for different question types
        patterns = {
            'factoid': r'^(what|who|when|where|which|how many|how much)',
            'descriptive': r'^(describe|explain|elaborate|what is|how does|tell me about)',
            'causal': r'^(why|what causes|what caused|how come|what is the reason)',
            'comparative': r'(compare|difference between|similarities|better|worse|versus|vs)',
            'procedural': r'^(how to|how do|what steps|process of|method of)'
        }
        
        for q_type, pattern in patterns.items():
            if re.search(pattern, query):
                return q_type
        return 'other'

    def preprocess_query(self, query: str) -> List[str]:
        """Preprocess and expand the query for better matching.
        
        Args:
            query (str): The user's question
            
        Returns:
            List[str]: List of query variations
        """
        # Clean the query
        query = query.lower().strip()
        query = re.sub(r'[^\w\s?]', ' ', query)
        query = re.sub(r'\s+', ' ', query)
        
        # Get question type
        q_type = self._classify_question_type(query)
        
        # Generate query variations
        queries = [query]
        
        # Base variations from question patterns
        for question_word, variations in self.question_patterns.items():
            if query.startswith(question_word):
                rest_of_query = query[len(question_word):].strip()
                for variation in variations:
                    expanded_query = f"{variation} {rest_of_query}"
                    queries.append(expanded_query)
        
        # Add type-specific variations
        if q_type == 'descriptive':
            queries.extend([
                f"summary of {query}",
                f"overview of {query}",
                f"description of {query}"
            ])
        elif q_type == 'causal':
            queries.extend([
                f"cause of {query}",
                f"reason for {query}",
                f"explanation for {query}"
            ])
        elif q_type == 'comparative':
            # Extract entities being compared
            entities = re.findall(r'between\s+(.+?)\s+and\s+(.+?)(?:\s+|$)', query)
            if entities:
                e1, e2 = entities[0]
                queries.extend([
                    f"differences {e1} {e2}",
                    f"similarities {e1} {e2}",
                    f"comparison {e1} {e2}"
                ])
        
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
        
        print(f"Searching for query variations: {queries}")
        print(f"Current index size: {self.index.ntotal} vectors")
        print(f"Number of metadata entries: {len(self.metadata)}")
        
        # Search with all query variations
        all_results = []
        print(f"Starting search with {len(queries)} query variations")
        
        for q in queries:
            # Encode query
            query_embedding = self.encode_query(q)
            print(f"Query '{q}' encoded to shape: {query_embedding.shape}")
            
            # Perform search
            start_time = timer()
            # Using IP similarity - scores are already similarities (higher is better)
            query_embedding = query_embedding.reshape(1, -1)
            scores, indices = self.index.search(query_embedding, top_k)
            scores = scores[0]  # IP similarity scores
            indices = indices[0]
            print(f"IP similarity search results - scores: {scores}, indices: {indices}")
            
            # Collect results
            results_for_query = 0
            for score, idx in zip(scores, indices):
                if idx == -1 or score < min_score:
                    print(f"Skipping result - idx: {idx}, score: {score} (below min_score: {min_score})")
                    continue
                    
                metadata = self.metadata[idx]
                print(f"\nProcessing metadata: {metadata}")  # Debug print
                
                # Extract text and metadata using multiple approaches
                text = None
                page = 0
                doc_id = ''
                
                # Method 1: Direct attribute access
                if hasattr(metadata, 'text'):
                    text = metadata.text
                elif hasattr(metadata, 'sentence_chunk'):
                    text = metadata.sentence_chunk
                elif hasattr(metadata, 'content'):
                    text = metadata.content
                    
                if hasattr(metadata, 'page_number'):
                    page = metadata.page_number
                elif hasattr(metadata, 'page'):
                    page = metadata.page
                    
                if hasattr(metadata, 'doc_id'):
                    doc_id = metadata.doc_id
                elif hasattr(metadata, 'document_id'):
                    doc_id = metadata.document_id
                
                # Method 2: Dictionary access
                if text is None and isinstance(metadata, dict):
                    text = metadata.get('text', metadata.get('sentence_chunk', metadata.get('content', '')))
                    page = metadata.get('page_number', metadata.get('page', 0))
                    doc_id = metadata.get('doc_id', metadata.get('document_id', ''))
                
                # Method 3: __dict__ access
                if text is None and hasattr(metadata, '__dict__'):
                    vars_dict = vars(metadata)
                    text = vars_dict.get('text', vars_dict.get('sentence_chunk', vars_dict.get('content', '')))
                    page = vars_dict.get('page_number', vars_dict.get('page', 0))
                    doc_id = vars_dict.get('doc_id', vars_dict.get('document_id', ''))
                
                # If we still couldn't get the text, skip this result
                if not text:
                    print(f"Warning: Could not extract text from metadata: {metadata}")
                    continue
                
                print(f"Extracted - Text: {text[:100]}..., Page: {page}, Doc ID: {doc_id}")  # Debug print

                result = {
                    'score': float(score),
                    'metadata': {'doc_id': doc_id},  # Only include necessary metadata
                    'text': text,
                    'page': page,
                    'query_variation': q
                }
                all_results.append(result)
                results_for_query += 1
            
            print(f"Added {results_for_query} results for query '{q}'")
        
        print("result", all_results) # Remove duplicates and sort by score
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
        """Step 1: Retrieve relevant context from the knowledge base.
        
        Args:
            query (str): The user's question
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict]: List of relevant context chunks with metadata
        """
        results = self.search(query, top_k=top_k, print_results=False)
        
        print(results,"=====yolo2======")
        
        # Filter results by document ID if specified
        if self.doc_id and results:
            filtered_results = []
            for r in results:
                result_doc_id = r['metadata'].get('doc_id') if isinstance(r['metadata'], dict) else getattr(r['metadata'], 'doc_id', None)
                if not result_doc_id or result_doc_id == self.doc_id:
                    filtered_results.append(r)
            results = filtered_results
            
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
    
    def add_document(self, text_chunks: List[str], metadata_list: List[Dict], save: bool = True) -> None:
        """Add document chunks and their metadata to the vector store."""
        if len(text_chunks) != len(metadata_list):
            raise ValueError("Number of text chunks must match number of metadata entries")

        # Validate metadata format
        required_keys = {'doc_id', 'sentence_chunk', 'page_number'}
        for i, metadata in enumerate(metadata_list):
            if not isinstance(metadata, dict):
                metadata_list[i] = {
                    'doc_id': str(metadata.doc_id) if hasattr(metadata, 'doc_id') else '',
                    'sentence_chunk': text_chunks[i],
                    'page_number': getattr(metadata, 'page_number', 0)
                }
            elif not all(key in metadata for key in required_keys):
                # Add missing keys with default values
                metadata['doc_id'] = metadata.get('doc_id', '')
                metadata['sentence_chunk'] = metadata.get('sentence_chunk', text_chunks[i])
                metadata['page_number'] = metadata.get('page_number', 0)

        # Compute embeddings for all chunks - use same settings as query encoding
        embeddings = self.embedding_model.encode(text_chunks, convert_to_tensor=False, normalize_embeddings=False)
        
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
        
        # Add embeddings to FAISS index
        self.index.add(embeddings)
        
        # Add metadata
        self.metadata.extend(metadata_list)
        
        if save:
            self.save_vector_store()
            
    def save_vector_store(self) -> None:
        """Save the FAISS index and metadata to disk."""
        # Ensure vector store directory exists
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        if isinstance(self.index, faiss.GpuIndex):
            index_cpu = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(index_cpu, str(self.vector_store_dir / 'embeddings.faiss'))
        else:
            faiss.write_index(self.index, str(self.vector_store_dir / 'embeddings.faiss'))
            
        # Save metadata
        with open(self.vector_store_dir / 'metadata.pkl', 'wb') as f:
            pickle.dump(self.metadata, f)
            
    def remove_document(self, doc_id: str, save: bool = True) -> None:
        """Remove all chunks belonging to a specific document.
        
        Args:
            doc_id: ID of document to remove
            save: Whether to save the updated index to disk
        """
        if not self.metadata:
            return
            
        # Find indices to keep (those not matching doc_id)
        keep_indices = [i for i, meta in enumerate(self.metadata) 
                       if meta.get('doc_id') != doc_id]
        
        if len(keep_indices) == len(self.metadata):
            return  # Nothing to remove
            
        # Create new index with kept vectors
        dimension = self.index.d
        new_index = faiss.IndexFlatL2(dimension)
        
        if keep_indices:  # If there are vectors to keep
            # Get vectors to keep
            all_vectors = faiss.vector_to_array(self.index.reconstruct_n(0, self.index.ntotal))
            all_vectors = all_vectors.reshape(self.index.ntotal, dimension)
            kept_vectors = all_vectors[keep_indices]
            
            # Add kept vectors to new index
            new_index.add(kept_vectors)
            
        # Update index and metadata
        self.index = new_index
        self.metadata = [self.metadata[i] for i in keep_indices]
        
        if save:
            self.save_vector_store()

    def clear_vector_store(self) -> None:
        """Clear all vectors and metadata from the store."""
        dimension = self.index.d
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        self.save_vector_store()
    
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
        response = re.sub(r'^[^.?!]\?\s', '', response)
        
        # Clean up whitespace
        response = re.sub(r'\s+', ' ', response)
        response = response.strip()
        
        return response

# API-friendly functions for Django views
def get_document_answer(query: str, vector_store_dir: str, user_id: str, doc_id: str = None, max_length: int = 256) -> Dict:
    """Get answer for a specific document or across all documents for a user.
    
    Args:
        query (str): User's question
        user_id (str): ID of the user making the query
        doc_id (str, optional): Specific document ID to query. If None, queries all user's documents
        max_length (int): Maximum length of generated response
        
    Returns:
        Dict: Response containing answer, confidence and source information
    """
    try:
        # Initialize retriever with user_id and optional document filter
        retriever = TextRetriever(user_id=user_id, doc_id=doc_id, vector_store_dir=vector_store_dir)
        
        # Verify index has content
        if retriever.index.ntotal == 0:
            return {
                'status': 'error',
                'answer': None,
                'confidence': 0.0,
                'doc_id': doc_id,
                'error': 'No documents found in vector store'
            }
            
        # Get response using RAG
        try:
            response = retriever.generate_response(query, max_length=max_length)
        except AttributeError as e:
            # Handle case where document chunk attributes can't be accessed
            print(f"Error accessing document attributes: {str(e)}")
            return {
                'status': 'error',
                'answer': None,
                'confidence': 0.0,
                'doc_id': doc_id,
                'error': 'Error accessing document content'
            }
        
        # Parse confidence from response
        confidence_match = re.search(r'Confidence: ([\d.]+)', response)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
        
        # Clean up the response text
        answer = re.sub(r'Answer \(Confidence: [\d.]+\):', '', response).strip()
        
        return {
            'status': 'success',
            'answer': answer,
            'confidence': confidence,
            'doc_id': doc_id,
            'error': None
        }
        
    except Exception as e:
        print(f"Error in get_document_answer: {str(e)}")
        return {
            'status': 'error',
            'answer': None,
            'confidence': 0.0,
            'doc_id': doc_id,
            'error': str(e)
        }