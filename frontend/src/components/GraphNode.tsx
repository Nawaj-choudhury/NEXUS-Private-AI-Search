import type { GraphNode as GraphNodeData } from "../services/graphService";

type Props = {
  node: GraphNodeData;
  x: number;
  y: number;
  isSelected: boolean;
  onSelect: (node: GraphNodeData) => void;
};

function GraphNode({ node, x, y, isSelected, onSelect }: Props) {
  const isConcept = node.node_type === "concept";
  const isWeb = node.node_type === "web_source";
  const fill = isConcept ? "var(--accent)" : isWeb ? "var(--signal)" : "var(--muted)";
  const radius = isConcept ? 22 : 17;

  return (
    <g className={isSelected ? "graph-node selected" : "graph-node"} onClick={() => onSelect(node)} onKeyDown={(event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onSelect(node);
      }
    }} role="button" tabIndex={0}>
      <circle cx={x} cy={y} fill={fill} r={radius} stroke={isSelected ? "var(--ink)" : "transparent"} strokeWidth={isSelected ? 2 : 0} />
      <text x={x} y={y + 38} textAnchor="middle">
        {node.label.length > 18 ? `${node.label.slice(0, 17)}…` : node.label}
      </text>
    </g>
  );
}

export default GraphNode;