import json
import re
from collections import Counter
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

def extract_keywords_from_title(title):
    """Extract meaningful keywords from poster title"""
    # Expanded stop words list
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'this', 
        'that', 'these', 'those', 'from', 'into', 'onto', 'upon', 'about', 'above', 'below', 
        'under', 'over', 'through', 'during', 'before', 'after', 'while', 'since', 'until', 
        'because', 'although', 'though', 'if', 'unless', 'when', 'where', 'why', 'how', 
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 
        'here', 'there', 'when', 'where', 'why', 'how', 'what', 'which', 'who', 'whom', 
        'whose', 'whether', 'study', 'analysis', 'investigation', 'research', 'development', 
        'design', 'implementation', 'evaluation', 'assessment', 'characterization', 
        'optimization', 'simulation', 'modeling', 'detection', 'measurement', 'observation'
    }
    
    # Clean and split title - require longer words
    words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
    
    # Filter out stop words and very common words
    keywords = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Return top 5 most meaningful keywords (reduced from 10)
    return list(dict(Counter(keywords).most_common(5)).keys())

def generate_tags_for_poster(poster):
    """Generate comprehensive tags for a poster"""
    tags = set()
    
    # Add institution name (clean it up)
    institution = poster.institution.lower().strip()
    if institution:
        tags.add(institution)
    
    # Add author names (only full name to avoid duplicates)
    full_name = f"{poster.first_name.lower()} {poster.last_name.lower()}"
    tags.add(full_name)
    
    # Add category
    tags.add(poster.get_category_name().lower())
    
    # Extract keywords from title (limited to most meaningful)
    keywords = extract_keywords_from_title(poster.title)
    tags.update(keywords)
    
    # Add session info
    tags.add(f"session {poster.session}")
    
    # Limit total tags to prevent overwhelming
    return list(tags)[:15]  # Maximum 15 tags per poster

def find_similar_posters(poster, all_posters, limit=5):
    """Find similar posters based on title and tag similarity"""
    if len(all_posters) <= 1:
        return []
    
    # Prepare texts for TF-IDF
    texts = []
    poster_ids = []
    
    for p in all_posters:
        if p.id != poster.id:  # Exclude the current poster
            # Combine title and tags for similarity
            text = f"{p.title} {' '.join(json.loads(p.tags or '[]'))}"
            texts.append(text)
            poster_ids.append(p.id)
    
    if not texts:
        return []
    
    # Add current poster's text
    current_text = f"{poster.title} {' '.join(json.loads(poster.tags or '[]'))}"
    texts.append(current_text)
    
    if not SKLEARN_AVAILABLE:
        # Fallback to simple keyword matching
        current_tags = set(json.loads(poster.tags or '[]'))
        similar_posters = []
        
        for p in all_posters:
            if p.id != poster.id:
                other_tags = set(json.loads(p.tags or '[]'))
                # Calculate simple Jaccard similarity
                intersection = len(current_tags.intersection(other_tags))
                union = len(current_tags.union(other_tags))
                similarity = intersection / union if union > 0 else 0
                
                if similarity > 0.1:
                    similar_posters.append((p, similarity))
        
        # Sort by similarity and return top results
        similar_posters.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in similar_posters[:limit]]
    
    try:
        # Calculate TF-IDF similarity
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Get similarity scores (cosine similarity)
        current_vector = tfidf_matrix[-1]  # Last vector is the current poster
        similarity_scores = np.dot(tfidf_matrix[:-1], current_vector.T).toarray().flatten()
        
        # Get top similar posters
        similar_indices = np.argsort(similarity_scores)[::-1][:limit]
        
        similar_posters = []
        for idx in similar_indices:
            if similarity_scores[idx] > 0.1:  # Only include if similarity > 0.1
                poster_id = poster_ids[idx]
                similar_poster = next((p for p in all_posters if p.id == poster_id), None)
                if similar_poster:
                    similar_posters.append(similar_poster)
        
        return similar_posters
    
    except Exception as e:
        print(f"Error finding similar posters: {e}")
        return []
