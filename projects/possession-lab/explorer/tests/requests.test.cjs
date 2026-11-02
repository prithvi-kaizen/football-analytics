const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createFixtureLoader} = require('../web/requests.js');

test('concurrent and repeated example requests share one fetch', async () => {
  let calls = 0, finish;
  const load = createFixtureLoader({fetchImpl: () => {
    calls++;
    return new Promise(resolve => {finish = () => resolve({ok:true,json:async()=>({frames:3025})});});
  }});
  const a = load('default'), b = load('default');
  assert.equal(calls, 1);
  finish();
  assert.deepEqual(await a, await b);
  assert.equal((await load('default')).frames,3025);
  assert.equal(calls,1);
});

test('a failed request can be retried successfully', async () => {
  let calls=0;
  const load=createFixtureLoader({fetchImpl:async()=> {
    calls++;
    return calls===1?{ok:false,status:503}:{ok:true,json:async()=>({truth:null})};
  }});
  await assert.rejects(load('public1'),/503/);
  assert.deepEqual(await load('public1'),{truth:null});
  assert.equal(calls,2);
});

test('a stalled fetch aborts with a useful error and remains retryable', async () => {
  let calls=0;
  const load=createFixtureLoader({timeoutMs:20,fetchImpl:(_url,{signal})=> {
    calls++;
    if(calls>1)return Promise.resolve({ok:true,json:async()=>({ready:true})});
    return new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new Error('aborted')),{once:true}));
  }});
  await assert.rejects(load('stationary_live'),/took too long/);
  assert.deepEqual(await load('stationary_live'),{ready:true});
});

test('fixture names cannot turn into paths or external requests',async()=>{
  let calls=0;
  const load=createFixtureLoader({fetchImpl:()=>{calls++;throw new Error('unexpected fetch');}});
  await assert.rejects(load('../private'),/Unknown example/);
  await assert.rejects(load('https://example.com'),/Unknown example/);
  assert.equal(calls,0);
});
