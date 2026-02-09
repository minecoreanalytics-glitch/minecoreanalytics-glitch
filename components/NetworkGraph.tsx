import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

// Simple types for the graph data
interface Node extends d3.SimulationNodeDatum {
  id: string;
  group: number;
  val: number;
  type?: string;
  label?: string;
  properties?: any;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  type?: string;
  properties?: any;
}

interface GraphData {
  nodes: any[];
  edges: any[];
  stats?: any;
}

interface NetworkGraphProps {
  height?: number;
  className?: string;
  data?: GraphData | null;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({ height = 400, className = "", data: graphData }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    // Clear previous
    d3.select(svgRef.current).selectAll("*").remove();

    const width = containerRef.current.clientWidth;

    // Transform API data or use mock data
    let data: { nodes: Node[]; links: Link[] };
    
    if (graphData && graphData.nodes && graphData.edges) {
      // Transform API data to D3 format
      data = {
        nodes: graphData.nodes.map(node => ({
          id: node.id,
          group: node.type === 'table' ? 1 : 2,
          val: node.type === 'table' ? 15 : 8,
          type: node.type,
          label: node.label,
          properties: node.properties
        })),
        links: graphData.edges
          .filter(edge => edge.type === 'RELATED_TO')
          .map(edge => ({
            source: edge.from_id,
            target: edge.to_id,
            type: edge.type,
            properties: edge.properties
          }))
      };
    } else {
      // Mock Morpheus Graph data structure
      data = {
        nodes: [
          { id: "Morpheus Core", group: 1, val: 20 },
          { id: "HTV Group", group: 2, val: 15 },
          { id: "BigQuery", group: 3, val: 10 },
          { id: "Salesforce", group: 3, val: 10 },
          { id: "Morpheus 360", group: 1, val: 15 },
          { id: "Billing Data", group: 4, val: 5 },
          { id: "Service Tickets", group: 4, val: 5 },
          { id: "Equipment", group: 4, val: 5 },
          { id: "Action Exec", group: 1, val: 10 },
        ] as Node[],
        links: [
          { source: "Morpheus Core", target: "BigQuery" },
          { source: "Morpheus Core", target: "Salesforce" },
          { source: "Morpheus Core", target: "Morpheus 360" },
          { source: "Morpheus 360", target: "HTV Group" },
          { source: "BigQuery", target: "Billing Data" },
          { source: "Salesforce", target: "Service Tickets" },
          { source: "Morpheus Core", target: "Action Exec" },
          { source: "HTV Group", target: "Equipment" },
        ] as Link[]
      };
    }

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height]);

    // Simulation setup
    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Draw lines
    const link = svg.append("g")
      .attr("stroke", "#374151")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(data.links)
      .join("line")
      .attr("stroke-width", 1.5);

    // Draw nodes
    const node = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(data.nodes)
      .join("circle")
      .attr("r", (d) => d.val)
      .attr("fill", (d) => {
        if (d.group === 1) return "#06B6D4"; // Core (Cyan)
        if (d.group === 2) return "#10B981"; // Customer (Green)
        if (d.group === 3) return "#3B82F6"; // Integration (Blue)
        return "#6B7280"; // Data (Gray)
      })
      .call(drag(simulation) as any);

    // Labels
    const text = svg.append("g")
      .selectAll("text")
      .data(data.nodes)
      .join("text")
      .text((d) => d.id)
      .attr("font-size", "10px")
      .attr("fill", "#9CA3AF")
      .attr("dx", 12)
      .attr("dy", 4);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y);

      text
        .attr("x", (d: any) => d.x)
        .attr("y", (d: any) => d.y);
    });

    function drag(simulation: d3.Simulation<Node, undefined>) {
      function dragstarted(event: any) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      function dragged(event: any) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      function dragended(event: any) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }

      return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }

  }, [height]);

  return (
    <div ref={containerRef} className={`w-full bg-morpheus-800 rounded-xl border border-morpheus-700 overflow-hidden shadow-lg relative ${className}`}>
      <div className="absolute top-4 left-4 z-10 pointer-events-none">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Morpheus Knowledge Graph
        </h3>
        <p className="text-xs text-gray-400">Real-time Entity Relations</p>
      </div>
      <svg ref={svgRef} className="w-full" style={{ height: `${height}px` }}></svg>
    </div>
  );
};

export default NetworkGraph;