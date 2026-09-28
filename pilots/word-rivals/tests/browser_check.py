"""Manual-run Chromium integration checks; Playwright is a development-only tool."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa'; OUT.mkdir(exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    c=browser.new_context(viewport={'width':1280,'height':1000})
    page=c.new_page(); errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((ROOT/'demo.html').read_text(),wait_until='load')
    page.locator('#localStart').click(); page.locator('[data-mission]').first.wait_for()
    assert page.locator('[data-word]').count()==16
    page.screenshot(path=str(OUT/'desktop-board.png'),full_page=True)
    for turn in range(12):
        mission=page.evaluate('({id:localGame.missions[0].id,targets:localGame.missions[0].targets})')
        page.locator(f'[data-mission="{mission["id"]}"]').click()
        for target in mission['targets']:page.locator(f'[data-word="{target}"]').click()
        page.locator('#submit').click();page.locator('#continue').wait_for()
        page.locator('#continue').click()
    page.locator('#rematch').wait_for()
    assert page.evaluate('room.game.moves')==[6,6]
    page.locator('#reviewToggle').click()
    assert page.locator('#reviewList .answerword').count()==16
    page.screenshot(path=str(OUT/'result-review.png'),full_page=True)
    old_starter=page.evaluate('localGame.starter')
    page.locator('#rematch').click()
    assert page.evaluate('localGame.starter')==1-old_starter
    results.append('Standalone HTML rendering: 12 UI turns, feedback, end, review, rematch and alternating starter PASS')
    assert errors==[], errors
    page.locator('#rulesBtn').click();page.keyboard.press('Escape')
    assert page.locator('#modal').get_attribute('class')=='hidden'
    mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    m=mobile.new_page();m.set_content((ROOT/'demo.html').read_text(),wait_until='load');m.locator('#localStart').click()
    assert m.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'horizontal overflow'
    m.screenshot(path=str(OUT/'mobile-board.png'),full_page=True)
    m.locator('[data-mission]').first.click();m.screenshot(path=str(OUT/'mobile-turn.png'),full_page=True)
    assert m.evaluate('document.documentElement.scrollWidth<=innerWidth')
    results.append('390 px touch emulation: no horizontal overflow; mission and board reachable PASS')
    results.append('Network navigation blocked by browser administrator policy; no browser-to-server or physical-phone test claimed')
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps({'checks':results,'pageErrors':errors,'method':'Authored local HTML loaded with set_content, not URL navigation'},ensure_ascii=False,indent=2))
print('\n'.join(results))
