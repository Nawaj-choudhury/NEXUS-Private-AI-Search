from .context_builder import ContextItem
from .models import RelatedTopic


def generate_related_topics(items: list[ContextItem], limit: int = 4) -> tuple[RelatedTopic, ...]:
    candidates = [
        ("machine learning", ("S1",)),
        ("artificial intelligence", ("S1",)),
        ("cybersecurity", ("S1",)),
        ("information retrieval", ("S1",)),
        ("search ranking", ("S1",)),
        ("model evaluation", ("S1",)),
    ]
    context = " ".join(item.text.lower() for item in items)
    return tuple(RelatedTopic(topic, citation_ids) for topic, citation_ids in candidates if topic in context)[:limit]