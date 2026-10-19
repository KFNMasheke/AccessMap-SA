import test from 'node:test';
import assert from 'node:assert/strict';
import {distanceMetres, parseSaved, selectFacilities} from '../model.mjs';
const pack = {origin:{x:0,y:0},facilities:[
  {id:'b',name:'West Library',category:'library',x:300,y:400},
  {id:'a',name:'East Clinic',category:'clinic',x:0,y:1000}
]};
test('distance, filtering and nearest ordering', () => {
  assert.equal(distanceMetres(pack.origin,pack.facilities[0]),500);
  assert.deepEqual(selectFacilities(pack).map(f=>f.id),['b','a']);
  assert.deepEqual(selectFacilities(pack,{category:'clinic'}).map(f=>f.id),['a']);
  assert.deepEqual(selectFacilities(pack,{query:' WEST '}).map(f=>f.id),['b']);
  assert.deepEqual(selectFacilities(pack,{savedOnly:true,saved:['a']}).map(f=>f.id),['a']);
});
test('stored bookmarks are validated and deduplicated', () => {
  assert.deepEqual(parseSaved('["a","a","missing",2]',pack.facilities),['a']);
  assert.deepEqual(parseSaved(null,pack.facilities),[]);
  assert.throws(()=>parseSaved('{}',pack.facilities));
  assert.throws(()=>parseSaved('broken',pack.facilities));
  assert.throws(()=>distanceMetres({x:NaN,y:0},pack.facilities[0]));
});
