import {computeAutogroupedBarSegments, type TraceTree} from './traceTree';
import {TraceTreeNode} from './traceTreeNode';

export class ParentAutogroupNode extends TraceTreeNode<TraceTree.ChildrenAutogroup> {
  head: TraceTreeNode<TraceTree.Span>;
  tail: TraceTreeNode<TraceTree.Span>;
  groupCount: number = 0;
  profiles: TraceTree.Profile[] = [];

  private _autogroupedSegments: [number, number][] | undefined;

  constructor(
    parent: TraceTreeNode<TraceTree.NodeValue> | null,
    node: TraceTree.ChildrenAutogroup,
    metadata: TraceTree.Metadata,
    head: TraceTreeNode<TraceTree.Span>,
    tail: TraceTreeNode<TraceTree.Span>
  ) {
    super(parent, node, metadata);

    this.expanded = false;
    this.head = head;
    this.tail = tail;
  }

  get children() {
    if (this.expanded) {
      return [this.head];
    }
    return this.tail.children;
  }

  // For parent autogroup nodes, in order to compute the bar segments, we need
  // to look at all of the children from head to tail.
  get autogroupedSegments(): [number, number][] {
    if (this._autogroupedSegments) {
      return this._autogroupedSegments;
    }

    const children: TraceTreeNode<TraceTree.NodeValue>[] = [];
    let start: TraceTreeNode<TraceTree.NodeValue> | undefined = this.head;

    while (start && start !== this.tail) {
      children.push(start);
      start = start.children[0];
    }

    children.push(this.tail);

    this._autogroupedSegments = computeAutogroupedBarSegments(children);
    return this._autogroupedSegments;
  }
}
