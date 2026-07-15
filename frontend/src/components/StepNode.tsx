import { Handle, Position, type NodeProps } from 'reactflow';
import type { StepData } from '../types';
import './StepNode.css';

function StepNode({ data }: NodeProps<{ step: StepData }>) {
  const { step } = data;
  // 判断图片类型：SVG data URI 或普通 URL
  const hasImage = step.image_url && (step.image_url.startsWith('data:image') || step.image_url.startsWith('http'));

  return (
    <div className="step-node">
      <Handle type="target" position={Position.Left} style={{ visibility: 'hidden' }} />
      <div className="step-node__badge">{step.step_number}</div>
      <div className="step-node__image">
        {hasImage ? (
          <img
            src={step.image_url}
            alt={step.title || `步骤${step.step_number}`}
          />
        ) : (
          <div className="step-node__placeholder">
            <span className="step-node__placeholder-num">{step.step_number}</span>
          </div>
        )}
      </div>
      <div className="step-node__title">{step.title || `步骤 ${step.step_number}`}</div>
      <div className="step-node__description">{step.description}</div>
      <Handle type="source" position={Position.Right} style={{ visibility: 'hidden' }} />
    </div>
  );
}

export default StepNode;
