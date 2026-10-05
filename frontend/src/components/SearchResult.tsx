import type { SearchResult as SearchResultData } from "../services/searchService";

type SearchResultProps = {
  result: SearchResultData;
  position: number;
  onResearch: (query: string) => void;
  onInspectEvidence: (query: string) => void;
  onOpenSource: (url: string | null | undefined) => void;
};

function SearchResult({ result, position, onResearch, onInspectEvidence, onOpenSource }: SearchResultProps) {
  const isPublic = result.source_type === "public_web";
  const domain = isPublic ? result.domain ?? result.source : result.source;

  return (
    <article className="search-result">
      <div className="result-heading">
        <div className="result-header-copy">
          <span className="result-number">#{position}</span>
          <h2>{result.title}</h2>
        </div>
        <span className="result-score">Relevance {result.score.toFixed(2)}</span>
      </div>

      <div className="result-badges">
        <span className={isPublic ? "source-badge public" : "source-badge private"}>
          {isPublic ? "WEB PUBLIC" : "LOCK PRIVATE"}
        </span>
        <span className="meta-badge">{isPublic ? "domain" : "source"}</span>
        <span className="meta-text">{domain}</span>
      </div>

      <p>{result.snippet}</p>

      <div className="result-actions">
        {result.url && (
          <button className="result-action" onClick={() => onOpenSource(result.url)} type="button">
            Open source
          </button>
        )}
        <button className="result-action" onClick={() => onInspectEvidence(result.title)} type="button">
          Inspect evidence
        </button>
        <button className="result-action" onClick={() => onResearch(result.title)} type="button">
          Research this result
        </button>
      </div>
    </article>
  );
}

export default SearchResult;