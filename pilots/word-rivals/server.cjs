'use strict';
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const core=require('./core.cjs');
const {createPolicy,readJSON:read}=require('./hosting.cjs');
const IDLE_MS=30*60*1000,MAX_MS=2*60*60*1000,MAX_PLAYERS=6,ALPHABET='0123456789abc';
function roomCode(rooms){let code;do{code='';for(let i=0;i<6;i++)code+=ALPHABET[crypto.randomInt(ALPHABET.length)];}while(rooms.has(code));return code;}
function makeServer(options={}){
 const policy=createPolicy(options),rooms=new Map(),idleMs=options.idleMs||IDLE_MS,maxMs=options.maxMs||MAX_MS;
 const token=()=>crypto.randomBytes(24).toString('base64url'),seed=()=>crypto.randomBytes(4).readUInt32BE();
 function send(s,m){if(!s.destroyed&&!s.writableEnded)try{s.write(m)}catch{}}
 function clean(){const now=Date.now();for(const [code,r] of rooms)if(now-r.touched>idleMs||now-r.created>maxMs){rooms.delete(code);for(const p of r.players)for(const s of p.streams){send(s,'event: expired\ndata: {}\n\n');s.end();}}}
 const cleanup=setInterval(clean,60000);cleanup.unref();
 const cookies=req=>Object.fromEntries((req.headers.cookie||'').split(';').map(s=>s.trim().split('=')));
 const getPlayer=(req,r)=>r.players.findIndex(p=>p.token===cookies(req)['wr_'+r.code]);
 const snapshot=(r,you)=>({revision:r.revision,code:r.code,you,status:r.status,matchId:r.matchId,online:r.players.map(p=>p.streams.size>0),players:r.players.length,maxPlayers:MAX_PLAYERS,game:r.game?core.publicState(r.game):null,expiresAt:Math.min(r.created+maxMs,r.touched+idleMs)});
 function broadcast(r){r.revision++;r.players.forEach((p,i)=>{const msg='data: '+JSON.stringify(snapshot(r,i))+'\n\n';for(const s of p.streams)send(s,msg);});}
 function json(res,status,body){res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(body));}
 function cookie(res,r,p,req){res.setHeader('Set-Cookie',`wr_${r.code}=${p.token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=7200${policy.production||req.socket.encrypted?'; Secure':''}`);}
 const server=http.createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('X-Frame-Options','DENY');res.setHeader('Permissions-Policy','microphone=(), camera=(), geolocation=()');
  try{
   if(!policy.guard(req,res))return;clean();const u=new URL(req.url,'http://local');
   if(req.method==='POST'&&req.headers.origin&&req.headers.origin!==`http://${req.headers.host}`&&req.headers.origin!==`https://${req.headers.host}`)return json(res,403,{error:'Cross-origin request refused'});
   if(req.method==='GET'&&['/','/index.html','/demo.html'].includes(u.pathname)){const file=path.join(__dirname,u.pathname==='/demo.html'?'demo.html':'online.html');if(!fs.existsSync(file))return json(res,404,{error:'Build required'});res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return fs.createReadStream(file).pipe(res);}
   if(req.method==='GET'&&u.pathname==='/health')return json(res,200,{ok:true,version:'1.0.0',mode:'band3-room-quiz'});
   if(req.method==='POST'&&u.pathname==='/api/create'){await read(req);const p={token:token(),streams:new Set(),last:0},now=Date.now(),code=roomCode(rooms);const r={code,revision:0,players:[p],created:now,touched:now,status:'lobby',matchId:null,game:null};rooms.set(code,r);cookie(res,r,p,req);return json(res,201,snapshot(r,0));}
   if(req.method==='POST'&&u.pathname==='/api/join'){
    const body=await read(req),code=String(body.code||'').trim().toLowerCase();if(!/^[0-9abc]{6}$/.test(code))return json(res,400,{error:'Use a 6-character room code with 0-9, a, b or c'});
    const r=rooms.get(code);if(!r)return json(res,404,{error:'Room not found or expired'});let you=getPlayer(req,r);if(you>=0)return json(res,200,snapshot(r,you));
    if(r.status!=='lobby')return json(res,409,{error:'This match has already started'});if(r.players.length>=MAX_PLAYERS)return json(res,409,{error:'This room is full'});
    const p={token:token(),streams:new Set(),last:0};r.players.push(p);r.touched=Date.now();cookie(res,r,p,req);broadcast(r);return json(res,200,snapshot(r,r.players.length-1));
   }
   const code=String(u.searchParams.get('room')||'').toLowerCase(),r=rooms.get(code);if(!r)return json(res,404,{error:'Room not found or expired'});const you=getPlayer(req,r);if(you<0)return json(res,403,{error:'Join this room first'});
   if(req.method==='GET'&&u.pathname==='/api/state')return json(res,200,snapshot(r,you));
   if(req.method==='GET'&&u.pathname==='/events'){const p=r.players[you];res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-store','Connection':'keep-alive','X-Accel-Buffering':'no'});res.write('retry: 1500\n\n');p.streams.add(res);broadcast(r);const beat=setInterval(()=>send(res,': ping\n\n'),15000);beat.unref();req.on('close',()=>{clearInterval(beat);p.streams.delete(res);broadcast(r)});return;}
   if(req.method==='POST'&&u.pathname==='/api/action'){
    const a=await read(req),p=r.players[you],now=Date.now();if(now-p.last<80)return json(res,429,{error:'Please wait a moment'});p.last=now;
    if(a.type==='start'){if(you!==0||r.status!=='lobby'||r.players.length<2)return json(res,409,{error:'Player 1 can start when at least two players have joined'});r.game=core.createGame(seed(),r.players.length,0);r.matchId=token();r.status='playing';}
    else{if(r.status!=='playing'||!r.game)throw new Error('The game has not started');if(a.matchId!==r.matchId)return json(res,409,{error:'Stale match'});core.apply(r.game,you,a);}
    r.touched=now;broadcast(r);return json(res,200,snapshot(r,you));
   }
   return json(res,404,{error:'Not found'});
  }catch(e){if(!res.destroyed&&!res.writableEnded)return json(res,e.status||400,{error:e instanceof SyntaxError?'Invalid JSON':e.message});}
 });
 server.requestTimeout=15000;server.headersTimeout=10000;
 server.on('close',()=>{clearInterval(cleanup);for(const r of rooms.values())for(const p of r.players)for(const s of p.streams)s.end();rooms.clear();});
 function stop(){for(const r of rooms.values())for(const p of r.players)for(const s of p.streams){send(s,'event: restarting\ndata: {}\n\n');s.end();}server.close();}
 return{server,rooms,clean,stop};
}
if(require.main===module){const port=Number(process.env.PORT||8787);makeServer().server.listen(port,process.env.HOST||'127.0.0.1',()=>console.log('Band III Room Quiz ready'));}
module.exports={makeServer,roomCode,MAX_PLAYERS};
