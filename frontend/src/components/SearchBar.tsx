import type { RefObject } from "react";

type SearchBarProps = {
  query: string;
  isLoading: boolean;
  inputRef: RefObject<HTMLInputElement | null>;
  scope: "private" | "web" | "all";
  retrievalMode: "keyword" | "semantic" | "hybrid";
  rerankEnabled: boolean;
  onQueryChange: (query: string) => void;
  onScopeChange: (scope: "private" | "web" | "all") => void;
  onRetrievalModeChange: (mode: "keyword" | "semantic" | "hybrid") => void;
  onRerankChange: (enabled: boolean) => void;
  onClear: () => void;
  onSubmit: () => void;
  onResearch: () => void;
};

function SearchBar({ query, isLoading, inputRef, scope, retrievalMode, rerankEnabled, onQueryChange, onScopeChange, onRetrievalModeChange, onRerankChange, onClear, onSubmit, onResearch }: SearchBarProps) {
  return (
    <form
      className="search-bar"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="search-bar-label-row">
        <label htmlFor="search-query">Ask NEXUS</label>
        <kbd>⌘ K</kbd>
      </div>
      <div className="search-controls premium-search-controls">
        <input
          id="search-query"
          ref={inputRef}
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search private vault, public web, or both..."
          type="search"
          aria-label="Search input"
        />
        {query && (
          <button aria-label="Clear search" className="clear-button" onClick={onClear} type="button">
            ×
          </button>
        )}
        <button aria-label="Run search" className="search-submit" disabled={isLoading} type="submit">
          {isLoading ? "..." : "↵"}
        </button>
      </div>

      <div className="search-options">
        <div className="control-group">
          <span className="control-label">SOURCE</span>
          {(["private", "web", "all"] as const).map((option) => (
            <button
              aria-pressed={scope === option}
              className={scope === option ? "selector active" : "selector"}
              key={option}
              onClick={() => onScopeChange(option)}
              type="button"
            >
              {option === "private" ? "Private" : option === "web" ? "Web" : "All"}
            </button>
          ))}
        </div>

        <div className="control-group retrieval-group">
          <span className="control-label">RETRIEVAL</span>
          {(["keyword", "semantic", "hybrid"] as const).map((option) => (
            <button
              aria-pressed={retrievalMode === option}
              className={retrievalMode === option ? "selector active" : "selector"}
              key={option}
              onClick={() => onRetrievalModeChange(option)}
              type="button"
            >
              {option}
            </button>
          ))}
          <button
            aria-pressed={rerankEnabled}
            className={rerankEnabled ? "rerank-toggle active" : "rerank-toggle"}
            onClick={() => onRerankChange(!rerankEnabled)}
            type="button"
          >
            {rerankEnabled ? "Rerank on" : "Rerank off"}
          </button>
        </div>
      </div>

      <div className="bar-actions">
        <button className="action-button compact primary" disabled={isLoading} onClick={onSubmit} type="button">
          Search
        </button>
        <button className="action-button compact" disabled={isLoading} onClick={onResearch} type="button">
          Research
        </button>
      </div>
    </form>
  );
}

export default SearchBar;