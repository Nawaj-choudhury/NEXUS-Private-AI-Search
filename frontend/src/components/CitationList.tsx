import { useState } from "react";

import type { Citation } from "../services/researchService";

function CitationList({ citations }: { citations: Citation[] }) {
  const [selectedCitation, setSelectedCitation] = useState<string | null>(citations[0]?.citation_id ?? null);

  return (
    <section className="citation-panel">
      <h3>Citations</h3>
      <ul className="citation-list">
        {citations.map((citation) => {
          const marker = citation.citation_id.startsWith("S") ? citation.citation_id : `[${citation.citation_id}]`;
          const isSelected = selectedCitation === citation.citation_id;

          return (
            <li key={citation.citation_id}>
              <button className={isSelected ? "citation-trigger active" : "citation-trigger"} onClick={() => setSelectedCitation(citation.citation_id)} type="button">
                <strong>{marker}</strong>
                <span>{citation.title}</span>
              </button>
              {isSelected && (
                <div className="citation-detail">
                  <span className="detail-label">Source</span>
                  <strong>{citation.title}</strong>
                  <small>
                    {citation.source_type === "public_web" ? `Web · ${citation.source ?? "verified public source"}` : `Private · ${citation.source}`}
                  </small>
                  {citation.source_type === "public_web" && citation.url && (
                    <a className="source-link" href={citation.url} rel="noreferrer" target="_blank">
                      Verified URL ↗
                    </a>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default CitationList;