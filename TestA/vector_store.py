import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
import os
from dotenv import load_dotenv
import hashlib
from collections import Counter
import re

load_dotenv()

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Enhanced vector store implementation for medical records semantic search.
    This implementation demonstrates RAG capabilities with:
    - TF-IDF-like scoring for better relevance
    - Medical term recognition
    - Semantic similarity simulation
    - Metadata filtering and boosting
    """
    
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
        self.document_frequencies = Counter()
        self.total_documents = 0
        
        # Medical terms for enhanced relevance
        self.medical_terms = {
            'symptoms': ['headache', 'fever', 'pain', 'nausea', 'fatigue', 'cough', 
                         'shortness of breath', 'dizziness', 'vomiting', 'rash'],
            'conditions': ['hypertension', 'diabetes', 'asthma', 'pneumonia', 
                          'migraine', 'anxiety', 'depression', 'arthritis'],
            'treatments': ['medication', 'therapy', 'surgery', 'rest', 'hydration',
                          'antibiotics', 'physical therapy', 'counseling'],
            'medications': ['ibuprofen', 'acetaminophen', 'amoxicillin', 'insulin',
                           'albuterol', 'metformin', 'lisinopril', 'aspirin']
        }
        
        # Build medical vocabulary
        self.medical_vocabulary = set()
        for category, terms in self.medical_terms.items():
            self.medical_vocabulary.update(terms)
        
        logger.info("Initialized enhanced vector store with medical terminology")
        
    def initialize(self):
        """Initialize the vector store collection"""
        # In production, this would connect to ChromaDB or similar
        logger.info("Vector store initialized successfully")
    
    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Add a document to the vector store with enhanced processing"""
        try:
            # Process and store document
            processed_text = self._preprocess_text(text)
            self.documents[doc_id] = {
                'text': text,
                'processed_text': processed_text,
                'metadata': metadata,
                'terms': self._extract_terms(processed_text)
            }
            
            # Update document frequencies for TF-IDF
            self._update_document_frequencies(self.documents[doc_id]['terms'])
            self.total_documents += 1
            
            # Generate enhanced embedding
            self.embeddings[doc_id] = self._generate_embedding(processed_text, metadata)
            
            logger.info(f"Added document {doc_id} to vector store with {len(self.documents[doc_id]['terms'])} terms")
            return True
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            return False
    
    def search(self, query_text: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform enhanced semantic search on medical records with:
        - TF-IDF scoring
        - Medical term boosting
        - Semantic similarity simulation
        - Metadata-based filtering
        """
        try:
            # Process query
            processed_query = self._preprocess_text(query_text)
            query_terms = self._extract_terms(processed_query)
            query_embedding = self._generate_query_embedding(processed_query)
            
            results = []
            
            for doc_id, doc in self.documents.items():
                # Apply filters if provided
                if filters and not self._matches_filters(doc['metadata'], filters):
                    continue
                
                # Calculate multi-factor relevance score
                scores = {
                    'tfidf': self._calculate_tfidf_score(query_terms, doc['terms']),
                    'medical': self._calculate_medical_relevance(query_terms, doc['terms']),
                    'semantic': self._calculate_semantic_similarity(query_embedding, self.embeddings[doc_id]),
                    'metadata': self._calculate_metadata_boost(query_text, doc['metadata'])
                }
                
                # Weighted combination of scores
                final_score = (
                    scores['tfidf'] * 0.4 +
                    scores['medical'] * 0.3 +
                    scores['semantic'] * 0.2 +
                    scores['metadata'] * 0.1
                )
                
                if final_score > 0:
                    results.append({
                        'id': doc_id,
                        'score': final_score,
                        'document': doc['text'],
                        'metadata': doc['metadata'],
                        'score_breakdown': scores  # For debugging/analysis
                    })
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # Log search metrics
            logger.info(f"Search query: '{query_text}' returned {len(results)} results")
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better search quality"""
        # Convert to lowercase and remove extra whitespace
        text = ' '.join(text.lower().split())
        # Remove punctuation but keep medical-relevant characters
        text = re.sub(r'[^\w\s\-/]', ' ', text)
        return text
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text"""
        # Split into words
        words = text.split()
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        terms = [w for w in words if w not in stop_words and len(w) > 2]
        return terms
    
    def _update_document_frequencies(self, terms: List[str]):
        """Update document frequency counts for TF-IDF calculation"""
        unique_terms = set(terms)
        for term in unique_terms:
            self.document_frequencies[term] += 1
    
    def _generate_embedding(self, text: str, metadata: Dict[str, Any]) -> np.ndarray:
        """
        Generate document embedding with medical context awareness
        In production, this would use a medical-specific transformer model
        """
        # Simulate embedding generation with multiple features
        features = []
        
        # Text-based features
        features.append(len(text))
        features.append(len(text.split()))
        
        # Medical term density
        medical_count = sum(1 for term in text.split() if term in self.medical_vocabulary)
        features.append(medical_count / max(len(text.split()), 1))
        
        # Record type encoding
        record_types = ['consultation', 'lab_result', 'imaging', 'prescription']
        record_type = metadata.get('record_type', 'other')
        for rt in record_types:
            features.append(1.0 if rt == record_type else 0.0)
        
        # Add some randomness to simulate semantic variation
        features.extend(np.random.rand(10) * 0.1)
        
        return np.array(features)
    
    def _generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for search query"""
        # Similar to document embedding but query-specific
        return self._generate_embedding(query, {'record_type': 'query'})
    
    def update_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Update an existing document in the vector store"""
        try:
            if doc_id in self.documents:
                self.documents[doc_id] = {
                    'text': text,
                    'metadata': metadata
                }
                self.embeddings[doc_id] = self._simple_embedding(text)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating document in vector store: {e}")
            return False
    
    def delete_document(self, doc_id: str):
        """Delete a document from the vector store"""
        try:
            if doc_id in self.documents:
                del self.documents[doc_id]
                del self.embeddings[doc_id]
                logger.info(f"Deleted document {doc_id} from vector store")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document from vector store: {e}")
            return False
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document metadata matches all filters"""
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True
    
    def _calculate_tfidf_score(self, query_terms: List[str], doc_terms: List[str]) -> float:
        """Calculate TF-IDF score between query and document"""
        if not query_terms or not doc_terms:
            return 0.0
        
        score = 0.0
        doc_term_freq = Counter(doc_terms)
        
        for term in query_terms:
            if term in doc_term_freq:
                # Term frequency in document
                tf = doc_term_freq[term] / len(doc_terms)
                
                # Inverse document frequency
                df = self.document_frequencies.get(term, 1)
                idf = np.log((self.total_documents + 1) / (df + 1))
                
                score += tf * idf
        
        # Normalize by query length
        return score / len(query_terms)
    
    def _calculate_medical_relevance(self, query_terms: List[str], doc_terms: List[str]) -> float:
        """Calculate relevance based on medical terminology"""
        medical_query_terms = [t for t in query_terms if t in self.medical_vocabulary]
        medical_doc_terms = [t for t in doc_terms if t in self.medical_vocabulary]
        
        if not medical_query_terms:
            return 0.0
        
        # Count matching medical terms
        matches = sum(1 for term in medical_query_terms if term in medical_doc_terms)
        
        # Boost score for medical term matches
        return matches / len(medical_query_terms)
    
    def _calculate_semantic_similarity(self, query_embedding: np.ndarray, doc_embedding: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        # Cosine similarity
        dot_product = np.dot(query_embedding, doc_embedding)
        norm_product = np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
        
        if norm_product == 0:
            return 0.0
        
        similarity = dot_product / norm_product
        # Normalize to 0-1 range
        return (similarity + 1) / 2
    
    def _calculate_metadata_boost(self, query_text: str, metadata: Dict[str, Any]) -> float:
        """Calculate boost based on metadata relevance"""
        boost = 0.0
        query_lower = query_text.lower()
        
        # Boost for recent records
        if 'visit_date' in metadata:
            # In a real system, calculate recency boost
            boost += 0.1
        
        # Boost for matching record type keywords
        record_type = metadata.get('record_type', '').lower()
        if record_type and record_type in query_lower:
            boost += 0.3
        
        return min(boost, 1.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics for monitoring"""
        return {
            'total_documents': self.total_documents,
            'unique_terms': len(self.document_frequencies),
            'medical_terms_indexed': sum(1 for term in self.document_frequencies if term in self.medical_vocabulary),
            'average_document_length': np.mean([len(doc['terms']) for doc in self.documents.values()]) if self.documents else 0
        }
    
    def is_healthy(self) -> bool:
        """Check if vector store is healthy"""
        try:
            # Basic health checks
            return (
                self.documents is not None and
                self.embeddings is not None and
                len(self.documents) == len(self.embeddings)
            )
        except Exception:
            return False
