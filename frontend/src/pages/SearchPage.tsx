import { useEffect, useRef, useState } from "react";

import { useAuth } from "../auth/AuthContext";
import CitationList from "../components/CitationList";
import ConceptExplorer from "../components/ConceptExplorer";
import EvidencePanel from "../components/EvidencePanel";
import KnowledgeGraph from "../components/KnowledgeGraph";
import RelatedTopics from "../components/RelatedTopics";
import ResearchAnswer from "../components/ResearchAnswer";
import SearchBar from "../components/SearchBar";
import SearchResults from "../components/SearchResults";
import { fetchGraph, type GraphNode, type GraphResponse } from "../services/graphService";
import { researchDocuments, type ResearchResponse } from "../services/researchService";
import { searchDocuments, type SearchMode, type SearchResponse } from "../services/searchService";
import { ApiRequestError } from "../services/api";
import { navigate } from "../routes";

type Scope = "private" | "web" | "all";
type RetrievalMode = "keyword" | "semantic" | "hybrid";

type CommandAction = "focus-search" | "search-private" | "search-web" | "search-all" | "research-query" | "open-discovery" | "toggle-theme";

function SearchPage() {
  const auth = useAuth();
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [researchResponse, setResearchResponse] = useState<ResearchResponse | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null);
  const [scope, setScope] = useState<Scope>(auth.user ? "private" : "web");
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("hybrid");
  const [view, setView] = useState<"search" | "research">("search");
  const [rerankEnabled, setRerankEnabled] = useState(true);
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [error, setError] = useState("");
  const [loginRequired, setLoginRequired] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isGraphLoading, setIsGraphLoading] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [commandValue, setCommandValue] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const storedTheme = window.localStorage.getItem("nexus-theme");
    if (storedTheme === "dark" || storedTheme === "light") setTheme(storedTheme);

    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen(true);
        requestAnimationFrame(() => searchInputRef.current?.focus());
      }
      if (event.key === "Escape") setCommandPaletteOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("nexus-theme", theme);
  }, [theme]);

  function effectiveMode(sourceScope = scope): SearchMode {
    return sourceScope === "all" ? retrievalMode : sourceScope;
  }

  async function handleSearch(nextQuery = query, sourceScope = scope) {
    if (sourceScope !== "web" && !auth.user) {
      setLoginRequired(true);
      setError("");
      setView("search");
      return;
    }
    setLoginRequired(false);
    const normalizedQuery = nextQuery.trim();
    if (!normalizedQuery) {
      setError("Enter a question or concept to begin.");
      searchInputRef.current?.focus();
      return;
    }
    setQuery(normalizedQuery);
    setIsLoading(true);
    setError("");
    setResearchResponse(null);
    setView("search");
    try {
      setResponse(await searchDocuments(normalizedQuery, effectiveMode(sourceScope), rerankEnabled && retrievalMode === "hybrid"));
    } catch (searchError) {
      setResponse(null);
      if (await handleExpiredSession(searchError)) return;
      setError(searchError instanceof Error ? searchError.message : "Search request failed");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResearch(nextQuery = query) {
    if (scope !== "web" && !auth.user) {
      setLoginRequired(true);
      setError("");
      setView("research");
      return;
    }
    setLoginRequired(false);
    const normalizedQuery = nextQuery.trim();
    if (!normalizedQuery) {
      setError("Enter a research question to begin.");
      searchInputRef.current?.focus();
      return;
    }
    setQuery(normalizedQuery);
    setIsLoading(true);
    setError("");
    setResponse(null);
    setView("research");
    try {
      setResearchResponse(await researchDocuments(normalizedQuery, effectiveMode()));
    } catch (researchError) {
      setResearchResponse(null);
      if (await handleExpiredSession(researchError)) return;
      setError(researchError instanceof Error ? researchError.message : "Research request failed");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleConceptSelect(concept: string) {
    await handleSearch(concept);
  }

  async function handleGraphNodeSelect(node: GraphNode) {
    if (!auth.user) {
      setLoginRequired(true);
      return;
    }
    setSelectedGraphNode(node);
    if (node.node_type !== "concept") return;
    setIsGraphLoading(true);
    try {
      setGraph(await fetchGraph(node.node_id));
    } catch (graphError) {
      if (await handleExpiredSession(graphError)) return;
      setError(graphError instanceof Error ? graphError.message : "Knowledge map unavailable");
    } finally {
      setIsGraphLoading(false);
    }
  }

  async function handleGraphOpen() {
    if (!auth.user) {
      setLoginRequired(true);
      setError("");
      return;
    }
    const concept = response?.discovery?.concepts[0] ?? (query.trim() || "machine learning");
    setIsGraphLoading(true);
    setView("search");
    try {
      setGraph(await fetchGraph(`concept:${concept.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`));
      setSelectedGraphNode(null);
    } catch (graphError) {
      if (await handleExpiredSession(graphError)) return;
      setError(graphError instanceof Error ? graphError.message : "Knowledge map unavailable");
    } finally {
      setIsGraphLoading(false);
    }
  }

  async function handleExpiredSession(requestError: unknown) {
    if (!(requestError instanceof ApiRequestError) || requestError.status !== 401) return false;
    await auth.refresh();
    setLoginRequired(true);
    setError("");
    return true;
  }

  async function handleLogout() {
    try {
      await auth.logout();
      setResponse(null);
      setResearchResponse(null);
      setGraph(null);
      setScope("web");
      navigate("/login");
    } catch (logoutError) {
      setError(logoutError instanceof Error ? logoutError.message : "Could not sign out.");
    }
  }

  function handleResultResearch(title: string) {
    if (!title.trim()) return;
    void handleResearch(title);
  }

  function handleInspectEvidence(queryText: string) {
    if (!queryText.trim()) return;
    void handleSearch(queryText);
  }

  function handleOpenSource(url: string | null | undefined) {
    if (!url) return;
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return;
      window.open(parsed.href, "_blank", "noopener,noreferrer");
    } catch {
      return;
    }
  }

  function handleCommandAction(action: CommandAction) {
    setCommandPaletteOpen(false);
    switch (action) {
      case "focus-search":
        searchInputRef.current?.focus();
        break;
      case "search-private":
        setScope("private");
        if (!auth.user) {
          setLoginRequired(true);
          break;
        }
        if (query.trim()) void handleSearch(query, "private");
        else setError("Enter a search term to query the private vault.");
        break;
      case "search-web":
        setScope("web");
        if (query.trim()) void handleSearch(query, "web");
        else setError("Enter a search term to query the public web.");
        break;
      case "search-all":
        setScope("all");
        if (!auth.user) {
          setLoginRequired(true);
          break;
        }
        if (query.trim()) void handleSearch(query, "all");
        else setError("Enter a search term to query all sources.");
        break;
      case "research-query":
        if (scope !== "web" && !auth.user) {
          setLoginRequired(true);
          break;
        }
        if (query.trim()) void handleResearch(query);
        else setError("Enter a research question to begin.");
        break;
      case "open-discovery":
        void handleGraphOpen();
        break;
      case "toggle-theme":
        setTheme((current) => (current === "dark" ? "light" : "dark"));
        break;
      default:
        break;
    }
  }

  const commandEntries: { label: string; value: CommandAction; hint: string }[] = [
    { label: "Focus search", value: "focus-search", hint: "⌘K" },
    { label: "Search private", value: "search-private", hint: "Scope: private" },
    { label: "Search web", value: "search-web", hint: "Scope: web" },
    { label: "Search all", value: "search-all", hint: "Scope: all" },
    { label: "Research current query", value: "research-query", hint: "Grounded synthesis" },
    { label: "Open discovery", value: "open-discovery", hint: "Knowledge map" },
    { label: "Toggle theme", value: "toggle-theme", hint: "Light / dark" },
  ];

  const filteredCommands = commandEntries.filter((entry) => entry.label.toLowerCase().includes(commandValue.toLowerCase()));
  const grounding = researchResponse?.grounding;
  const groundingLabel = grounding?.status === "grounded" && researchResponse?.citation_validation_passed
    ? "Citations verified"
    : grounding?.status === "partially_grounded"
      ? "Partial grounding"
      : grounding?.status === "unsupported"
        ? "Unsupported claims removed"
        : researchResponse?.evidence_sufficient === false
          ? "Insufficient evidence"
          : "Grounding not assessed";

  return (
    <div className="app-shell">
      <aside className="side-rail">
        <div className="brand-mark" aria-label="NEXUS home">
          <span className="brand-glyph">N</span>
          <span>NEXUS</span>
        </div>
        <div className="rail-status">
          <span className="status-dot" />
          Local-first workspace
        </div>
        <nav aria-label="Primary navigation" className="rail-nav">
          <button aria-label="Search" className={view === "search" ? "rail-link active" : "rail-link"} onClick={() => setView("search")} type="button">
            <span>⌕</span>Search
          </button>
          <button aria-label="Research" className={view === "research" ? "rail-link active" : "rail-link"} onClick={() => setView("research")} type="button">
            <span>✦</span>Research
          </button>
          <button aria-label="Knowledge map" className={graph ? "rail-link active" : "rail-link"} onClick={() => void handleGraphOpen()} type="button">
            <span>◌</span>Knowledge map
          </button>
        </nav>
        <div className="rail-footer">
          {auth.user ? (
            <div className="vault-status">
              <span>⌑</span>
              <div>
                <strong>Private vault</strong>
                <small>Processed locally</small>
              </div>
            </div>
          ) : (
            <div className="vault-status locked-vault">
              <span aria-hidden="true">⌑</span>
              <div>
                <strong>Private vault</strong>
                <small>Sign in to access</small>
              </div>
            </div>
          )}
          <button
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
            className="theme-toggle"
            onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}
            type="button"
          >
            {theme === "light" ? "◐ Dark" : "○ Light"}
          </button>
        </div>
      </aside>

      <main className="main-stage">
        <header className="topbar">
          <span className="topbar-context">PRIVATE INTELLIGENCE / {view.toUpperCase()}</span>
          <div className="topbar-actions">
            {auth.user ? (
              <>
                <span className="account-email" title={auth.user.email}>{auth.user.email}</span>
                <button className="account-action" disabled={auth.busy} onClick={() => void handleLogout()} type="button">
                  {auth.busy ? "Signing out..." : "Log out"}
                </button>
              </>
            ) : (
              <>
                <button className="account-action" onClick={() => navigate("/login")} type="button">Sign in</button>
                <button className="account-action create-account" onClick={() => navigate("/register")} type="button">Create account</button>
              </>
            )}
            <button className="shortcut-hint" onClick={() => setCommandPaletteOpen(true)} type="button">
              ⌘ K <span>Command palette</span>
            </button>
          </div>
        </header>

        <section className={response || researchResponse ? "search-hero compact" : "search-hero"}>
          <div className="hero-kicker">
            <span className="signal-line" />
            Private AI Search
          </div>
          <h1>{view === "research" ? "Make sense of what you know." : "Find the signal."}</h1>
          <p className="hero-copy">Search private vault content, public results, and the relationships between them.</p>

          <SearchBar
            inputRef={searchInputRef}
            isLoading={isLoading}
            onClear={() => {
              setQuery("");
              setResponse(null);
              setResearchResponse(null);
              setGraph(null);
              setError("");
            }}
            onQueryChange={setQuery}
            onResearch={() => void handleResearch()}
            onRerankChange={setRerankEnabled}
            onRetrievalModeChange={setRetrievalMode}
            onScopeChange={(nextScope) => {
              setScope(nextScope);
              setLoginRequired(nextScope !== "web" && !auth.user);
              setError("");
            }}
            onSubmit={() => void handleSearch()}
            query={query}
            rerankEnabled={rerankEnabled}
            retrievalMode={retrievalMode}
            scope={scope}
          />

        </section>

        {loginRequired && !auth.user && (
          <section className="auth-required" role="status">
            <div>
              <span className="section-kicker">ACCOUNT REQUIRED</span>
              <strong>Sign in to search your private vault.</strong>
              <p>WEB search stays available without an account. Private and combined sources require your session.</p>
            </div>
            <div className="auth-required-actions">
              <button className="action-button primary compact" onClick={() => navigate("/login")} type="button">Sign in</button>
              <button className="auth-text-button" onClick={() => navigate("/register")} type="button">Create account</button>
            </div>
          </section>
        )}

        {auth.error && !auth.user && (
          <section className="notice error-notice" role="alert">
            <strong>Session check unavailable.</strong>
            <span>{auth.error}</span>
            <button onClick={() => void auth.refresh()} type="button">Retry</button>
          </section>
        )}

        {error && (
          <section className="notice error-notice" role="alert">
            <strong>Something interrupted the signal.</strong>
            <span>{error}</span>
            <button onClick={() => setError("")} type="button">
              Dismiss
            </button>
          </section>
        )}

        {isLoading && (
          <section aria-live="polite" className="loading-state">
            <span className="loading-pulse" />
            <div>
              <strong>{view === "research" ? "Building a grounded answer" : "Searching your index"}</strong>
              <span>Working locally across the selected sources.</span>
            </div>
          </section>
        )}

        {!isLoading && view === "search" && response && (
          <section className="results-workspace">
            <div className="workspace-heading">
              <div>
                <span className="section-kicker">SEARCH RESULTS</span>
                <h2>
                  {response.total_results} sources for <em>{response.query}</em>
                </h2>
              </div>
              <span className="result-meta">{response.retrieval?.reranked ? "Reranked locally" : "Ranked retrieval"}</span>
            </div>

            {response.total_results === 0 ? (
              <div className="empty-state">
                <span className="empty-icon">∅</span>
                <h3>No signal found</h3>
                <p>Try a broader phrase, switch to All, or widen the retrieval mode.</p>
              </div>
            ) : (
              <SearchResults
                onInspectEvidence={handleInspectEvidence}
                onOpenSource={handleOpenSource}
                onResearch={handleResultResearch}
                results={response.results}
              />
            )}

            <ConceptExplorer concepts={response.discovery?.concepts ?? []} onSelect={handleConceptSelect} />
            {response.discovery?.concepts?.length ? (
              <button className="map-launch" onClick={() => void handleGraphOpen()} type="button">
                <span>◌</span>
                <div>
                  <strong>Explore the knowledge map</strong>
                  <small>See how these results connect through concepts and sources.</small>
                </div>
                <span>→</span>
              </button>
            ) : null}
          </section>
        )}

        {!isLoading && view === "research" && researchResponse && (
          <section className="research-workspace">
            <div className="workspace-heading">
              <div>
                <span className="section-kicker">
                  LOCAL OLLAMA · {scope === "private" ? "PRIVATE CONTEXT" : scope === "web" ? "PUBLIC WEB CONTEXT" : "ALL SELECTED SOURCES"}
                </span>
                <h2>
                  Grounded synthesis for <em>{researchResponse.query}</em>
                </h2>
              </div>
              <span className={grounding?.status === "grounded" && researchResponse.citation_validation_passed ? "validation-badge" : "validation-badge warning"}>
                {groundingLabel}
              </span>
            </div>

            <ResearchAnswer answer={researchResponse.answer} groundingStatus={grounding?.status ?? "not_assessed"} valid={researchResponse.citation_validation_passed} />

            <div className="research-grid">
              <CitationList citations={researchResponse.citations} />
              <EvidencePanel evidence={researchResponse.evidence} />
              <RelatedTopics
                onSelect={(topic) => {
                  if (topic.trim()) void handleResearch(topic);
                }}
                topics={researchResponse.related_topics}
              />
            </div>
          </section>
        )}

        {!isLoading && !response && !researchResponse && !error && (
          <section className="welcome-strip">
            <div>
              <span className="section-kicker">READY WHEN YOU ARE</span>
              <h2>Your knowledge, with a little more reach.</h2>
              <p>Search the private vault, inspect public sources, or move from a result into a grounded research answer.</p>
            </div>
            <div className="welcome-index">
              <span>01</span>
              <strong>Search</strong>
              <span>02</span>
              <strong>Discover</strong>
              <span>03</span>
              <strong>Research</strong>
            </div>
          </section>
        )}

        {graph && (
          <section className="discovery-workspace">
            <div className="workspace-heading">
              <div>
                <span className="section-kicker">KNOWLEDGE DISCOVERY</span>
                <h2>See the structure behind the result.</h2>
              </div>
              {isGraphLoading && <span className="result-meta">Expanding map...</span>}
            </div>

            <KnowledgeGraph
              graph={graph}
              isBusy={isLoading || isGraphLoading}
              onExpand={async (node) => {
                setIsGraphLoading(true);
                try {
                  setGraph(await fetchGraph(node.node_id));
                } catch (graphError) {
                  setError(graphError instanceof Error ? graphError.message : "Knowledge map unavailable");
                } finally {
                  setIsGraphLoading(false);
                }
              }}
              onNodeSelect={handleGraphNodeSelect}
              onResearchConcept={(concept) => {
                if (concept.trim()) void handleResearch(concept);
              }}
              onSearchConcept={(concept) => {
                if (concept.trim()) void handleSearch(concept);
              }}
              selectedNodeId={selectedGraphNode?.node_id ?? null}
            />

            <aside className="node-inspector">
              {selectedGraphNode ? (
                <>
                  <span className="section-kicker">SELECTED NODE</span>
                  <h3>{selectedGraphNode.label}</h3>
                  <p>
                    {selectedGraphNode.node_type === "concept"
                      ? "A concept extracted from indexed evidence."
                      : selectedGraphNode.source_type === "public_web"
                        ? `Public web source · ${selectedGraphNode.domain ?? "verified domain"}`
                        : "Private source in your local vault."}
                  </p>
                  <button className="action-button primary" onClick={() => void handleConceptSelect(selectedGraphNode.label)} type="button">
                    Search this concept →
                  </button>
                </>
              ) : (
                <p>Select a concept or source to inspect its contribution.</p>
              )}
            </aside>
          </section>
        )}
      </main>

      {commandPaletteOpen && (
        <div aria-modal="true" className="command-overlay" onClick={() => setCommandPaletteOpen(false)} role="dialog">
          <div className="command-palette" onClick={(event) => event.stopPropagation()}>
            <div className="command-header">
              <span>Command palette</span>
              <kbd>Esc</kbd>
            </div>
            <input
              autoFocus
              className="command-input"
              onChange={(event) => setCommandValue(event.target.value)}
              placeholder="Search commands..."
              type="text"
              value={commandValue}
            />
            <div className="command-list">
              {filteredCommands.length ? (
                filteredCommands.map((entry) => (
                  <button className="command-item" key={entry.value} onClick={() => handleCommandAction(entry.value)} type="button">
                    <span>{entry.label}</span>
                    <small>{entry.hint}</small>
                  </button>
                ))
              ) : (
                <div className="command-empty">No matching command.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SearchPage;
