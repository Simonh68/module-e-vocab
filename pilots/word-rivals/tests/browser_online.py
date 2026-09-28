"""Two independent Chromium contexts against an actual local HTTP/SSE server.
Not a public deployment, not a test on physical phones or separate Internet links.
"""
import json, os, socket, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa-online';OUT.mkdir(exist_ok=True)
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
server=subprocess.Popen(['node','server.cjs'],cwd=ROOT,env={**os.environ,'PORT':str(port)},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
base=f'http://127.0.0.1:{port}'
corpus=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify(require('./content.cjs')))"],cwd=ROOT,text=True))
answers={w['context']:[w['id']] for w in corpus['words']}
answers.update({p['clue']:p['ids'] for p in corpus['pairs']})
errors=[];results=[];blocked=None
try:
    for _ in range(50):
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=.2):break
        except OSError:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        contexts=[browser.new_context(viewport={'width':1280,'height':1000}),browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)]
        pages=[c.new_page() for c in contexts]
        for page in pages:
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.set_default_timeout(8000)
        pages[0].goto(base,wait_until='domcontentloaded')
        pages[0].locator('#create').click();pages[0].locator('.code').wait_for()
        code=pages[0].evaluate('room.code');assert len(code)==12
        pages[1].goto(f'{base}/?room={code}',wait_until='domcontentloaded')
        pages[1].locator('#joinForm button').click()
        pages[0].wait_for_function('room.online.length===2 && room.online.every(Boolean)')
        pages[0].locator('#start').click()
        for page in pages:page.wait_for_function('room.game?.phase==="choose"')
        assert pages[0].evaluate('room.you')==0 and pages[1].evaluate('room.you')==1
        pages[0].screenshot(path=str(OUT/'online-desktop.png'),full_page=True)
        pages[1].screenshot(path=str(OUT/'online-mobile.png'),full_page=True)
        for page in pages:assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        for turn in range(12):
            state=pages[0].evaluate('room.game');actor=state['active'];page=pages[actor]
            mission=state['missions'][0]
            page.locator(f'[data-mission="{mission["id"]}"]').click()
            page.wait_for_function('room.game.phase==="answer"')
            for word in answers[mission['clue']]:page.locator(f'[data-word="{word}"]').click()
            time.sleep(.1);page.locator('#submit').click()
            for view in pages:view.wait_for_function('(turn)=>room.game?.turn===turn+1',arg=turn)
            if turn==3:
                # Actual page reload recovers the same seat and server-side game state.
                pages[1].reload(wait_until='domcontentloaded')
                pages[1].wait_for_function('room?.you===1 && room.game?.turn===4')
                for view in pages:view.wait_for_function('room.online.every(Boolean)')
            time.sleep(.1)
            next_page=pages[1-actor];next_page.locator('#continue').click()
            target='over' if turn==11 else 'choose'
            for view in pages:view.wait_for_function('(phase)=>room.game?.phase===phase',arg=target)
        assert pages[0].evaluate('room.game.moves')==[6,6]
        assert pages[0].evaluate('room.game.scores')==pages[1].evaluate('room.game.scores')
        for i,page in enumerate(pages):page.screenshot(path=str(OUT/f'online-result-{i}.png'),full_page=True)
        old=pages[0].evaluate('room.matchId');starter=pages[0].evaluate('room.game.starter')
        time.sleep(.15);pages[0].locator('#rematch').click();assert pages[0].evaluate('room.game.phase')=='over'
        time.sleep(.15);pages[1].locator('#rematch').click()
        for page in pages:page.wait_for_function('(id)=>room.matchId!==id',arg=old)
        assert pages[0].evaluate('room.game.starter')==1-starter
        # Reject stale room snapshots on the client, not only stale game versions.
        assert pages[0].evaluate('''()=>{const rev=room.revision;setState({...room,revision:rev-1,online:[false,false]});return room.revision===rev&&room.online.every(Boolean);}''')
        assert not errors,errors
        results=['Two separate browser sessions joined one room through HTTP/SSE', 'Twelve turns completed with identical scores on both clients', 'Mobile 390 px and desktop 1280 px: no horizontal overflow', 'Mid-match reload retained player seat and game state', 'Rematch required both players and alternated starter', 'Stale client snapshot rejected', 'No captured JavaScript page errors']
        browser.close()
except Exception as exc:
    blocked=str(exc)
finally:
    server.terminate()
    try:server.wait(timeout=6)
    except subprocess.TimeoutExpired:server.kill();server.wait()
report={'method':'Actual local HTTP/SSE server, two Chromium contexts, one container/network','public_deployment':False,'physical_devices':False,'results':results,'pageErrors':errors,'blocked_or_failed':blocked}
(OUT/'browser-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))

if blocked: raise SystemExit(1)
