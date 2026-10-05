import { apiRequest } from "./api";

export type SearchResult = {
  title: string;
  snippet: string;
  score: number;
  source: string;
  document_id: string;
  chunk_id: string;
  source_type: string;
  url?: string | null;
  domain?: string | null;
};

export type SearchResponse = {
  query: string;
  total_results: number;
  retrieval?: {
    mode: string;
    reranked: boolean;
    candidate_count: number;
    final_count: number;
  };
  discovery?: { concepts: string[] };
  results: SearchResult[];
};

export type SearchMode = "keyword" | "semantic" | "hybrid" | "private" | "web" | "all";

export async function searchDocuments(query: string, mode: SearchMode, rerank = true): Promise<SearchResponse> {
  const response = await apiRequest(`/api/search?q=${encodeURIComponent(query)}&mode=${mode}&rerank=${String(rerank)}`);
  return response.json() as Promise<SearchResponse>;
}