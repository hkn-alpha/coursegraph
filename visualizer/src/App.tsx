import React, { useCallback, useMemo } from "react";
import "./App.css";
import DagreGraph from "dagre-d3-react";
import { curveBundle } from "d3";
import { edges } from "./edges";
import { nodes } from "./nodes";
import useResizeObserver from "use-resize-observer";
import dagre from "dagre";

const NODE_CONFIG = {
  ry: 8, // border radius
  rx: 8,
  style: "fill: white; stroke-width: 2px; stroke: #0f2040;",
  width: 200,
  height: 75,
};

const CURVE_CONFIG = {
  curve: curveBundle,
  style: "fill:none; stroke: #0f2040; stroke-width: 2px;",
};

const CURVE_COREQ_CONFIG = {
  curve: curveBundle,
  style: CURVE_CONFIG.style + "stroke-dasharray:4;",
};

const DAGRE_CONFIG = {
  rankdir: "BT", // use LR for non-EE
  align: "UL", // always use UL
  ranker: "longest-path",
  ranksep: 70,
  nodesep: 50,
  edgesep: 60,
  marginx: 2,
  marginy: 2,
};

function getUrl(dept: string, num: string) {
  if (dept === "ECE" && num === "374") {
    num = "374B";
  } else if (dept === "CS" && num === "374") {
    num = "374A";
  }
  return (
    "/" +
    encodeURIComponent("Course Wiki") +
    "/" +
    encodeURIComponent(`${dept} Course Offerings`) +
    "/" +
    dept +
    num +
    "/"
  );
}

const dagreNodes = nodes.map((node) => ({
  id: node.id,
  label: `<a href="${getUrl(
    node.dept,
    node.num
  )}"><div class="containerdiv"><p class="coursename">${
    node.label
  }</p></div></a>`,
  labelType: "html",
  config: NODE_CONFIG,
}));

const reactNodes = [...dagreNodes];

const dagreEdges = (edges as [string, string, boolean][]).map(
  ([from, to, isCoreq]) => ({
    source: from,
    target: to,
    config: isCoreq ? CURVE_COREQ_CONFIG : CURVE_CONFIG,
  })
);

const g = new dagre.graphlib.Graph();

g.setGraph({});
g.setDefaultEdgeLabel(function () {
  return {};
});

dagreNodes.forEach((node) => g.setNode(node.id, node));
dagreEdges.forEach((edge) => g.setEdge(edge.source, edge.target));

dagre.layout(g, DAGRE_CONFIG);

const reactEdges = [...dagreEdges];

function App() {
  const { ref, width = 1000 } = useResizeObserver();
  return (
    <div ref={ref}>
      <DagreGraph
        nodes={reactNodes as any} // sorry sorry sorry
        links={reactEdges}
        config={DAGRE_CONFIG}
        width={Math.max(1000, Math.min(width, 1920)).toString()}
        height={"1800"}
        shape="rect"
        zoomable
        onNodeClick={(n: any) => console.log(n)}
        onRelationshipClick={() => console.log("edge")}
      />
    </div>
  );
}

export default App;
