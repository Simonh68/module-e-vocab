'use strict';
// Public-hosting boundary for the isolated pilot. No IPs, identities, or request logs.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const BODY_LIMIT = 2048;
class RequestError extends Error {
  constructor(message, status = 400) { super(message); this.status = status; }
}
function fail(res, status, message) {
  res.writeHead(status, {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});
  res.end(JSON.stringify({error:message}));
  return false;
}
function createPolicy(options = {}) {
  const production = options.production === true;
  let origin = null;
  if (production) {
    let u;
    try { u = new URL(options.publicOrigin); } catch { throw new Error('PUBLIC_ORIGIN or RENDER_EXTERNAL_URL is required for public hosting'); }
    if (u.protocol !== 'https:' || u.username || u.password || u.search || u.hash || u.pathname !== '/') {
      throw new Error('Public origin must be an HTTPS origin without a path or credentials');
    }
    origin = u.origin;
  }
  const cap = options.createLimit ?? 60, joinCap = options.joinLimit ?? 240;
  const counters = new Map();
  function admit(key, limit) {
    const minute = Math.floor(Date.now()/60000);
    let c = counters.get(key);
    if (!c || c.minute !== minute) { c = {minute,count:0}; counters.set(key,c); }
    return ++c.count <= limit;
  }
  const policies = {};
  for (const file of ['online.html','demo.html']) {
    const full = path.join(__dirname,file);
    const html = fs.existsSync(full) ? fs.readFileSync(full,'utf8') : '';
    const hashes = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
      .map(m=>`'sha256-${crypto.createHash('sha256').update(m[1]).digest('base64')}'`).join(' ');
    policies[file] = `default-src 'self'; script-src 'self' ${hashes}; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'`;
  }
  return {
    production, origin,
    guard(req,res) {
      res.setHeader('Cache-Control','no-store');
      res.setHeader('X-Robots-Tag','noindex, nofollow, noarchive');
      res.setHeader('Referrer-Policy','no-referrer');
      res.setHeader('Content-Security-Policy',policies[req.url?.split('?')[0]==='/demo.html'?'demo.html':'online.html']);
      if (production) res.setHeader('Strict-Transport-Security','max-age=86400');
      const u = new URL(req.url,'http://local');
      if (!['GET','POST'].includes(req.method)) return fail(res,405,'Method not allowed');
      // Health probes expose no room or player information; the edge supplies public TLS.
      if (production && u.pathname !== '/health' && req.headers.host !== new URL(origin).host) return fail(res,403,'Unexpected host');
      if (req.method === 'POST') {
        if (production && req.headers.origin !== origin) return fail(res,403,'Cross-origin request refused');
        if (req.headers['sec-fetch-site'] === 'cross-site') return fail(res,403,'Cross-origin request refused');
        if (Number(req.headers['content-length'] || 0) > BODY_LIMIT) return fail(res,413,'Request too large');
        if (u.pathname === '/api/create' && !admit('create',cap)) return fail(res,429,'Room creation limit reached; try again later');
        if (u.pathname === '/api/join' && !admit('join',joinCap)) return fail(res,429,'Join limit reached; try again later');
      }
      if (req.method==='GET' && u.pathname==='/robots.txt') {
        res.writeHead(200,{'Content-Type':'text/plain; charset=utf-8'});
        res.end('User-agent: *\nDisallow: /\n'); return false;
      }
      return true;
    }
  };
}
async function readJSON(req) {
  if (!/^application\/json(?:;|$)/i.test(req.headers['content-type'] || '')) throw new RequestError('JSON required',415);
  const chunks = []; let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > BODY_LIMIT) throw new RequestError('Request too large',413);
    chunks.push(chunk);
  }
  let body;
  try { body=JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}'); }
  catch { throw new RequestError('Invalid JSON'); }
  if (!body || Array.isArray(body) || typeof body !== 'object') throw new RequestError('A JSON object is required');
  const route = new URL(req.url,'http://local').pathname;
  const allowed = route==='/api/create'?[]:route==='/api/join'?['code']:['type','version','matchId','missionId','ids'];
  if (Object.keys(body).some(k=>!allowed.includes(k))) throw new RequestError('Unexpected field');
  return body;
}
module.exports={createPolicy,readJSON,RequestError};
