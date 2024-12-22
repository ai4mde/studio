import { RemarkPlugin, RemarkNode } from './types/remark';

const remarkPlantuml: RemarkPlugin = () => {
  return (tree: RemarkNode) => {
    // Implementation
    return tree;
  };
};

export default remarkPlantuml; 