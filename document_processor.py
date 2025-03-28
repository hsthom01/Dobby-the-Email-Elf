import os
from PyPDF2 import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_file(file_path):
    """Extract text from a single file based on its extension."""
    file_extension = os.path.splitext(file_path)[1].lower()
    logger.info(f"Processing file: {file_path}")
    
    try:
        if file_extension == '.pdf':
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                text += extracted or ""
            logger.info(f"Extracted text from PDF (length: {len(text)}): {text[:50]}...")
            return text
        
        elif file_extension == '.docx':
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            logger.info(f"Extracted text from DOCX (length: {len(text)}): {text[:50]}...")
            return text
        
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"Extracted text from TXT (length: {len(text)}): {text[:50]}...")
            return text
        
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return None
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def process_document_folder(folder_path, chunk_size=200):
    """Process all supported files in a folder and return a list of text chunks."""
    supported_extensions = ('.pdf', '.docx', '.txt')
    all_text = ""
    
    logger.info(f"Scanning folder: {folder_path}")
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(supported_extensions):
                file_path = os.path.join(root, file)
                text = extract_text_from_file(file_path)
                if text:
                    all_text += text + " "
                else:
                    logger.warning(f"No text extracted from {file_path}")

    if not all_text:
        logger.warning("No text found in any documents")
        return []

    # Split into chunks of ~chunk_size words
    words = all_text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    logger.info(f"Total chunks created: {len(chunks)} with chunk_size={chunk_size}")
    return chunks

class RAGSystem:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.chunks = []

    def build_index(self, document_chunks):
        """Build FAISS index from document chunks."""
        if not document_chunks:
            logger.warning("No document chunks provided to build index")
            return False
        
        self.chunks = document_chunks
        embeddings = self.model.encode(self.chunks, show_progress_bar=True)
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype(np.float32))
        logger.info(f"Built FAISS index with {len(self.chunks)} chunks")
        return True

    def retrieve_relevant_chunks(self, query, k=3):
        """Retrieve top-k relevant document chunks for a given query."""
        if not self.index or not self.chunks:
            logger.warning("No index or chunks available for retrieval")
            return []
        
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding.astype(np.float32), k)
        return [self.chunks[idx] for idx in indices[0]]