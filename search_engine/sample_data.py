from .models import Document

SAMPLE_DOCUMENTS = [
    Document(
        id="ai-foundations",
        title="Foundations of Artificial Intelligence",
        content="Artificial intelligence combines reasoning, perception, and learning methods to solve tasks that traditionally require human judgment.",
        source="NEXUS knowledge base",
    ),
    Document(
        id="machine-learning",
        title="An Introduction to Machine Learning",
        content="Machine learning systems learn patterns from data and use those patterns to make predictions, classify information, or support decisions.",
        source="NEXUS knowledge base",
    ),
    Document(
        id="cybersecurity-basics",
        title="Cybersecurity and Defensive Engineering",
        content="Cybersecurity protects systems and information through access control, threat detection, secure design, monitoring, and incident response.",
        source="NEXUS knowledge base",
    ),
    Document(
        id="search-engines",
        title="How Search Engines Retrieve Information",
        content="Search engines index documents, retrieve candidates for a query, and rank results using signals that estimate relevance and usefulness.",
        source="NEXUS knowledge base",
    ),
    Document(
        id="large-language-models",
        title="Large Language Models",
        content="Large language models learn statistical patterns in text and generate language by estimating likely continuations from their context.",
        source="NEXUS knowledge base",
    ),
    Document(
        id="information-retrieval",
        title="Information Retrieval Principles",
        content="Information retrieval focuses on finding relevant documents for a user's query through indexing, matching, scoring, and ranking.",
        source="NEXUS knowledge base",
    ),
]