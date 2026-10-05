import { apiRequest } from "./api";

export type Citation = {
  citation_id: string;
  title: string;
  source: string;
  document_id: string;
  chunk_id: string;
  source_type?: string;
  url?: string | null;
};

export type EvidenceItem = {
  citation_id: string;
  excerpt: string;
  title: string;
  source: string;
  document_id: string;
  chunk_id: string;
  score: number;
  source_type?: string;
  url?: string | null;
};

export type GroundingStatus = "grounded" | "partially_grounded" | "unsupported" | "not_assessed";
export type ClaimGroundingStatus = "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED";

export type ClaimGrounding = {
  claim: string;
  citation_ids: string[];
  supporting_citation_ids: string[];
  partially_supporting_citation_ids: string[];
  status: ClaimGroundingStatus;
};

export type GroundingSummary = {
  status: GroundingStatus;
  claims_checked: number;
  claims_supported: number;
  claims_partially_supported: number;
  claims_unsupported: number;
  claims: ClaimGrounding[];
};

export type ResearchResponse = {
  query: string;
  answer: string;
  citations: Citation[];
  evidence: EvidenceItem[];
  related_topics: { topic: string; citation_ids: string[] }[];
  sources: Citation[];
  evidence_sufficient: boolean;
  citation_validation_passed: boolean;
  grounding: GroundingSummary;
};

export async function researchDocuments(query: string, mode = "hybrid", topK = 5): Promise<ResearchResponse> {
  const response = await apiRequest("/api/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode, top_k: topK }),
  });
  return response.json() as Promise<ResearchResponse>;
}