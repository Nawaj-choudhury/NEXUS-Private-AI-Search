function GraphLegend() {
  return (
    <div className="graph-legend" aria-label="Graph legend">
      <span><i className="legend-dot concept-dot" />Concept</span>
      <span><i className="legend-dot private-dot" />Private source</span>
      <span><i className="legend-dot web-dot" />Public web source</span>
    </div>
  );
}

export default GraphLegend;