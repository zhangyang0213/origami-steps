import { useEffect, useMemo } from 'react';
import ReactFlow, {
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  type Node,
  type Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from '@dagrejs/dagre';
import StepNode from './StepNode';
import type { StepData } from '../types';

const NODE_WIDTH = 220;
const NODE_HEIGHT = 260;

function getLayoutedElements(nodes: Node[], edges: Edge[]) {
  if (nodes.length === 0) return { nodes: [], edges: [] };

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 120 });

  nodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });
  dagre.layout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
    };
  });

  return { nodes: layoutedNodes, edges };
}

const nodeTypes = { stepNode: StepNode };

interface FlowChartInnerProps {
  steps: StepData[];
}

function FlowChartInner({ steps }: FlowChartInnerProps) {
  const { fitView } = useReactFlow();

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(() => {
    const nodes: Node[] = steps.map((step) => ({
      id: `step-${step.step_number}`,
      type: 'stepNode',
      data: { step },
      position: { x: 0, y: 0 },
    }));

    const edges: Edge[] = steps.slice(0, -1).map((step, i) => ({
      id: `e${step.step_number}-${steps[i + 1].step_number}`,
      source: `step-${step.step_number}`,
      target: `step-${steps[i + 1].step_number}`,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#e8734a', strokeWidth: 2 },
    }));

    return getLayoutedElements(nodes, edges);
  }, [steps]);

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  // 当 steps 变化时，强制更新节点和边
  useEffect(() => {
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
    // 延迟 fitView 确保 DOM 更新完成
    setTimeout(() => fitView({ padding: 0.2, duration: 300 }), 100);
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges, fitView]);

  if (steps.length === 0) {
    return (
      <div className="flowchart-empty">
        <div className="flowchart-empty__icon">📐</div>
        <p>请输入折纸名称或上传图片，查看步骤分解</p>
        <p className="flowchart-empty__hint">点击上方「演示」按钮快速体验</p>
      </div>
    );
  }

  return (
    <div className="flowchart-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
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

interface FlowChartProps {
  steps: StepData[];
}

function FlowChart({ steps }: FlowChartProps) {
  return (
    <ReactFlowProvider>
      <FlowChartInner steps={steps} />
    </ReactFlowProvider>
  );
}

export default FlowChart;
