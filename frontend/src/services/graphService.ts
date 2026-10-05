import { apiRequest } from "./api";

export type GraphNode = {
  node_id: string;
  node_type: "concept" | "document" | "web_source";
  label: string;
  source_type?: string | null;
  document_id?: string | null;
  url?: string | null;
  domain?: string | null;
  occurrence_count: number;
  chunk_ids: string[];
};

export type GraphEdge = {
  source_id: string;
  target_id: string;
  relation: string;
  weight: number;
  evidence_count: number;
  method: string;
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  center_id?: string | null;
  explanation?: string | null;
};

export async function fetchGraph(conceptId: string): Promise<GraphResponse> {
  const response = await apiRequest(`/api/graph/concept/${encodeURIComponent(conceptId)}`);
  return response.json() as Promise<GraphResponse>;
}