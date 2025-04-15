import fitz
from tqdm.auto import tqdm
import re
from spacy.lang.en import English, Language
import numpy as np
from pathlib import Path
import faiss
import pickle
# Embedding our text chunks
from sentence_transformers import SentenceTransformer
embedding_model = SentenceTransformer(model_name_or_path="all-mpnet-base-v2", device="cpu")



pdf_path = 'kumar2016.pdf'

# Initialize spaCy with custom sentence segmentation rules
nlp = English()

# Custom sentence segmentation rules
@Language.component("custom_sentencizer")
def custom_sentencizer(doc):
    # Patterns that should not break sentences
    non_breaking_patterns = [
        r'[A-Z][a-z]*\.',  # Abbreviations like 'Dr.', 'Mr.'
        r'[A-Z]\.',        # Initials like 'A.', 'B.'
        r'Vol\.',          # Volume
        r'No\.',           # Number
        r'et al\.',        # Citations
        r'vs\.',           # Versus
        r'e\.g\.',         # Latin abbreviations
        r'i\.e\.',
        r'pp\.',           # Pages
        r'\([0-9]{4}\)',   # Years in parentheses
        r'[0-9]+\.',       # Numbered lists
    ]
    
    # Join the patterns
    pattern = '|'.join(non_breaking_patterns)
    
    MIN_SENTENCE_LENGTH = 25  # Minimum characters for a valid sentence
    
    # Find all potential sentence boundaries
    for token in doc[:-1]:
        if token.text.endswith('.'):
            # Check if the period is part of a non-breaking pattern
            span = doc[token.i-2:token.i+1].text if token.i > 1 else token.text
            
            # Get the text from the start of the document to this token
            current_sent = doc[:token.i+1].text.strip()
            
            # Don't break if it's a non-breaking pattern or the sentence is too short
            if not re.search(pattern, span) and len(current_sent) < MIN_SENTENCE_LENGTH:
                token.is_sent_start = False
    
    return doc

# Add the components to the pipeline
nlp.add_pipe("sentencizer")
nlp.add_pipe("custom_sentencizer")

def text_formatter(text: str) -> str:
    cleaned_text = text.replace("\n", " ").strip()
    # Remove multiple spaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text

def split_into_sentences(text: str) -> list[str]:
    # Process the text with spaCy
    doc = nlp(text)
    
    MIN_SENTENCE_LENGTH = 25  # Minimum characters for a valid sentence
    
    # Extract sentences and clean them
    current_sentence = []
    sentences = []
    
    for sent in doc.sents:
        # Clean the sentence
        sentence = str(sent).strip()
        
        # Skip if sentence is just a number or punctuation
        if not any(c.isalpha() for c in sentence):
            continue
            
        # If sentence is too short, add it to the current sentence
        if len(sentence) < MIN_SENTENCE_LENGTH:
            if current_sentence:
                current_sentence.append(sentence)
            else:
                current_sentence = [sentence]
        else:
            # If we have accumulated short sentences, combine them
            if current_sentence:
                combined = ' '.join(current_sentence)
                if len(combined) >= MIN_SENTENCE_LENGTH:
                    sentences.append(combined)
                current_sentence = []
            # Add the current sentence
            sentences.append(sentence)
    
    return sentences

# Open PDF and get lines/pages
def open_and_read_pdf(pdf_path: str) -> list[dict]:
    """
    Opens a PDF file, reads its text content page by page, and collects statistics.

    Parameters:
        pdf_path (str): The file path to the PDF document to be opened and read.

    Returns:
        list[dict]: A list of dictionaries, each containing the page number
        (adjusted), character count, word count, sentence count, token count, and the extracted text
        for each page.
    """
    doc = fitz.open(pdf_path)  # open a document
    pages_and_texts = []
    for page_number, page in tqdm(enumerate(doc)):  # iterate the document pages
        text = page.get_text()  # get plain text encoded as UTF-8
        text = text_formatter(text)
        pages_and_texts.append({"page_number": page_number,  # adjust page numbers since our PDF starts on page 42
                                "page_char_count": len(text),
                                "page_word_count": len(text.split(" ")),
                                "page_sentence_count_raw": len(text.split(". ")),
                                "page_token_count": len(text) / 4,  # 1 token = ~4 chars, see: https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them
                                "text": text})
    return pages_and_texts

pages_and_texts = open_and_read_pdf(pdf_path=pdf_path)

class TextChunker:
    def __init__(self, context_length=384, chars_per_token=4, buffer_factor=0.8):
        """Initialize the TextChunker with configurable parameters.
        
        Args:
            context_length (int): Maximum number of tokens per chunk
            chars_per_token (int): Average number of characters per token
            buffer_factor (float): Safety buffer for token count (0.0 to 1.0)
        """
        self.context_length = context_length
        self.chars_per_token = chars_per_token
        self.buffer_factor = buffer_factor
        self.max_tokens = context_length * buffer_factor
        
        # Statistics
        self.chunks = []
        self.sentences = []
        self.sentence_token_lengths = []
        
    def estimate_tokens(self, text):
        """Estimate the number of tokens in a text."""
        return len(text) / self.chars_per_token
    
    def chunk_by_tokens(self, sentences):
        """Create chunks that fit within token limit."""
        self.sentences = sentences
        self.sentence_token_lengths = [self.estimate_tokens(s) for s in sentences]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence, tokens in zip(sentences, self.sentence_token_lengths):
            # If adding this sentence would exceed the limit, start a new chunk
            if current_tokens + tokens > self.max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            
            # Add the sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += tokens
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        self.chunks = chunks
        return chunks
    
    def get_statistics(self):
        """Get comprehensive statistics about the chunks and sentences."""
        if not self.chunks or not self.sentences:
            return {"error": "No chunks created yet. Call chunk_by_tokens first."}
        
        # Sentence statistics
        avg_tokens_per_sentence = sum(self.sentence_token_lengths) / len(self.sentence_token_lengths)
        max_tokens_per_sentence = max(self.sentence_token_lengths)
        min_tokens_per_sentence = min(self.sentence_token_lengths)
        
        # Chunk statistics
        chunk_sizes = [sum(self.estimate_tokens(s) for s in chunk) for chunk in self.chunks]
        avg_tokens_per_chunk = sum(chunk_sizes) / len(chunk_sizes)
        
        return {
            "sentences": {
                "total": len(self.sentences),
                "avg_tokens": avg_tokens_per_sentence,
                "max_tokens": max_tokens_per_sentence,
                "min_tokens": min_tokens_per_sentence
            },
            "chunks": {
                "total": len(self.chunks),
                "avg_tokens": avg_tokens_per_chunk,
                "max_tokens": max(chunk_sizes),
                "min_tokens": min(chunk_sizes),
                "avg_sentences": sum(len(c) for c in self.chunks) / len(self.chunks)
            },
            "config": {
                "context_length": self.context_length,
                "buffer_factor": self.buffer_factor,
                "effective_max_tokens": self.max_tokens
            }
        }

# Process the PDF and create chunks with page tracking
all_sentences = []
sentence_page_numbers = []  # Track which page each sentence comes from
for page in pages_and_texts:
    sentences = split_into_sentences(page['text'])
    all_sentences.extend(sentences)
    sentence_page_numbers.extend([page['page_number']] * len(sentences))  # Track page number for each sentence

# Create chunker and process text
chunker = TextChunker(context_length=384, chars_per_token=4, buffer_factor=0.8)
chunks = chunker.chunk_by_tokens(all_sentences)
stats = chunker.get_statistics()

# Print analysis
print("\nSentence Analysis:")
print(f"Total sentences: {stats['sentences']['total']}")
print(f"Average tokens per sentence: {stats['sentences']['avg_tokens']:.1f}")
print(f"Maximum tokens per sentence: {stats['sentences']['max_tokens']:.1f}")
print(f"Minimum tokens per sentence: {stats['sentences']['min_tokens']:.1f}")

print("\nChunk Analysis:")
print(f"Total chunks: {stats['chunks']['total']}")
print(f"Average tokens per chunk: {stats['chunks']['avg_tokens']:.1f}")
print(f"Max tokens in any chunk: {stats['chunks']['max_tokens']:.1f}")
print(f"Min tokens in any chunk: {stats['chunks']['min_tokens']:.1f}")
print(f"Average sentences per chunk: {stats['chunks']['avg_sentences']:.1f}")

# Print sample chunks
print("\nSample chunks:")
for i, chunk in enumerate(chunks[:3]):
    chunk_tokens = chunker.estimate_tokens(''.join(chunk))
    print(f"\nChunk {i+1} ({chunk_tokens:.1f} tokens, {len(chunk)} sentences):")
    for j, sentence in enumerate(chunk, 1):
        print(f"{j}. {sentence}")

# Convert chunks into a format suitable for RAG
pages_and_chunks = []
for i, chunk in enumerate(chunks):
    # Get the starting index of this chunk in all_sentences
    chunk_start_idx = sum(len(c) for c in chunks[:i])
    # Get the most common page number for sentences in this chunk
    chunk_page_numbers = sentence_page_numbers[chunk_start_idx:chunk_start_idx + len(chunk)]
    page_number = max(set(chunk_page_numbers), key=chunk_page_numbers.count)  # Most frequent page number
    
    # Join the sentences and clean up
    sentence_chunk = " ".join(chunk).strip()
    sentence_chunk = re.sub(r'\.([A-Z])', r'. \1', sentence_chunk)  # Fix spacing after periods
    
    # Create chunk dictionary in desired format
    chunk_dict = {
        'page_number': page_number,
        'sentence_chunk': sentence_chunk,
        'chunk_char_count': len(sentence_chunk),
        'chunk_word_count': len(sentence_chunk.split()),
        'chunk_token_count': chunker.estimate_tokens(sentence_chunk)
    }
    
    pages_and_chunks.append(chunk_dict)

print(f"\nTotal chunks after processing: {len(pages_and_chunks)}")

# Display all processed chunks
if pages_and_chunks:
    print("\nAll processed chunks:")
    for i, chunk in enumerate(pages_and_chunks, 1):
        print(f"\nChunk {i}:")
        print(f"Page number: {chunk['page_number']}")
        print(f"Token count: {chunk['chunk_token_count']:.1f}")
        print(f"Word count: {chunk['chunk_word_count']}")
        print(f"Char count: {chunk['chunk_char_count']}")
        print("Text:")
        print(chunk['sentence_chunk'])
        print("-" * 80)


# Create embeddings and store in FAISS
print("\nCreating embeddings...")
embeddings = []
for item in tqdm(pages_and_chunks):
    embedding = embedding_model.encode(item["sentence_chunk"])
    embeddings.append(embedding)

# Convert embeddings to numpy array
embeddings_array = np.array(embeddings).astype('float32')

# Create FAISS index
dimension = embeddings_array.shape[1]  # Get embedding dimension
index = faiss.IndexFlatL2(dimension)  # L2 distance index
index.add(embeddings_array)  # Add vectors to the index

# Create output directory if it doesn't exist
output_dir = Path('vector_store')
output_dir.mkdir(exist_ok=True)

# Save the FAISS index
faiss.write_index(index, str(output_dir / 'embeddings.faiss'))

# Save the metadata (everything except embeddings)
metadata = [{
    'page_number': item['page_number'],
    'sentence_chunk': item['sentence_chunk'],
    'chunk_char_count': item['chunk_char_count'],
    'chunk_word_count': item['chunk_word_count'],
    'chunk_token_count': item['chunk_token_count']
} for item in pages_and_chunks]

with open(output_dir / 'metadata.pkl', 'wb') as f:
    pickle.dump(metadata, f)

print(f"\nSaved vector store to: {output_dir}")
print(f"Total vectors: {len(embeddings)}")
print(f"Vector dimension: {dimension}")


# 