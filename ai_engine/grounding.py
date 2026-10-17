import re
from collections.abc import Sequence
from dataclasses import dataclass

from .context_builder import ContextItem
from .models import ClaimGrounding, GroundingSummary

CITATION_PATTERN = re.compile(r"\[(S\d+)\]")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
CLAUSE_SPLIT_PATTERN = re.compile(
    r";\s*|,\s+(?=(?:and|but|however|while)\b)|\s+(?:but|however)\s+|(?<=\])\s+(?:and|but)\s+(?!\[S\d+\])",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
NEGATION_PATTERN = re.compile(r"\b(?:no|not|never|without|cannot|can't|isn't|aren't|wasn't|weren't|doesn't|don't|didn't|won't|wouldn't|shouldn't|lack|lacks|lacking)\b", re.IGNORECASE)
UNSUPPORTED_CLAIM_TEXT = "The available indexed evidence does not provide enough information to establish this claim."
SUPPORTED_OVERLAP = 0.6
PARTIAL_OVERLAP = 0.3

STOPWORDS = frozenset(
    "a about above after again against all am an and any are as at be because been before being below "
    "between both but by can could did do does doing down during each few for from further had has have "
    "having he her here hers herself him himself his how i if in into is it its itself just me more most "
    "my myself no nor not of off on once only or other ought our ours ourselves out over own same she "
    "should so some such than that the their theirs them themselves then there these they this those "
    "through to too under until up very was we were what when where which while who whom why will with "
    "would you your yours yourself yourselves"
    .split()
)


@dataclass(frozen=True, slots=True)
class ExtractedClaim:
    text: str
    original: str
    citation_ids: tuple[str, ...]


def _normalize_term(term: str) -> str:
    if len(term) > 5 and term.endswith("ies"):
        return term[:-3] + "y"
    if len(term) > 5 and term.endswith("ing"):
        term = term[:-3]
        if len(term) > 2 and term[-1] == term[-2]:
            term = term[:-1]
        return term
    if len(term) > 4 and term.endswith("ed"):
        return term[:-2]
    if len(term) > 4 and term.endswith("s"):
        return term[:-1]
    return term


def _meaningful_terms(text: str) -> set[str]:
    return {
        normalized
        for term in TOKEN_PATTERN.findall(text.lower())
        if term not in STOPWORDS
        for normalized in (_normalize_term(term),)
        if len(normalized) > 2
    }


def extract_claims(answer: str) -> tuple[ExtractedClaim, ...]:
    """Treat each short-answer sentence as one assertion with only its local citations."""
    claims: list[ExtractedClaim] = []
    normalized_answer = re.sub(r"([.!?])\s+(\[(?:S\d+)\](?:\s+\[S\d+\])*)", r" \2\1", answer.strip())
    for sentence in SENTENCE_SPLIT_PATTERN.split(normalized_answer):
        for segment in CLAUSE_SPLIT_PATTERN.split(sentence):
            original = segment.strip()
            if not original:
                continue
            citation_ids = tuple(dict.fromkeys(match.group(1) for match in CITATION_PATTERN.finditer(original)))
            text = CITATION_PATTERN.sub("", original)
            text = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", text).strip()
            text = re.sub(r"\s+([,.!?;:])", r"\1", text)
            if _meaningful_terms(text):
                claims.append(ExtractedClaim(text, original, citation_ids))
    return tuple(claims)


def _overlap(claim: str, evidence: str) -> float:
    claim_terms = _meaningful_terms(claim)
    if not claim_terms:
        return 0.0
    evidence_terms = _meaningful_terms(evidence)
    return len(claim_terms & evidence_terms) / len(claim_terms)


def _negation_mismatch(claim: str, evidence: str) -> bool:
    return bool(NEGATION_PATTERN.search(claim)) != bool(NEGATION_PATTERN.search(evidence))


def _supported_citations(claim: ExtractedClaim, evidence_by_id: dict[str, ContextItem]) -> tuple[str, ...]:
    return tuple(
        citation_id
        for citation_id in claim.citation_ids
        if citation_id in evidence_by_id and _overlap(claim.text, evidence_by_id[citation_id].text) >= SUPPORTED_OVERLAP
    )


def _assess_claim(claim: ExtractedClaim, evidence_by_id: dict[str, ContextItem]) -> ClaimGrounding:
    overlaps = {
        citation_id: 0.0 if _negation_mismatch(claim.text, evidence_by_id[citation_id].text) else _overlap(claim.text, evidence_by_id[citation_id].text)
        for citation_id in claim.citation_ids
        if citation_id in evidence_by_id
    }
    supported_ids = tuple(citation_id for citation_id in claim.citation_ids if overlaps.get(citation_id, 0.0) >= SUPPORTED_OVERLAP)
    partial_ids = tuple(citation_id for citation_id in claim.citation_ids if PARTIAL_OVERLAP <= overlaps.get(citation_id, 0.0) < SUPPORTED_OVERLAP)
    if supported_ids:
        status = "SUPPORTED"
    elif partial_ids:
        status = "PARTIALLY_SUPPORTED"
    else:
        status = "UNSUPPORTED"
    return ClaimGrounding(claim.text, claim.citation_ids, supported_ids, partial_ids, status)


def _render_supported_claim(claim: ExtractedClaim, supporting_ids: Sequence[str]) -> str:
    text = CITATION_PATTERN.sub("", claim.original).strip()
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    ending_match = re.search(r"([.!?]+[\"')\]]?)$", text)
    if ending_match:
        ending = ending_match.group(1)
        body = text[:-len(ending)].rstrip()
    else:
        ending = "."
        body = text.rstrip()
    if body:
        body = body[0].upper() + body[1:]
    citations = " ".join(f"[{citation_id}]" for citation_id in supporting_ids)
    return f"{body} {citations}{ending}" if citations else text


def ground_answer(answer: str, evidence: Sequence[ContextItem]) -> tuple[str, GroundingSummary]:
    """Retain only claims with strong lexical support in their cited evidence text.

    SUPPORTED requires at least 80% meaningful-term overlap with a cited item.
    PARTIALLY_SUPPORTED requires 30%-79% overlap. UNSUPPORTED means no cited item
    reaches 30%, including claims with missing or invalid citation IDs. Partial and
    unsupported claims are replaced rather than repeated as factual statements.
    """
    claims = extract_claims(answer)
    if not claims:
        return answer.strip(), GroundingSummary()

    evidence_by_id = {item.citation_id: item for item in evidence}
    assessed = tuple(_assess_claim(claim, evidence_by_id) for claim in claims)
    final_sentences: list[str] = []
    disclaimer_added = False
    for claim, assessment in zip(claims, assessed, strict=True):
        if assessment.status == "SUPPORTED":
            final_sentences.append(_render_supported_claim(claim, assessment.supporting_citation_ids))
        elif not disclaimer_added:
            final_sentences.append(UNSUPPORTED_CLAIM_TEXT)
            disclaimer_added = True

    supported_count = sum(claim.status == "SUPPORTED" for claim in assessed)
    partial_count = sum(claim.status == "PARTIALLY_SUPPORTED" for claim in assessed)
    unsupported_count = sum(claim.status == "UNSUPPORTED" for claim in assessed)
    if supported_count == len(assessed):
        status = "grounded"
    elif supported_count:
        status = "partially_grounded"
    elif partial_count:
        status = "partially_grounded"
    else:
        status = "unsupported"

    summary = GroundingSummary(status, len(assessed), supported_count, partial_count, unsupported_count, assessed)
    return " ".join(final_sentences), summary