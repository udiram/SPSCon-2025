import json
import re
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter
from datetime import datetime, timedelta

from models import db, User, Poster, Favorite, Visit, UserProfile, UserQuery
from utils.groq_client import GroqClient, hash_query
from utils.similarity import get_similar_posters


# Semantic domain knowledge for physics subfields
SEMANTIC_EXPANSIONS = {
    "medical physics": ["radiotherapy", "radiation therapy", "stereotactic", "oncology", "radiation oncology", 
                        "medical imaging", "radiology", "dosimetry", "treatment planning", "radiosurgery",
                        "radiation dose", "cancer treatment", "proton therapy", "brachytherapy", "ethos"],
    "quantum": ["quantum computing", "quantum information", "quantum mechanics", "quantum entanglement", 
                "quantum optics", "qbit", "superposition"],
    "particle physics": ["hep", "high energy", "collider", "lhc", "cern", "detector", "experimental particle"],
    "condensed matter": ["solid state", "material science", "semiconductor", "superconductor"],
    "astrophysics": ["astronomy", "cosmology", "galaxy", "star", "planet", "exoplanet"],
    "optics": ["laser", "photonics", "optical", "interferometry"],
    "computational": ["simulation", "modeling", "algorithm", "machine learning", "artificial intelligence"],
    "nuclear": ["nuclear physics", "reactor", "fission", "fusion"]
}

# Expand semantic terms
def expand_semantic_terms(terms: List[str]) -> set:
    """Expand terms with semantic domain knowledge"""
    expanded = set()
    for term in terms:
        term_lower = term.lower()
        expanded.add(term_lower)
        # Check if this term matches any semantic domain
        for domain, related_terms in SEMANTIC_EXPANSIONS.items():
            if domain in term_lower:
                expanded.update(related_terms)
            # Also check reverse - if related term matches, add domain
            for related in related_terms:
                if related in term_lower:
                    expanded.add(domain)
                    expanded.update(related_terms)
    return expanded


def extract_physics_terms(text: str) -> set:
    """Extract meaningful physics-related terms from text"""
    if not text:
        return set()
    
    text_lower = text.lower()
    
    # Extract multi-word physics terms
    physics_terms = set()
    
    # Common physics patterns
    patterns = [
        r'\b(medical physics|quantum computing|particle physics|condensed matter|astrophysics)\b',
        r'\b(radiotherapy|radiation therapy|stereotactic|oncology|radiosurgery)\b',
        r'\b(quantum|quantum information|quantum optics)\b',
        r'\b(experimental|computational|theoretical)\b',
        r'\b(laser|photonics|optics|interferometry)\b',
        r'\b(simulation|modeling|algorithm|machine learning)\b',
        r'\b(superconductor|semiconductor|material science)\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        physics_terms.update(matches)
    
    # Extract meaningful words (length > 4, not common stop words)
    stop_words = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'their', 'would', 'could', 'should',
                  'using', 'based', 'study', 'analysis', 'investigation', 'research', 'development', 'design'}
    
    words = re.findall(r'\b[a-z]{5,}\b', text_lower)
    physics_terms.update(w for w in words if w not in stop_words)
    
    return physics_terms


class ProfileBuilder:
    """Builds and maintains user profiles from interactions"""
    
    def __init__(self, user: User):
        self.user = user
    
    def build_profile(self) -> Dict[str, Any]:
        """Build comprehensive user profile from all available data"""
        profile = {
            "interests": [],
            "categories": [],
            "institutions": [],
            "sessions": [],
            "experience_level": None,
            "favorite_count": 0,
            "visit_count": 0,
            "top_tags": [],
            "semantic_terms": set(),  # New: semantic concept terms
            "poster_interactions": []
        }
        
        # Get favorites
        favorites = Favorite.query.filter_by(user_id=self.user.id).all()
        favorite_posters = [fav.poster for fav in favorites if fav.poster]
        profile["favorite_count"] = len(favorite_posters)
        
        # Get visits
        visits = Visit.query.filter_by(user_id=self.user.id).all()
        visited_posters = [visit.poster for visit in visits if visit.poster]
        profile["visit_count"] = len(visited_posters)
        
        # Aggregate from poster interactions
        all_interacted_posters = list(set(favorite_posters + visited_posters))
        
        if all_interacted_posters:
            # Extract categories
            categories = [p.get_category_name() for p in all_interacted_posters]
            profile["categories"] = list(set(categories))
            
            # Extract institutions
            institutions = [p.institution for p in all_interacted_posters]
            profile["institutions"] = list(set(institutions))
            
            # Extract sessions
            sessions = [p.session for p in all_interacted_posters]
            profile["sessions"] = list(set(sessions))
            
            # Extract tags
            all_tags = []
            for poster in all_interacted_posters:
                if poster.tags:
                    try:
                        tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
                        all_tags.extend(tags)
                    except:
                        pass
            
            # Get top tags
            tag_counts = Counter(all_tags)
            profile["top_tags"] = [tag for tag, _ in tag_counts.most_common(10)]
            
            # Extract semantic terms from titles and tags
            semantic_terms = set()
            for poster in all_interacted_posters:
                semantic_terms.update(extract_physics_terms(poster.title))
                if poster.tags:
                    try:
                        tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
                        for tag in tags:
                            semantic_terms.update(extract_physics_terms(str(tag)))
                    except:
                        pass
            
            # Expand semantic terms
            profile["semantic_terms"] = expand_semantic_terms(list(semantic_terms))
            
            # Store poster interaction details
            profile["poster_interactions"] = [
                {
                    "id": p.id,
                    "title": p.title,
                    "category": p.get_category_name(),
                    "institution": p.institution,
                    "session": p.session,
                    "tags": json.loads(p.tags) if p.tags and isinstance(p.tags, str) else []
                }
                for p in all_interacted_posters
            ]
        
        return profile
    
    def update_profile_from_query(self, query_text: str, groq_client: GroqClient) -> Dict[str, Any]:
        """Update profile with insights from a natural language query"""
        # Get existing profile
        existing_profile = self.build_profile()
        
        # Extract semantic terms from query immediately
        query_semantic_terms = extract_physics_terms(query_text)
        expanded_query_terms = expand_semantic_terms(list(query_semantic_terms))
        
        # Build history context
        history = {
            "favorites": existing_profile.get("poster_interactions", [])[:10],
            "categories": existing_profile.get("categories", []),
            "top_tags": existing_profile.get("top_tags", []),
            "semantic_terms": list(existing_profile.get("semantic_terms", set()))
        }
        
        # Extract preferences using Groq
        extracted = groq_client.extract_user_preferences(query_text, history)
        
        # Merge with existing profile
        profile = existing_profile.copy()
        
        # Merge interests
        if "interests" in extracted:
            existing_interests = set(profile.get("interests", []))
            new_interests = set(extracted["interests"])
            profile["interests"] = list(existing_interests.union(new_interests))
        
        # Merge categories
        if "categories" in extracted:
            existing_categories = set(profile.get("categories", []))
            new_categories = set(extracted["categories"])
            profile["categories"] = list(existing_categories.union(new_categories))
        
        # Merge institutions
        if "institutions" in extracted:
            existing_institutions = set(profile.get("institutions", []))
            new_institutions = set(extracted["institutions"])
            profile["institutions"] = list(existing_institutions.union(new_institutions))
        
        # Update experience level if provided
        if "experience_level" in extracted and extracted["experience_level"]:
            profile["experience_level"] = extracted["experience_level"]
        
        # Update session preferences
        if "session_preferences" in extracted:
            existing_sessions = set(profile.get("sessions", []))
            new_sessions = set(extracted["session_preferences"])
            profile["sessions"] = list(existing_sessions.union(new_sessions))
        
        # Merge semantic terms
        existing_semantic = profile.get("semantic_terms", set())
        if isinstance(existing_semantic, list):
            existing_semantic = set(existing_semantic)
        profile["semantic_terms"] = existing_semantic.union(expanded_query_terms)
        
        # Save to database
        self._save_profile(profile)
        
        # Save query
        query_record = UserQuery(
            user_id=self.user.id,
            query_text=query_text,
            extracted_interests=json.dumps(extracted)
        )
        db.session.add(query_record)
        db.session.commit()
        
        return profile
    
    def _save_profile(self, profile: Dict[str, Any]):
        """Save or update user profile in database"""
        user_profile = UserProfile.query.filter_by(user_id=self.user.id).first()
        
        if not user_profile:
            user_profile = UserProfile(user_id=self.user.id)
            db.session.add(user_profile)
        
        # Convert set to list for JSON serialization
        profile_for_db = profile.copy()
        if "semantic_terms" in profile_for_db and isinstance(profile_for_db["semantic_terms"], set):
            profile_for_db["semantic_terms"] = list(profile_for_db["semantic_terms"])
        
        user_profile.preferences_json = json.dumps(profile_for_db)
        user_profile.last_updated = datetime.utcnow()
        
        # Extract research areas from interests and tags
        research_areas = []
        if profile.get("interests"):
            research_areas.extend(profile["interests"])
        if profile.get("top_tags"):
            research_areas.extend(profile["top_tags"][:5])
        if profile.get("semantic_terms"):
            semantic_list = list(profile["semantic_terms"]) if isinstance(profile["semantic_terms"], set) else profile["semantic_terms"]
            research_areas.extend(semantic_list[:10])
        user_profile.research_areas = json.dumps(list(set(research_areas)))
        
        db.session.commit()
    
    def get_or_build_profile(self) -> Dict[str, Any]:
        """Get profile from DB or build from scratch"""
        user_profile = UserProfile.query.filter_by(user_id=self.user.id).first()
        
        if user_profile and user_profile.preferences_json:
            try:
                profile = json.loads(user_profile.preferences_json)
                # Convert semantic_terms back to set if it's a list
                if "semantic_terms" in profile and isinstance(profile["semantic_terms"], list):
                    profile["semantic_terms"] = set(profile["semantic_terms"])
                # Refresh with latest interactions
                fresh_profile = self.build_profile()
                # Merge fresh data
                profile.update(fresh_profile)
                return profile
            except:
                pass
        
        # Build fresh profile
        profile = self.build_profile()
        self._save_profile(profile)
        return profile


class RecommendationGenerator:
    """Generates poster recommendations using hybrid approach"""
    
    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
    
    def generate_poster_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        all_posters: List[Poster],
        limit: int = 20,
        exclude_visited: bool = True,
        exclude_favorited: bool = False
    ) -> List[Dict[str, Any]]:
        """Generate poster recommendations using semantic-aware hybrid scoring"""
        
        # Convert posters to dict format for Groq
        poster_dicts = []
        for poster in all_posters:
            tags = []
            if poster.tags:
                try:
                    tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
                except:
                    tags = []
            
            poster_dicts.append({
                "id": poster.id,
                "title": poster.title,
                "tags": tags,
                "category": poster.get_category_name(),
                "institution": poster.institution,
                "session": poster.session,
                "poster_number": poster.poster_number
            })
        
        # Get LLM suggestions with better prompting
        llm_poster_ids = set()
        llm_reasons = ""
        try:
            llm_suggestions = self.groq_client.suggest_poster_ids(user_profile, poster_dicts)
            llm_poster_ids = set(llm_suggestions.get("poster_ids", []))
            llm_reasons = llm_suggestions.get("reasons", "")
        except Exception as e:
            print(f"Groq API error: {e}")
        
        # Build semantic profile terms
        semantic_terms = user_profile.get("semantic_terms", set())
        if isinstance(semantic_terms, list):
            semantic_terms = set(semantic_terms)
        
        # Also add terms from interests, tags, categories
        profile_terms = set()
        for term in user_profile.get("interests", []):
            profile_terms.update(extract_physics_terms(str(term)))
        for tag in user_profile.get("top_tags", []):
            profile_terms.update(extract_physics_terms(str(tag)))
        for cat in user_profile.get("categories", []):
            profile_terms.update(extract_physics_terms(str(cat)))
        
        # Expand all profile terms semantically
        all_profile_terms = semantic_terms.union(profile_terms)
        expanded_profile_terms = expand_semantic_terms(list(all_profile_terms))
        
        # Interactions to seed related recommendations
        interacted_ids = {p["id"] for p in user_profile.get("poster_interactions", [])}

        # Precompute boosts from favorites/visits
        id_to_tags = {}
        id_to_semantic = {}
        for p in all_posters:
            try:
                tags = json.loads(p.tags) if isinstance(p.tags, str) else (p.tags or [])
                id_to_tags[p.id] = set(tags)
            except:
                id_to_tags[p.id] = set()
            
            # Extract semantic terms from poster
            poster_semantic = extract_physics_terms(p.title)
            if p.tags:
                try:
                    tags = json.loads(p.tags) if isinstance(p.tags, str) else (p.tags or [])
                    for tag in tags:
                        poster_semantic.update(extract_physics_terms(str(tag)))
                except:
                    pass
            id_to_semantic[p.id] = expand_semantic_terms(list(poster_semantic))

        # Build semantic signature of interacted posters
        interacted_semantic = set()
        for pid in interacted_ids:
            interacted_semantic.update(id_to_semantic.get(pid, set()))

        # Score all posters
        recommendations = []
        for poster in all_posters:
            poster_id = poster.id
            
            # Skip if should exclude
            if exclude_visited and poster_id in interacted_ids:
                continue
            
            # 1) Semantic match score (60% weight) - most important
            semantic_score = self._semantic_match_score(
                poster, 
                expanded_profile_terms,
                id_to_semantic.get(poster_id, set())
            )

            # 2) Structured alignment (15% weight)
            align_score = self._calculate_profile_similarity(poster, user_profile)

            # 3) Related-to-favorites boost via semantic overlap (15% weight)
            poster_semantic_set = id_to_semantic.get(poster_id, set())
            semantic_overlap = len(poster_semantic_set & interacted_semantic)
            fav_boost = min(1.0, semantic_overlap / max(1, len(poster_semantic_set) or 1))

            # 4) LLM prior (10% weight) - helpful but not dominant
            llm_score = 1.0 if poster_id in llm_poster_ids else 0.0

            # Weighted sum
            combined_score = (
                0.60 * semantic_score +
                0.15 * align_score +
                0.15 * fav_boost +
                0.10 * llm_score
            )
            
            # Include all recommendations (will be ranked and limited)
            recommendations.append({
                "poster": poster,
                "score": combined_score,
                "llm_recommended": poster_id in llm_poster_ids,
                "reasons": self._generate_reason(poster, user_profile, llm_reasons, expanded_profile_terms)
            })
        
        # Sort by score (most relevant first)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # Always return top N results (ranked from most to least relevant)
        return recommendations[:limit]
    
    def _semantic_match_score(self, poster: Poster, profile_terms: set, poster_semantic: set) -> float:
        """Compute semantic match score between poster and profile"""
        if not profile_terms:
            return 0.0
        
        # Extract semantic terms from poster if not provided
        if not poster_semantic:
            poster_semantic = extract_physics_terms(poster.title)
            if poster.tags:
                try:
                    tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
                    for tag in tags:
                        poster_semantic.update(extract_physics_terms(str(tag)))
                except:
                    pass
            poster_semantic = expand_semantic_terms(list(poster_semantic))
        
        # Calculate overlap
        if not poster_semantic:
            return 0.0
        
        overlap = len(poster_semantic & profile_terms)
        
        # Normalize - reward posters that match many profile terms
        # Use Jaccard similarity for better normalization
        union_size = len(poster_semantic | profile_terms)
        if union_size == 0:
            return 0.0
        
        jaccard = overlap / union_size
        
        # Also boost if there's any overlap at all
        overlap_ratio = overlap / max(1, len(profile_terms))
        
        # Combine Jaccard and overlap ratio
        return min(1.0, (jaccard * 0.6) + (overlap_ratio * 0.4))
    
    def _calculate_profile_similarity(self, poster: Poster, profile: Dict[str, Any]) -> float:
        """Calculate how well a poster matches the user profile"""
        score = 0.0
        
        # Category match
        poster_category = poster.get_category_name()
        if poster_category in profile.get("categories", []):
            score += 0.3
        
        # Institution match
        if poster.institution in profile.get("institutions", []):
            score += 0.2
        
        # Session match
        if poster.session in profile.get("sessions", []):
            score += 0.1
        
        # Tag overlap
        poster_tags = []
        if poster.tags:
            try:
                poster_tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
            except:
                pass
        
        user_tags = set(profile.get("top_tags", []))
        poster_tag_set = set(poster_tags)
        
        if user_tags and poster_tag_set:
            overlap = len(user_tags.intersection(poster_tag_set))
            score += min(0.4, overlap / max(len(user_tags), len(poster_tag_set)))
        
        return min(1.0, score)
    
    def _generate_reason(self, poster: Poster, profile: Dict[str, Any], llm_reasons: str, profile_terms: set) -> str:
        """Generate human-readable reason for recommendation"""
        reasons = []
        
        # Check semantic match
        poster_semantic = expand_semantic_terms(list(extract_physics_terms(poster.title)))
        semantic_overlap = list(poster_semantic & profile_terms)[:3]
        if semantic_overlap:
            reasons.append(f"Matches your interest in: {', '.join(semantic_overlap)}")
        
        if poster.get_category_name() in profile.get("categories", []):
            reasons.append(f"Matches your interest in {poster.get_category_name()} category")
        
        if poster.institution in profile.get("institutions", []):
            reasons.append(f"From {poster.institution}")
        
        poster_tags = []
        if poster.tags:
            try:
                poster_tags = json.loads(poster.tags) if isinstance(poster.tags, str) else poster.tags
            except:
                pass
        
        user_tags = set(profile.get("top_tags", []))
        overlap = set(poster_tags).intersection(user_tags)
        if overlap:
            reasons.append(f"Related tags: {', '.join(list(overlap)[:3])}")
        
        if not reasons:
            return "Recommended based on your preferences"
        
        return "; ".join(reasons[:3])


class UserSimilarityCalculator:
    """Calculates similarity between users for recommendations"""
    
    def calculate_similarities(
        self,
        target_user: User,
        target_profile: Dict[str, Any],
        all_users: List[User],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Calculate similarity scores between target user and all others"""
        similarities = []
        
        # Get target user's interacted posters
        target_favorites = {fav.poster_id for fav in Favorite.query.filter_by(user_id=target_user.id).all()}
        target_visits = {visit.poster_id for visit in Visit.query.filter_by(user_id=target_user.id).all()}
        target_interactions = target_favorites.union(target_visits)
        
        # Get target semantic terms
        target_semantic = target_profile.get("semantic_terms", set())
        if isinstance(target_semantic, list):
            target_semantic = set(target_semantic)
        
        for user in all_users:
            if user.id == target_user.id:
                continue
            
            # Get other user's interactions
            other_favorites = {fav.poster_id for fav in Favorite.query.filter_by(user_id=user.id).all()}
            other_visits = {visit.poster_id for visit in Visit.query.filter_by(user_id=user.id).all()}
            other_interactions = other_favorites.union(other_visits)
            
            # Calculate Jaccard similarity
            if not target_interactions and not other_interactions:
                continue
            
            intersection = len(target_interactions.intersection(other_interactions))
            union = len(target_interactions.union(other_interactions))
            
            if union == 0:
                continue
            
            jaccard_score = intersection / union
            
            # Get profile overlap
            profile_builder = ProfileBuilder(user)
            other_profile = profile_builder.build_profile()
            
            other_semantic = other_profile.get("semantic_terms", set())
            if isinstance(other_semantic, list):
                other_semantic = set(other_semantic)
            
            semantic_overlap = len(target_semantic & other_semantic)
            semantic_score = min(1.0, semantic_overlap / max(1, len(target_semantic | other_semantic)))
            
            category_overlap = len(
                set(target_profile.get("categories", [])).intersection(
                    set(other_profile.get("categories", []))
                )
            )
            tag_overlap = len(
                set(target_profile.get("top_tags", [])).intersection(
                    set(other_profile.get("top_tags", []))
                )
            )
            
            # Combined score
            profile_score = (semantic_score * 0.5) + (category_overlap * 0.3) + (tag_overlap * 0.2)
            combined_score = (jaccard_score * 0.6) + (min(profile_score, 1.0) * 0.4)
            
            if combined_score > 0:
                similarities.append({
                    "user": user,
                    "score": combined_score,
                    "shared_posters": intersection,
                    "categories": list(set(target_profile.get("categories", [])).intersection(
                        set(other_profile.get("categories", []))
                    ))
                })
        
        # Sort by score
        similarities.sort(key=lambda x: x["score"], reverse=True)
        return similarities[:limit]
