'use strict';
// Dependency-free single-process pilot. Public hosting requires hosting.cjs and explicit HTTPS configuration.
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const core=require('./core.cjs');
const {createPolicy,readJSON:read}=require('./hosting.cjs');
const IDLE_MS=30*60*1000, MAX_MS=2*60*60*1000;
function makeServer(options={}){
 const policy=createPolicy(options);
 const rooms=new Map(),idleMs=options.idleMs||IDLE_MS,maxMs=options.maxMs||MAX_MS;
 const token=()=>crypto.randomBytes(24).toString('base64url');
 const seed=()=>crypto.randomBytes(4).readUInt32BE();
 function send(stream,message){if(stream.destroyed||stream.writableEnded)return;if(stream.writableLength>262144){stream.destroy();return;}try{stream.write(message);}catch{stream.destroy();}}
 function clean(){const now=Date.now();for(const [code,r]of rooms)if(now-r.touched>idleMs||now-r.created>maxMs){rooms.delete(code);for(const p of r.players){for(const s of p.streams){send(s,'event: expired\ndata: {}\n\n');s.end();}p.streams.clear();}}}
 const cleanup=setInterval(clean,Math.min(60000,idleMs));cleanup.unref();
 const cookies=req=>Object.fromEntries((req.headers.cookie||'').split(';').map(s=>s.trim().split('=')));
 const getPlayer=(req,r)=>r.players.findIndex(p=>p.token===cookies(req)[`wr_${r.code}`]);
 const snapshot=(r,you)=>({revision:r.revision,code:r.code,you,status:r.status,matchId:r.matchId,online:r.players.map(p=>p.streams.size>0),players:r.players.length,rematch:r.players.map(p=>p.rematch),game:r.game?core.publicState(r.game):null,expiresAt:Math.min(r.created+maxMs,r.touched+idleMs)});
 function broadcast(r){if(!rooms.has(r.code))return;r.revision++;r.players.forEach((p,i)=>{const msg=`data: ${JSON.stringify(snapshot(r,i))}\n\n`;for(const s of p.streams)send(s,msg);});}
 function json(res,status,body){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(body));}

 function cookie(res,r,p,req){res.setHeader('Set-Cookie',`wr_${r.code}=${p.token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=7200${policy.production||req.socket.encrypted?'; Secure':''}`);}
 const server=http.createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('X-Frame-Options','DENY');res.setHeader('Permissions-Policy','microphone=(), camera=(), geolocation=()');
  res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'");
  try{
   if(!policy.guard(req,res))return;
   clean();const u=new URL(req.url,'http://local');
   if(req.method==='POST'&&req.headers.origin&&req.headers.origin!==`http://${req.headers.host}`&&req.headers.origin!==`https://${req.headers.host}`)return json(res,403,{error:'Cross-origin request refused'});
   if(req.method==='GET'&&['/','/index.html','/demo.html'].includes(u.pathname)){
    const f=u.pathname==='/demo.html'?'demo.html':'online.html';const file=path.join(__dirname,f);
    if(!fs.existsSync(file))return json(res,404,{error:'Run npm run build before starting the pilot'});
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return fs.createReadStream(file).pipe(res);
   }
   if(req.method==='GET'&&u.pathname==='/health')return json(res,200,{ok:true,version:'0.2.0',mode:'pilot'});
   if(req.method==='POST'&&u.pathname==='/api/create'){
    await read(req);if(rooms.size>=(options.maxRooms??100))return json(res,503,{error:'Pilot room limit reached'});
    let code;do{code=crypto.randomBytes(6).toString('hex').toUpperCase();}while(rooms.has(code));
    const p={token:token(),streams:new Set(),rematch:false,last:0},now=Date.now();
    const r={code,revision:0,players:[p],created:now,touched:now,status:'lobby',matchId:null,game:null,starter:seed()%2};rooms.set(code,r);cookie(res,r,p,req);return json(res,201,snapshot(r,0));
   }
   if(req.method==='POST'&&u.pathname==='/api/join'){
    const body=await read(req),code=String(body.code||'').trim().toUpperCase();if(!/^[0-9A-F]{12}$/.test(code))return json(res,400,{error:'Invalid room code'});
    const r=rooms.get(code);if(!r)return json(res,404,{error:'Room not found or expired'});
    let you=getPlayer(req,r);if(you>=0)return json(res,200,snapshot(r,you));
    if(r.players.length>=2)return json(res,409,{error:'This room already has two players'});
    const p={token:token(),streams:new Set(),rematch:false,last:0};r.players.push(p);r.touched=Date.now();cookie(res,r,p,req);broadcast(r);return json(res,200,snapshot(r,1));
   }
   const code=(u.searchParams.get('room')||'').toUpperCase(),r=rooms.get(code);
   if(!r)return json(res,404,{error:'Room not found or expired'});
   const you=getPlayer(req,r);if(you<0)return json(res,403,{error:'Join this room first'});
   if(req.method==='GET'&&u.pathname==='/api/state')return json(res,200,snapshot(r,you));
   if(req.method==='GET'&&u.pathname==='/events'){
    const p=r.players[you];if(p.streams.size>=3)return json(res,429,{error:'Too many open windows'});
    res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-store','Connection':'keep-alive','X-Accel-Buffering':'no'});res.write('retry: 1500\n\n');p.streams.add(res);broadcast(r);
    res.on('error',()=>res.destroy());const beat=setInterval(()=>send(res,': ping\n\n'),15000);beat.unref();req.on('close',()=>{clearInterval(beat);p.streams.delete(res);broadcast(r);});return;
   }
   if(req.method==='POST'&&u.pathname==='/api/action'){
    const a=await read(req),p=r.players[you],now=Date.now();if(!a||typeof a!=='object'||Array.isArray(a))return json(res,400,{error:'Invalid action'});if(now-p.last<80)return json(res,429,{error:'Please wait a moment'});p.last=now;
    if(a.type==='start'){
     if(you!==0||r.status!=='lobby'||r.players.length!==2||r.players.some(p=>!p.streams.size))return json(res,409,{error:'Both players must be connected'});
     r.game=core.createGame(seed(),r.starter);r.matchId=token();r.status='playing';
    }else if(a.type==='rematch'){
     if(a.matchId!==r.matchId)return json(res,409,{error:'Stale match'});
     if(r.game?.phase!=='over')return json(res,409,{error:'Finish the game first'});
     p.rematch=true;if(r.players.every(p=>p.rematch)&&r.players.every(p=>p.streams.size)){r.starter=1-r.starter;r.matchId=token();r.game=core.createGame(seed(),r.starter);for(const p of r.players)p.rematch=false;}
    }else{
     if(a.matchId!==r.matchId)return json(res,409,{error:'Stale match'});
     if(r.status!=='playing'||!r.game)throw new Error('The game has not started');
     if(r.players.some(p=>!p.streams.size))return json(res,409,{error:'Waiting for the other player to reconnect'});
     core.apply(r.game,you,a);
    }
    r.touched=now;broadcast(r);return json(res,200,snapshot(r,you));
   }
   return json(res,404,{error:'Not found'});
  }catch(e){if(!res.destroyed&&!res.writableEnded)return json(res,e.status||400,{error:e instanceof SyntaxError?'Invalid JSON':e.message});}
 });
 server.maxConnections=1024;
 server.requestTimeout=15000;server.headersTimeout=10000;
 server.on('close',()=>{clearInterval(cleanup);const closing=[...rooms.values()];rooms.clear();for(const r of closing)for(const p of r.players){for(const s of p.streams)s.end();p.streams.clear();}});
 function stop(){for(const r of rooms.values())for(const p of r.players)for(const s of p.streams){send(s,'event: restarting\ndata: {}\n\n');s.end();}server.close();server.closeIdleConnections();}
 return{server,rooms,clean,stop};
}
if(require.main===module){const host=process.env.HOST||'127.0.0.1',port=Number(process.env.PORT||8787);makeServer().server.listen(port,host,()=>console.log(`WORD RIVALS pilot: http://${host}:${port} (no public deployment)`));}
module.exports={makeServer};
