<p align="center">
    <img
        src="https://avatars.githubusercontent.com/u/155311177"
        alt="AI4MDE studio"
        width="64"
    />
</p>

<h1 align="center">
  <b>Working with Diagrams</b>
</h1>

You can create diagrams from scratch in the `Projects` section accessible from the sidebar menu. Here, you first create and name your project. A project can have many systems, and a system can have many diagrams. For example, you might want to create a project called `Airline`, which is split over several systems such as `Logistics`, `Payments`, `Marketing`, `Maintenance`, etc. Each of these systems might contain one or several class, use case or activity diagrams. These diagrams may or may not have common elements, like the class `Airplane` appearing in class diagrams in both the `Logistics` and the `Maintenance` systems.

Once you have your project and system, you can get started working on a diagram.

<h2 align="center">
  <b>Class Diagrams</b>
</h2>

<h3>Nodes</h3>
<b>Creating and Editing</b>
<p>Nodes are the buidling blocks of class diagrams. By right-clicking your modelling area, you have the option to create a new node representing a <b>Class</b>, <b>Enum</b>, <b>Signal</b> or <b>Application</b>. You will have to name your node. If you are creating an <b>Enum</b>, you can also use the create menu to specify your literals. By right clicking a node, you then have the option to edit it. This allows you to:</p>
<ul>
  <li>rename the node</li>
  <li>edit attributes and methods for classes</li>
  <li>edit literals for enums</li>
</ul>
<b>Importing Nodes from Other Systems</b>
<p>In the class diagram, you have the option to import nodes from other diagrams, and even from other systems within your project. The origin system is marked when it is different than the current one. Sometimes you are importing a node that in other diagrams has some preexisting edges connecting it to nodes that already exist in your current diagram. If that happens, these edges will be added to your current diagram as well.</p>
<b>Removing and Deleting</b>
<p>You have two options in terms of removing a node:</p>
<ul>
  <li><b>Remove from Diagram</b>: only deletes the node and its edges in the current diagram.</li>
  <li><b>Delete Completely</b>: removes the node and its edges in any diagram in your project.</li>
</ul>
<p>This distinction is important when you have imported a node to multiple systems, and allows you to decide whether you want to delete it only from the current diagram or from everywhere in your project.</p>

<br/>

<h3>Edges</h3>
<b>Creating and Editing</b>
<p>You can create an edge by right-clicking on a source node and then selecting the <b>Connect</b> option, then selecting the target node. You can create different types of edges: <b>Association</b>, <b>Generalization</b>, <b>Composition</b>, <b>Dependency</b>. In the edge creation menu, you have the option of setting a label, as well as any eventual source/target label or multiplicity. You can right-click an edge and then select <b>Edit</b> in order to change all of these properties.</p>

<p>You may be in the situation of having to reposition edges in order to avoid overlaps that can make the label, multiplicityes or edge type indistinguishable. You can drag the circular endpoints to reposition the edge. You can also add bending points by double-clicking a specific spot on the edge. These points are also draggable. If you wish to delete a bending point, you can do so by right-clicking it.</p>

<b>Removing and Deleting</b>
<p>When removing an edge, you have similar options as for a node:</p>
<ul>
  <li><b>Remove from Diagram</b>: only removes the edge from the current diagram.</li>
  <li><b>Delete Completely</b>: removes the edge from any diagram in your project.</li>
</ul>
<p>Once again, this distinction is important when you have imported the same nodes to multiple systems, which can lead to imported edges that reoccur in multiple diagrams.</p>


<h2 align="center">
  <b>Use Case Diagrams</b>
</h2>

<h3>Nodes</h3>
Similarly to the class diagram, you can right-click anywhere to have the option to <b>Create a Node</b>. You can then select between several types:
<ul>
  <li><b>Actor</b> nodes</li>
  <li><b>Use Case</b> nodes</li>
  <li>One <b>System Boundary</b> per diagram. After adding it, you have the option to add other nodes to the system by right-clicking them. This means that their position respective to the system boundary is fixed. If you move the system boundary, the added nodes will move with it. You can also remove nodes from the system in the same way.</li>
</ul>

> ☝️ <b>Important note</b>: Do not delete the system boundary if some nodes are still added to it, as this is currently not handled well and the diagram will be lost.

<h3>Edges</h3>
<p>To create an edge, right-click on a source node and select <b>Connect</b>. Then select between the following edge types: <b>Interaction</b>, <b>Extension</b>, <b>Inclusion</b>, and <b>Generalization</b>.</p>

> ☝️ Node imports are not yet available in Use Case diagrams. Because of this, there is no distinction between deletion and removal for nodes and edges, you only have the <b>Delete</b> option.
