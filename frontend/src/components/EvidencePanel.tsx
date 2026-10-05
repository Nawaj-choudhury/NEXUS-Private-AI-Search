import type { EvidenceItem } from "../services/researchService";

function EvidencePanel({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <section className="evidence-panel">
      <h3>Source evidence</h3>
      <div className="evidence-list">
        {evidence.map((item) => (
          <article className="evidence-item" key={`${item.chunk_id}-${item.citation_id}`}>
            <div className="evidence-header">
              <span className="citation-marker">[{item.citation_id}]</span>
              <strong>{item.title}</strong>
            </div>
            <small className="evidence-source">
              {item.source_type === "public_web" ? `WEB · ${item.url ?? item.source}` : `PRIVATE · ${item.source}`}
            </small>
            <p>{item.excerpt}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default EvidencePanel;