type Props = {
  concepts: string[];
  onSelect: (concept: string) => void;
};

function ConceptExplorer({ concepts, onSelect }: Props) {
  if (!concepts.length) return null;
  return (
    <section className="concept-explorer" aria-label="Related concepts">
      <h2>Concepts in these results</h2>
      <div className="concept-list">
        {concepts.map((concept) => (
          <button
            aria-label={`Explore concept: ${concept}`}
            className="concept-chip"
            key={concept}
            onClick={() => onSelect(concept)}
            type="button"
          >
            {concept}
          </button>
        ))}
      </div>
    </section>
  );
}

export default ConceptExplorer;