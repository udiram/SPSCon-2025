from utils.tag_generator import find_similar_posters

def get_similar_posters(poster, all_posters, limit=5):
    """Wrapper function to get similar posters"""
    return find_similar_posters(poster, all_posters, limit)

