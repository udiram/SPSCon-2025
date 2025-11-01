import json
import re
from collections import Counter
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Physics subfield taxonomy for validation
PHYSICS_SUBFIELDS = {
    'medical physics', 'radiation therapy', 'radiotherapy', 'oncology', 'radiology',
    'quantum physics', 'quantum computing', 'quantum mechanics', 'quantum information',
    'particle physics', 'high energy physics', 'experimental particle physics',
    'astrophysics', 'cosmology', 'astronomy', 'stellar physics',
    'condensed matter physics', 'solid state physics', 'materials science',
    'nuclear physics', 'nuclear engineering',
    'optics', 'photonics', 'laser physics', 'optical physics',
    'computational physics', 'simulation', 'numerical methods',
    'plasma physics', 'fusion',
    'biophysics', 'biological physics',
    'engineering physics', 'applied physics',
    'theoretical physics', 'mathematical physics',
    'atomic physics', 'molecular physics',
    'geophysics', 'atmospheric physics',
    'statistical mechanics', 'thermodynamics',
    'experimental physics', 'instrumentation'
}

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

def generate_tags_for_poster(poster, use_llm=True):
    """
    Generate comprehensive tags for a poster using LLM-based smart tagging.
    Falls back to rule-based approach if LLM fails.
    """
    tags = set()
    
    # Try LLM-based tagging first
    if use_llm:
        try:
            from utils.groq_client import GroqClient
            groq = GroqClient()
            smart_tags = groq.generate_smart_tags(poster.title)
            
            if smart_tags:
                # Validate tags against physics taxonomy
                validated_tags = []
                for tag in smart_tags:
                    tag_lower = tag.lower().strip()
                    # Accept if it matches known subfields or is a reasonable physics term
                    if tag_lower in PHYSICS_SUBFIELDS or len(tag_lower.split()) <= 3:
                        validated_tags.append(tag_lower)
                
                if validated_tags:
                    tags.update(validated_tags[:10])  # Keep top 10 LLM tags
        except Exception as e:
            print(f"LLM tagging failed for poster {poster.id}: {e}")
    
    # Add metadata tags (institution, author, category, session)
    # These are always included regardless of LLM success
    
    # Add institution (shortened for clarity)
    institution = poster.institution.lower().strip()
    # Try to extract just the main institution name
    if 'university' in institution:
        # Extract university name
        inst_parts = institution.split('university')
        if inst_parts[0]:
            short_inst = inst_parts[0].strip() + ' university'
            tags.add(short_inst)
    elif institution:
        tags.add(institution)
    
    # Add author name (for searchability)
    full_name = f"{poster.first_name.lower()} {poster.last_name.lower()}"
    tags.add(full_name)
    
    # Add category
    tags.add(poster.get_category_name().lower())
    
    # Add session info
    tags.add(f"session {poster.session}")
    
    # If LLM didn't provide enough tags, supplement with keyword extraction
    if len(tags) < 8:
        keywords = extract_keywords_from_title(poster.title)
        tags.update(keywords[:5])
    
    # Return as list, limit to 15 total
    return list(tags)[:15]

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
