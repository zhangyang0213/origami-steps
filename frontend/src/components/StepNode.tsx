import { Handle, Position, type NodeProps } from 'reactflow';
import type { StepData } from '../types';
import './StepNode.css';

// 自定义 ReactFlow 节点：折纸步骤卡片
function StepNode({ data }: NodeProps<{ step: StepData }>) {
  const { step } = data;

  return (
    <div className="step-node">
      <Handle type="target" position={Position.Left} />
      <div className="step-node__badge">步骤 {step.step_number}</div>
      <div className="step-node__image">
        {step.image_url ? (
          <img src={step.image_url} alt={step.title} />
        ) : (
          <div className="step-node__placeholder">📐</div>
        )}
      </div>
      <div className="step-node__title">{step.title}</div>
      <div className="step-node__description">{step.description}</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export default StepNode;
