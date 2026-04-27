const fs = require('fs');
const crypto = require('crypto');

function generateUUID(seed) {
  const hash = crypto.createHash('sha256').update(seed).digest('hex');
  return hash.substring(0, 8) + '-' +
         hash.substring(8, 12) + '-' +
         hash.substring(12, 16) + '-' +
         hash.substring(16, 20) + '-' +
         hash.substring(20, 32);
}

const rawData = fs.readFileSync('docs/bol_shop_example.json');
const data = JSON.parse(rawData);

const firstSystem = data.systems[0];
const systemId = firstSystem.id;

const diagram = {
  id: 'c2d1e8d4-6b3a-55b7-9d2f-0d7c8d3e4f91',
  type: 'classes',
  name: 'Bol Shop Structure',
  description: 'Imported structure overview',
  system: systemId,
  nodes: [],
  edges: []
};

const classifiers = firstSystem.classifiers || [];
const relations = firstSystem.relations || [];

classifiers.forEach((classifier, index) => {
  const nodeId = generateUUID('node-' + classifier.id);
  const x = (index % 5) * 250;
  const y = Math.floor(index / 5) * 150;
  
  diagram.nodes.push({
    id: nodeId,
    classifier: classifier.id,
    position: { x, y }
  });
});

relations.forEach((relation, index) => {
  const edgeId = generateUUID('edge-' + (relation.id || index));
  diagram.edges.push({
    id: edgeId,
    relation: relation.id,
    sourceNode: generateUUID('node-' + relation.source),
    targetNode: generateUUID('node-' + relation.target)
  });
});

console.log(JSON.stringify(diagram, null, 2));
