import type { GroundingStatus } from "../services/researchService";

function ResearchAnswer({ answer, valid, groundingStatus }: { answer: string; valid: boolean; groundingStatus: GroundingStatus }) {
  const warning = groundingStatus === "partially_grounded"
    ? "Partially supported claims were replaced with an evidence-limit notice."
    : groundingStatus === "unsupported"
      ? "Unsupported claims were replaced with an evidence-limit notice."
      : !valid
        ? "The answer was withheld because it contained invalid citation references."
        : null;

  return (
    <section className="research-answer">
      <div className="research-label">AI SYNTHESIS</div>
      <h2>Research answer</h2>
      <p>{answer}</p>
      {warning && (
        <div className="callout warning">
          {warning}
        </div>
      )}
    </section>
  );
}

export default ResearchAnswer;