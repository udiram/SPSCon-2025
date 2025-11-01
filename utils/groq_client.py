import os
import json
import hashlib
from typing import Any, Dict, List, Optional

from config import Config


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile") -> None:
        # Lazy import so the app can run without the package installed in some environments
        try:
            from groq import Groq  # type: ignore
            self._Groq = Groq
        except Exception:
            self._Groq = None
        self.api_key = api_key or Config.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.model = model
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            if not self._Groq:
                raise RuntimeError("groq package is not installed. Add it to requirements.txt")
            if not self.api_key:
                raise RuntimeError("GROQ_API_KEY not configured")
            self._client = self._Groq(api_key=self.api_key)

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, json_mode: bool = True) -> str:
        self._ensure_client()
        params = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        # Try JSON mode if supported (llama-3 models support it)
        if json_mode and "llama" in self.model.lower():
            try:
                params["response_format"] = {"type": "json_object"}
            except:
                pass
        
        completion = self._client.chat.completions.create(**params)
        return completion.choices[0].message.content

    @staticmethod
    def _safe_json_loads(text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            return {}

    def extract_user_preferences(self, query_text: str, user_history: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert at understanding physics research interests. Extract structured preferences from the user's natural language query. "
            "Understand semantic relationships: e.g., 'medical physics' includes radiotherapy, radiation therapy, stereotactic radiosurgery, oncology, etc. "
            "Return JSON with keys: interests (string[] - extract key physics subfields/topics), categories (string[]), institutions (string[]), "
            "experience_level (one of: 'beginner'|'intermediate'|'advanced'|'expert'|null), time_constraints (string|null), "
            "session_preferences (number[]), include_reasons (string[]). "
            "Be semantically aware - if someone says 'medical physics', expand to related terms like radiotherapy, radiation therapy, etc."
        )
        history_str = json.dumps(user_history)[:4000]
        user_prompt = (
            f"User query: {query_text}\n\n"
            f"User history (may be sparse): {history_str}\n\n"
            f"Extract interests semantically - expand terms to related concepts in physics."
        )
        content = self._chat(system_prompt, user_prompt)
        return self._safe_json_loads(content)

    def suggest_poster_ids(self, profile: Dict[str, Any], posters: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert at matching physics research posters to user interests. "
            "Understand semantic relationships: 'medical physics' includes radiotherapy, radiation therapy, stereotactic, oncology, etc. "
            "Be semantically aware - match posters based on meaning, not just keywords. "
            "Given a user profile and a list of poster items, select up to 30 poster ids that best match SEMANTICALLY. "
            "Each poster item fields: id, title, tags (string[]), category (string), institution (string), session (number). "
            "Return JSON: { poster_ids: number[], reasons: string }"
        )
        # Include semantic terms in profile for LLM
        profile_for_llm = profile.copy()
        semantic_terms = profile.get("semantic_terms", set())
        if isinstance(semantic_terms, set):
            profile_for_llm["semantic_terms"] = list(semantic_terms)
        
        user_prompt = json.dumps({"profile": profile_for_llm, "posters": posters})[:12000]
        content = self._chat(system_prompt, user_prompt, temperature=0.1)
        return self._safe_json_loads(content)

    def suggest_similar_users(self, profile: Dict[str, Any], users: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = (
            "Given a target user profile and a list of other user profiles, select up to 20 similar user ids. "
            "Return JSON: { user_ids: number[], reasons: string }"
        )
        user_prompt = json.dumps({"target": profile, "users": users})[:12000]
        content = self._chat(system_prompt, user_prompt, temperature=0.1)
        return self._safe_json_loads(content)
    
    def generate_smart_tags(self, title: str, abstract: Optional[str] = None) -> List[str]:
        """
        Generate nuanced, general physics category tags using LLM.
        Returns 8-12 high-quality tags focused on physics subfields.
        """
        system_prompt = (
            "You are an expert physics categorization system. Generate 8-12 nuanced, general physics category tags "
            "for research posters. Focus on broad subfields and methodologies, not overly specific terms.\n\n"
            "Valid categories include (but not limited to):\n"
            "- medical physics, radiation therapy, radiotherapy, oncology\n"
            "- quantum physics, quantum computing, quantum mechanics, quantum information\n"
            "- particle physics, high energy physics, experimental particle physics\n"
            "- astrophysics, cosmology, astronomy, stellar physics\n"
            "- condensed matter physics, solid state physics, materials science\n"
            "- nuclear physics, nuclear engineering\n"
            "- optics, photonics, laser physics, optical physics\n"
            "- computational physics, simulation, numerical methods\n"
            "- plasma physics, fusion\n"
            "- biophysics, biological physics\n"
            "- engineering physics, applied physics\n"
            "- theoretical physics, mathematical physics\n"
            "- atomic physics, molecular physics\n"
            "- geophysics, atmospheric physics\n"
            "- statistical mechanics, thermodynamics\n\n"
            "Return ONLY a JSON object with format: {\"tags\": [\"tag1\", \"tag2\", ...]}\n"
            "Keep tags general and meaningful. Avoid overly specific jargon."
        )
        
        user_prompt = f"Title: {title}"
        if abstract:
            user_prompt += f"\n\nAbstract/Description: {abstract[:500]}"
        
        try:
            content = self._chat(system_prompt, user_prompt, temperature=0.3)
            result = self._safe_json_loads(content)
            tags = result.get("tags", [])
            
            # Validate and limit tags
            if isinstance(tags, list) and len(tags) > 0:
                # Keep 8-12 tags, lowercase and deduplicate
                unique_tags = list(dict.fromkeys([t.lower().strip() for t in tags if isinstance(t, str)]))
                return unique_tags[:12]
            return []
        except Exception as e:
            print(f"Error generating smart tags: {e}")
            return []


def hash_query(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


