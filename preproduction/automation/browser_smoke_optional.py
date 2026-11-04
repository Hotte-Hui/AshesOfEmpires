#!/usr/bin/env python3
"""Optional real-browser smoke test. Requires playwright AND installed Chromium.

Not part of default stdlib tests; no package installation occurs here.
Browser has an isolated non-persistent context. This is not a UE5 test.
"""
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(ROOT))
from tools.story_engine_v4 import StoryEngine


def run_route(page,a_choice,m_choice):
    page.locator('#taskList button:not([disabled])').first.click()
    for i in range(5):
        page.get_by_role('button',name='Weiter' if i<4 else 'Gespräch beenden').click()
    for _ in range(2):page.locator('#taskList button:not([disabled])').first.click()
    page.locator('#taskList button:not([disabled])').first.click()
    for n in ('Quadrat','Kreis','Dreieck'):page.get_by_role('button',name=n,exact=True).click()
    page.locator('#taskList button:not([disabled])').first.click()
    page.locator('#taskList button:not([disabled])').first.click()
    page.get_by_role('button',name=('Irina die vollständige Abweichung zeigen' if a_choice=='share_with_irina' else 'Den Hinweis vorerst für dich behalten')).click()
    assert 'MATTHIAS ADLER' in page.locator('#heroName').inner_text().upper()
    for _ in range(2):page.locator('#taskList button:not([disabled])').first.click()
    page.locator('#taskList button:not([disabled])').first.click()
    # Overlay needed: rot=0, x=2, y=-1
    page.get_by_role('button',name='offset_x +').click();page.get_by_role('button',name='offset_x +').click()
    page.get_by_role('button',name='offset_y −').click()
    page.get_by_role('button',name='Pläne vergleichen').click()
    page.locator('#taskList button:not([disabled])').first.click()
    for i in range(5):page.get_by_role('button',name='Weiter' if i<4 else 'Gespräch beenden').click()
    page.locator('#taskList button:not([disabled])').first.click()
    page.get_by_role('button',name=('Eine eigene Kopie des Vermerks sichern' if m_choice=='preserve_evidence' else 'Eine offizielle Stellungnahme verlangen')).click()
    page.get_by_role('button',name='Abschluss ansehen / überspringen').click()
    assert '11/11 Ziele abgeschlossen' in page.locator('#progressText').inner_text()
    assert 'Demo erfolgreich abgeschlossen.' in page.locator('#interactive').inner_text()
    state=page.evaluate('state')
    # Cross-runtime contract: browser export must load in the canonical v4 Python reference.
    assert StoryEngine().load_json(__import__('json').dumps(state))==state
    assert state['completed_events']==['a1_completed','m1_completed','slice_completed']
    assert state['choice_history']=={'a1_choose':a_choice,'m1_choose':m_choice}
    assert len(state['inventory'])==6
    return state


def main():
    html=(ROOT/'preview'/'ashes_story_lab_v0.4.html').read_text('utf-8')
    executable=os.environ.get('AOE_CHROME_BIN') or '/usr/bin/chromium'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=executable,args=['--no-sandbox'])
        for a in ('share_with_irina','keep_private'):
            for m in ('preserve_evidence','request_explanation'):
                page=browser.new_page(viewport={'width':1280,'height':780})
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.set_content(html,wait_until='load')
                state=run_route(page,a,m)
                assert not errors,errors
                print('PASS browser:',a,m,len(state['completed_objectives']),'objectives')
                page.close()
        browser.close()

if __name__=='__main__':main()
