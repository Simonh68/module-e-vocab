'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');

test('inline Battle Room script parses successfully',()=>{
  const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
  const scripts=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]);
  assert.ok(scripts.length>0);
  for(const script of scripts)assert.doesNotThrow(()=>new Function(script));
});

test('room code input uses a real newline and digit filter',()=>{
  const html=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
  assert.equal(html.includes(');\\nconst q='),false);
  assert.ok(html.includes("replace(/\\D/g,'').slice(0,6)"));
});
