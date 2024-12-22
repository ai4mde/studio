import { Node } from 'unist';

export interface RemarkPlugin {
  (options?: unknown): (tree: Node) => Node | Promise<Node>;
}

export interface RemarkNode extends Node {
  value?: string;
  lang?: string;
  children?: RemarkNode[];
  data?: {
    hProperties?: Record<string, unknown>;
    hName?: string;
    hChildren?: RemarkNode[];
  };
} 