import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

class Element {
  constructor(tag){this.tag=tag;this.children=[];this.textContent='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=[...children];}
  setAttribute(name,value){this[name]=value;}
}
const container=new Element('div');
const context=vm.createContext({window:{},URL,document:{
  addEventListener(){},createElement:tag=>new Element(tag),getElementById:()=>container,
}});
vm.runInContext(await readFile('web/js/financial-display.js','utf8'),context);
vm.runInContext(await readFile('web/js/company.js','utf8'),context);
const flatten=node=>[node,...node.children.flatMap(flatten)];

test('reviewed AI renders quoted evidence as text with physical PDF page links',()=>{
  context.rows=[{section:'business_brief',title:'Reviewed title',insight_text:'Reviewed text',
    confidence:'low',model_name:'test-only:1',source_document_id:'source',
    evidence:[{source_url:'https://example.com/report.pdf',page:3,quote:'<script>untrusted source text</script>'}]}];
  vm.runInContext('renderInsights(rows,new Map())',context);
  const nodes=flatten(container);
  assert.equal(nodes.find(n=>n.tag==='blockquote').textContent,'<script>untrusted source text</script>');
  assert.ok(nodes.some(n=>n.textContent.includes('Reviewed AI interpretation')));
  assert.ok(nodes.some(n=>n.textContent.includes('model self-assessment')));
  assert.equal(nodes.find(n=>n.tag==='a').href,'https://example.com/report.pdf#page=3');
  assert.equal(nodes.filter(n=>n.tag==='script').length,0);
});

test('missing AI outputs remain explicit unavailable state',()=>{
  vm.runInContext('renderInsights([],new Map())',context);
  assert.ok(flatten(container).some(n=>n.textContent.includes('No validated source-backed AI insights')));
});
