import { useMemo, useState } from "react";

import type { GraphNode as GraphNodeData, GraphResponse } from "../services/graphService";
import GraphLegend from "./GraphLegend";
import GraphNode from "./GraphNode";

type Props = {
  graph: GraphResponse;
  isBusy?: boolean;
  selectedNodeId?: string | null;
  onNodeSelect: (node: GraphNodeData) => void;
  onExpand: (node: GraphNodeData) => void;
  onSearchConcept: (concept: string) => void;
  onResearchConcept: (concept: string) => void;
};

function KnowledgeGraph({ graph, isBusy = false, selectedNodeId, onNodeSelect, onExpand, onSearchConcept, onResearchConcept }: Props) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(selectedNodeId ?? null);

  const width = 760;
  const height = 360;

  const center = useMemo(
    () => graph.nodes.find((node) => node.node_id === graph.center_id) ?? graph.nodes[0],
    [graph.center_id, graph.nodes],
  );

  const positions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    if (center) map.set(center.node_id, { x: width / 2, y: height / 2 });

    const rest = graph.nodes.filter((node) => node.node_id !== center?.node_id);
    rest.forEach((node, index) => {
      const angle = (index / Math.max(rest.length, 1)) * Math.PI * 2;
      map.set(node.node_id, {
        x: width / 2 + Math.cos(angle) * 210,
        y: height / 2 + Math.sin(angle) * 108,
      });
    });
    return map;
  }, [center, graph.nodes]);

  const selectedNode = graph.nodes.find((node) => node.node_id === (selectedNodeId ?? focusedNodeId)) ?? null;

  const handleFocus = () => {
    if (!selectedNode) return;
    const pos = positions.get(selectedNode.node_id);
    if (!pos) return;
    setFocusedNodeId(selectedNode.node_id);
    setPan({ x: width / 2 - pos.x * zoom, y: height / 2 - pos.y * zoom });
  };

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setFocusedNodeId(null);
  };

  return (
    <section className="knowledge-graph" aria-label="Knowledge graph">
      <div className="graph-header-row">
        <div className="graph-heading">
          <h2>Knowledge map</h2>
          <span>
            {graph.nodes.length} nodes · {graph.edges.length} relationships
          </span>
        </div>
        <div className="graph-toolbar" aria-label="Knowledge map controls">
          <button className="small-button" onClick={() => setZoom((value) => Number(Math.max(0.8, value - 0.15)).toFixed(2) as unknown as number)} type="button">−</button>
          <button className="small-button" onClick={() => setZoom((value) => Number(Math.min(1.8, value + 0.15)).toFixed(2) as unknown as number)} type="button">+</button>
          <button className="small-button" onClick={handleFocus} type="button">Focus</button>
          <button className="small-button" onClick={handleReset} type="button">Reset</button>
        </div>
      </div>

      <GraphLegend />

      <div className="graph-canvas-wrap">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Knowledge graph visualization">
          <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
            {graph.edges.map((edge) => {
              const source = positions.get(edge.source_id);
              const target = positions.get(edge.target_id);
              if (!source || !target) return null;
              return (
                <line
                  className="graph-edge"
                  key={`${edge.source_id}-${edge.target_id}-${edge.relation}`}
                  x1={source.x}
                  x2={target.x}
                  y1={source.y}
                  y2={target.y}
                />
              );
            })}
            {graph.nodes.map((node) => {
              const position = positions.get(node.node_id);
              if (!position) return null;
              return (
                <GraphNode
                  isSelected={selectedNodeId === node.node_id || focusedNodeId === node.node_id}
                  key={node.node_id}
                  node={node}
                  onSelect={onNodeSelect}
                  x={position.x}
                  y={position.y}
                />
              );
            })}
          </g>
        </svg>
      </div>

      {selectedNode && (
        <div className="graph-actions">
          <button className="action-button compact primary" disabled={isBusy} onClick={() => onExpand(selectedNode)} type="button">
            Expand
          </button>
          <button className="action-button compact" disabled={isBusy} onClick={() => onSearchConcept(selectedNode.label)} type="button">
            Search concept
          </button>
          <button className="action-button compact" disabled={isBusy} onClick={() => onResearchConcept(selectedNode.label)} type="button">
            Research concept
          </button>
        </div>
      )}

      {graph.explanation && <p className="graph-explanation">{graph.explanation}</p>}
    </section>
  );
}

export default KnowledgeGraph;