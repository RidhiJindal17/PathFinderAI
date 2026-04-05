import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

def get_resources_for_skill(skill: str) -> dict:
    """
    Generate dynamic, search-based learning resources for ANY skill.
    Returns: skill name, estimated time, and a list of links (video, article, docs).
    """
    skill_clean = skill.strip()
    skill_encoded = quote_plus(skill_clean)
    
    return {
        "skill": skill_clean,
        "estimated_time": "2-4 weeks",
        "resources": [
            {
                "title": f"{skill_clean} Full Course (YouTube)",
                "url": f"https://www.youtube.com/results?search_query={skill_encoded}+full+course+free",
                "type": "video"
            },
            {
                "title": f"{skill_clean} FreeCodeCamp Resources",
                "url": f"https://www.google.com/search?q={skill_encoded}+freecodecamp",
                "type": "article"
            },
            {
                "title": f"{skill_clean} Official Documentation",
                "url": f"https://www.google.com/search?q={skill_encoded}+official+documentation",
                "type": "docs"
            }
        ]
    }

def generate_learning_path(missing_skills: list[str]) -> list[dict]:
    """
    Map a list of missing skill names to their dynamic, search-based resource sets.
    """
    results = []
    for skill in missing_skills:
        if not skill or not skill.strip():
            continue
        
        logger.info(f"Generating dynamic resources for skill: '{skill}'")
        res = get_resources_for_skill(skill)
        results.append(res)
            
    return results
