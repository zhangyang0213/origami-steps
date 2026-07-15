import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from '@dagrejs/dagre';
import StepNode from './StepNode';
import type { StepData } from '../types';

// dagre 布局参数
const NODE_WIDTH = 220;
const NODE_HEIGHT = 240;

// 使用 dagre 进行水平布局
function getLayoutedElements(nodes: Node[], edges: Edge[]): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 100 });

  nodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

const nodeTypes = { stepNode: StepNode };

interface FlowChartProps {
  steps: StepData[];
}

function FlowChart({ steps }: FlowChartProps) {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    const nodes: Node[] = steps.map((step) => ({
      id: String(step.step_number),
      type: 'stepNode',
      data: { step },
      position: { x: 0, y: 0 },
    }));

    const edges: Edge[] = steps.slice(0, -1).map((step, i) => ({
      id: `e${step.step_number}-${steps[i + 1].step_number}`,
      source: String(step.step_number),
      target: String(steps[i + 1].step_number),
      type: 'smoothstep',
      animated: false,
      style: { stroke: '#e8734a', strokeWidth: 2 },
    }));

    return getLayoutedElements(nodes, edges);
  }, [steps]);

  const [nodes] = useNodesState(layoutedNodes);
  const [edges] = useEdgesState(layoutedEdges);

  const onInit = useCallback((instance: any) => {
    setTimeout(() => instance.fitView({ padding: 0.2 }), 50);
  }, []);

  if (steps.length === 0) {
    return (
      <div className="flowchart-empty">
        <p>🔍 请输入折纸名称或上传图片，查看步骤分解</p>
      </div>
    );
  }

  return (
    <div className="flowchart-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onInit={onInit}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
      >
        <Controls />
        <MiniMap
          nodeStrokeColor="#e8734a"
          nodeColor="#fffdf7"
          nodeBorderRadius={8}
        />
        <Background variant={BackgroundVariant.Dots} color="#d4c5b0" gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}

export default FlowChart;
