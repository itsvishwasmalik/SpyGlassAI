import fitz
from tqdm.auto import tqdm
import re
from spacy.lang.en import English, Language
import numpy as np
from pathlib import Path
import faiss
import pickle
import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer

# Configure Django settings if running as standalone script
if __name__ == "__main__":
    import django
    import os
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spyglass.settings')
    django.setup()

from django.conf import settings

@Language.component("custom_sentencizer")
def custom_sentencizer(doc):
    """Custom sentence segmentation component for spaCy."""
    # Use existing sentence boundaries
    for sent in doc.sents:
        # Don't change sentence boundaries
        pass
    return doc

class TextChunker:
    def __init__(self, context_length=384, chars_per_token=4, buffer_factor=0.8):
        """Initialize the TextChunker with configurable parameters."""
        self.context_length = context_length
        self.chars_per_token = chars_per_token
        self.buffer_factor = buffer_factor
        self.max_tokens = context_length * buffer_factor
        
        self.chunks = []
        self.sentences = []
        self.sentence_token_lengths = []
    
    def estimate_tokens(self, text: str) -> float:
        """Estimate the number of tokens in a text."""
        return len(text) / self.chars_per_token
    
    def chunk_by_tokens(self, sentences: List[str]) -> List[List[str]]:
        """Create chunks that fit within token limit."""
        self.sentences = sentences
        self.sentence_token_lengths = [self.estimate_tokens(s) for s in sentences]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence, tokens in zip(sentences, self.sentence_token_lengths):
            if current_tokens + tokens > self.max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(sentence)
            current_tokens += tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        self.chunks = chunks
        return chunks

@dataclass
class DocumentChunk:
    page_number: int
    text: str
    char_count: int
    word_count: int
    token_count: float

class DocumentProcessor:
    def __init__(self, model_name: str = "all-mpnet-base-v2", vector_store_dir: str = 'vector_store'):
        self.embedding_model = SentenceTransformer(model_name_or_path=model_name, device="cpu")
        # self.embedding_model = settings.embedding_model
        self.vector_store_dir = Path(vector_store_dir)
        self.vector_store_dir.mkdir(exist_ok=True)
        self.chunker = TextChunker()
        
        # Initialize spaCy with custom sentence segmentation
        self.nlp = English()
        self.nlp.add_pipe("sentencizer")
        
        # Only add custom sentencizer if not already present
        if "custom_sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("custom_sentencizer")
    
    def get_document_store_path(self, doc_id: str) -> Path:
        """Get the path for document-specific vector store."""
        print("doc_id ======> ", doc_id)
        doc_store = self.vector_store_dir / str(doc_id)
        doc_store.mkdir(parents=True, exist_ok=True)
        return doc_store

    def process_document(self, pdf_path: str, doc_id: str) -> bool:
        """Process a PDF document and store its embeddings."""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
            print("doc_id process_document ======> ", doc_id)
            # Get document-specific directory
            doc_store = self.get_document_store_path(doc_id)
            
            # Process document
            pages_and_chunks = self._extract_and_chunk_text(pdf_path)
            if not pages_and_chunks:
                raise ValueError("No text could be extracted from the document")
            
            # Create and store embeddings
            embeddings = []
            for chunk in tqdm(pages_and_chunks, desc="Creating embeddings"):
                embedding = self.embedding_model.encode(chunk.text)
                embeddings.append(embedding)
            
            # Convert to numpy array and create FAISS index
            embeddings_array = np.array(embeddings).astype('float32')
            dimension = embeddings_array.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings_array)
            
            # Save FAISS index and metadata
            index_path = str(doc_store / 'embeddings.faiss')
            metadata_path = str(doc_store / 'metadata.pkl')
            
            faiss.write_index(index, index_path)
            with open(metadata_path, 'wb') as f:
                pickle.dump(pages_and_chunks, f)
            
            print(f"Successfully processed document. Stored at: {doc_store}")
            return True
            
        except Exception as e:
            print(f"Error processing document: {e}")
            return False

    def query_document(self, doc_id: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Query a specific document's embeddings for relevant chunks."""
        try:
            doc_store = self.get_document_store_path(doc_id)
            index_path = doc_store / 'embeddings.faiss'
            metadata_path = doc_store / 'metadata.pkl'
            
            # Check if document exists
            if not (index_path.exists() and metadata_path.exists()):
                raise FileNotFoundError(f"Document {doc_id} not found in vector store")
            
            # Load index and metadata
            index = faiss.read_index(str(index_path))
            with open(metadata_path, 'rb') as f:
                chunks = pickle.load(f)
            
            # Encode query and search
            query_vector = self.embedding_model.encode(query)
            D, I = index.search(query_vector.reshape(1, -1).astype('float32'), k)
            
            # Format results
            results = []
            for idx, (distance, chunk_idx) in enumerate(zip(D[0], I[0])):
                if chunk_idx >= 0 and chunk_idx < len(chunks):  # Ensure valid index
                    chunk = chunks[chunk_idx]
                    results.append({
                        'chunk_index': idx,
                        'page_number': chunk.page_number,
                        'text': chunk.text,
                        'relevance_score': float(1 / (1 + distance))
                    })
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results
            
        except FileNotFoundError as e:
            print(f"Document not found: {e}")
            return []
        except Exception as e:
            print(f"Error querying document: {e}")
            return []

    def _extract_and_chunk_text(self, pdf_path: str) -> List[DocumentChunk]:
        """Extract and chunk text from PDF."""
        pages_and_texts = self._open_and_read_pdf(pdf_path)
        all_chunks = []
        
        for page in pages_and_texts:
            sentences = self._split_into_sentences(page['text'])
            chunks = self.chunker.chunk_by_tokens(sentences)
            
            for chunk in chunks:
                text = " ".join(chunk).strip()
                chunk_obj = DocumentChunk(
                    page_number=page['page_number'],
                    text=text,
                    char_count=len(text),
                    word_count=len(text.split()),
                    token_count=self.chunker.estimate_tokens(text)
                )
                all_chunks.append(chunk_obj)
        
        return all_chunks

    def _open_and_read_pdf(self, pdf_path: str) -> List[Dict]:
        """Opens and reads PDF content."""
        doc = fitz.open(pdf_path)
        pages_and_texts = []
        
        for page_number, page in enumerate(doc):
            text = page.get_text()
            text = self._text_formatter(text)
            pages_and_texts.append({
                "page_number": page_number,
                "text": text
            })
            
        return pages_and_texts

    def _text_formatter(self, text: str) -> str:
        """Format and clean text."""
        cleaned_text = text.replace("\n", " ").strip()
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        return cleaned_text

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        doc = self.nlp(text)
        sentences = []
        current_sentence = []
        MIN_SENTENCE_LENGTH = 25
        
        for sent in doc.sents:
            sentence = str(sent).strip()
            
            if not any(c.isalpha() for c in sentence):
                continue
                
            if len(sentence) < MIN_SENTENCE_LENGTH:
                if current_sentence:
                    current_sentence.append(sentence)
                else:
                    current_sentence = [sentence]
            else:
                if current_sentence:
                    combined = ' '.join(current_sentence)
                    if len(combined) >= MIN_SENTENCE_LENGTH:
                        sentences.append(combined)
                    current_sentence = []
                sentences.append(sentence)
        
        return sentences


def process_new_document(user_path: str, pdf_path: str, doc_id: str) -> bool:
    """
    Process a new PDF document and store its embeddings.
    
    Args:
        pdf_path (str): Path to the PDF file
        doc_id (str): Unique identifier for the document
        
    Returns:
        bool: True if processing was successful
    """
    try:
        vector_store_dir = os.path.join(user_path, "vector_store")
        processor = DocumentProcessor(vector_store_dir=vector_store_dir)
        print("doc_id process_neew_document ======> ", doc_id)
        return processor.process_document(pdf_path, doc_id)
    except Exception as e:
        print(f"Error processing new document: {e}")
        return False
    
if __name__ == "__main__":
    # Check if BASE_DIR is set correctly
    print("BASE_DIR ======> ", settings.BASE_DIR)
    
    # Example usage
    pdf_path = os.path.join(settings.BASE_DIR, "Data", "research_paper", "10.1007@s12540-020-00809-3.pdf")
    doc_id = "10.1007@s12540-020-00809-3"
    
    if os.path.exists(pdf_path):
        success = process_new_document(pdf_path=pdf_path, doc_id=doc_id)
        if success:
            print(f"Successfully processed document: {doc_id}")
        else:
            print(f"Failed to process document: {doc_id}")
    else:
        print(f"PDF file not found at: {pdf_path}")