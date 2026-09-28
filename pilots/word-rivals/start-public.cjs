'use strict';
// Requires a managed HTTPS ingress; never trust X-Forwarded-* from arbitrary clients.
const {makeServer}=require('./server.cjs');
const publicOrigin=process.env.PUBLIC_ORIGIN || process.env.RENDER_EXTERNAL_URL;
const {server,stop}=makeServer({production:true,publicOrigin});
const port=Number(process.env.PORT || 10000);
if (!Number.isInteger(port) || port<1 || port>65535) throw new Error('Invalid PORT');
server.listen(port,'0.0.0.0',()=>console.log('WORD RIVALS 0.2.0: isolated HTTPS pilot backend ready'));
for (const signal of ['SIGTERM','SIGINT']) process.once(signal,()=>{
  stop();
  setTimeout(()=>{server.closeAllConnections();process.exit(0);},5000).unref();
});
