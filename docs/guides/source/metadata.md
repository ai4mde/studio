<p align="center">
    <img
        src="https://avatars.githubusercontent.com/u/155311177"
        alt="AI4MDE studio"
        width="64"
    />
</p>

<h1 align="center">
  AI4MDE &middot; <b>Metadata Model</b>
</h1>

## 1. Management
### Project
A project is the root of the metadata model. A project ecapsulates systems, releases (system versions), diagrams, metadata, user interfaces, and prototypes. A project defines the context of a combination of all other models. In practice, a project is a company/organization.

**Example:** Supermarket
**Definition:** [/api/model/metadata/models.py](../api/model/metadata/models.py)

**Properties:**
- `id`
- `name`
- `description`

### System
A system is a subdivision of a project. A system ecapsulates diagrams, metadata, user interfaces, and prototypes. A system defines the context of a combination of these models. In practice, a system is a fragment of a company/organization.

**Example:** Webshop Order System
**Definition:** [/api/model/metadata/models.py](../api/model/metadata/models.py)

**Properties:**
- `id`
- `project`
- `name`
- `description`

### Release
A release is a snapshot of a system in time. It is static and cannot be changed. It expresses the state of a system during a specific period in development.

**Example:** Weather Forecast System v1.6.3
**Definition:** [/api/model/metadata/models.py](../api/model/metadata/models.py)

**Properties:**
- `id`
- `project`
- `system`
- `name`
- `created_at`
- `release_notes`
- Json snapshot of `diagrams`, `metadata` & `interfaces`


## 2. Diagrams
### Diagram
A diagram represents a UML diagram. Currently supported diagram types are: `Class`, `Use Case` & `Activity`. A diagram is a set of `nodes`and `edges`, which are the vertex and edge elements of the graph. A diagram falls under a system, and describes the technical details of the system. More information on UML can be found on their website: [https://www.uml.org/](https://www.uml.org/)

**Example:** UML Activity Diagram
**Definition:** [/api/model/diagram/models.py](../api/model/diagram/models.py)

**Properties:**
- `id`
- `name`
- `description`
- `type`
- `system`


### Node
A node is a vertex in a diagram. It can represent many things, depending on the type. What a node type represents can be read in the UML documentation. Currently, the following types are implemented:

*Class Diagram:*
- `Class`
- `Enum`

*Use Case Diagram:*
- `Use Case`
- `Actor`

*Activity Diagram:*
- `Action`
- `Initial`
- `Final`
- `Fork`
- `Join`
- `Decision`
- `Merge`

**Example:** Payment (Class) / Customer (Actor)
**Definition:** [/api/model/diagram/models.py](../api/model/diagram/models.py)

**Properties:**
- `id`
- `diagram`
- `cls` (pointer to a `classifier`, which contains the actual information of the node)
- `data` (`x` and `y` coordinates in the diagram)

The actual information of a node (`classifier`)  has been split from the positional coordinates (`node`) such that nodes from different diagrams can point to the same information, preventing redundancy in the database.

### Edge
An edge is a line in a diagram. It can represent many things, depending on the type. What an edge type represents can be read in the UML documentation. Currently, the following types are implemented:

*Class Diagram:*
- `Association`
- `Generalization`
- `Composition`
- `Dependency`

*Use Case Diagram:*
- `Interaction`
- `Extension`
- `Inclusion`

*Activity Diagram:*
- `Connection`

**Example:** Interaction between Manager (Actor) and Order Product (Use Case)
**Definition:** [/api/model/diagram/models.py](../api/model/diagram/models.py)

**Properties:**
- `id`
- `diagram`
- `rel` (pointer to a `relation`, which contains the actual information of the edge)
- `data` (`type` of the edge)

The actual information of an edge (`relation`)  has been split from the line (`edge`) such that edges from different diagrams can point to the same information, preventing redundancy in the database.

## 3. Metadata
### Classifier
A classifier contains the data of a node in a diagram. It's data property is a JSON blob that can represent many things, depending on the type of the corresponding node.

**Definition:** [/api/model/metadata/models.py](../api/model/metadata/models.py)

**Properties:**
- `id`
- `system`
- `data` (JSON blob)

### Relation
A relation contains the data of an edge in a diagram. It's data property is a JSON blob that can represent many things, depending on the type of the corresponding edge.

**Definition:** [/api/model/metadata/models.py](../api/model/metadata/models.py)

**Properties:**
- `id`
- `system`
- `data` (JSON blob)
- `target` (Classifier)
- `source` (Classifier)

### User Interface
A user interface is a component in a system that an actor can interact with. It is a set of pages, categories and styling, which are all stored in a JSON blob.

**Example:** Manager component in a web shop
**Definition:** [/api/model/metadata/models.py](../api/model/diagram/models.py)

**Properties:**
- `id`
- `name`
- `description`
- `actor`
- `system`
- `data` (JSON blob containing pages, categories and styling)

The following models are not directly stored in the database, but are specified in the `data` JSON blob of a User Interface:

- **Category**
A category is a descriptor for a page, used to organize pages in the navigation menu of a prototype. It has the following properties:
    - `id`
    - `name`

- **Page**
A page is a set of section components, used to generate web pages that an actor can interact with in a prototype. It has the following properties:
    - `id`
    - `name`
    - `category`
    - `sections`

- **Section Component**
A section component is a component in a page that directly acts on a class. Section components are used to build pages in a prototype. A section component has the following properties:
    - `id`
    - `name`
    - `class`
    - `attributes` (list of attributes of the `class` which are used in the section component)
    - `operations` (Create/Update/Delete)
    - `custom operations`

- **Styling**
Styling describes the appearance of a user interface. It is used to generate .css files in a prototype. A styling object has the following properties:
    - `radius`
    - `text color`
    - `accent color`
    - `background color`
    - `style` (Basic/Modern/Abstract)

## 4. Prototypes
### Prototype
A prototype is a basic software implementation of a system, which can be launched and interacted with. A prototype object is used to generate an actual software implementation in the `prototypes` Docker container.

**Example:** To Do application prototype
**Definition:** [/api/model/generator/models.py](../api/model/generator/models.py)

**Properties:**
- `id`
- `name`
- `description`
- `system`
- `metadata` (a JSON snapshot of the diagrams & user interfaces during generation)
- `database hash` (a hash of class diagrams and user interface names in a system, used for reusing databases across multiple prototypes)

## 5. Prose
### Pipeline

TODO