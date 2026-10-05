import type { SearchResult as SearchResultData } from "../services/searchService";
import SearchResult from "./SearchResult";

type Props = {
  results: SearchResultData[];
  onResearch: (query: string) => void;
  onInspectEvidence: (query: string) => void;
  onOpenSource: (url: string | null | undefined) => void;
};

function SearchResults({ results, onResearch, onInspectEvidence, onOpenSource }: Props) {
  return (
    <section aria-live="polite" className="results-list">
      {results.map((result, index) => (
        <SearchResult
          key={`${result.chunk_id}-${index}`}
          onInspectEvidence={onInspectEvidence}
          onOpenSource={onOpenSource}
          onResearch={onResearch}
          position={index + 1}
          result={result}
        />
      ))}
    </section>
  );
}

export default SearchResults;