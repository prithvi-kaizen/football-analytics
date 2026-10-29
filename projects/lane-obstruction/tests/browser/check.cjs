// Optional browser verification: npm install playwright, then node tests/browser/check.cjs.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
(async()=>{
 const root=path.resolve(__dirname,'../..'),base=process.env.LANE_VIEWER_URL||'http://127.0.0.1:4183/outputs/viewer.html';
 const browser=await chromium.launch({headless:true,...(process.env.LANE_BROWSER_CHANNEL?{channel:process.env.LANE_BROWSER_CHANNEL}:{}),...(process.env.LANE_BROWSER_EXECUTABLE?{executablePath:process.env.LANE_BROWSER_EXECUTABLE}:{})});
 const page=await browser.newPage({viewport:{width:1365,height:1100}}),errors=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base);await page.waitForSelector('#pitch circle');
 const initial=await page.locator('#laneValue').textContent();
 await page.selectOption('#target','1');assert.notEqual(await page.locator('#laneValue').textContent(),initial);checks.push('Target select changes displayed target and lane scores');
 await page.selectOption('#defender','1');assert((await page.locator('#defenderValue').textContent()).includes('DLO'));checks.push('Defender select changes named DLO and arrival margin');
 await page.selectOption('#example','1');assert.equal(await page.locator('#frame').inputValue(),'0');checks.push('Possession select resets frame and target set');
 await page.click('#next');assert.equal(await page.locator('#frame').inputValue(),'1');
 await page.click('#previous');assert.equal(await page.locator('#frame').inputValue(),'0');checks.push('Previous/Next move exactly one sampled frame; boundary buttons disabled');
 await page.locator('#frame').focus();await page.keyboard.press('ArrowRight');assert.equal(await page.locator('#frame').inputValue(),'1');checks.push('Range control responds to keyboard ArrowRight');
 await page.check('#freeze');assert((await page.locator('#laneValue').textContent()).includes('frozen-state'));await page.uncheck('#freeze');checks.push('Freeze checkbox switches defender-state display');
 const polygons=await page.locator('#pitch polygon').count();await page.uncheck('#corridor');assert.equal(await page.locator('#pitch polygon').count(),0);assert.equal(polygons,1);await page.check('#corridor');checks.push('Corridor checkbox hides and restores the finite baseline corridor');
 await page.click('#play');await page.waitForTimeout(650);assert.equal(await page.locator('#play').textContent(),'Pause replay');await page.click('#play');assert.equal(await page.locator('#play').textContent(),'Play replay');checks.push('Play advances; Pause stops; playback does not autoplay');
 await page.locator('#exact summary').click();assert.equal(await page.locator('#timelineRows tr').count(),10);checks.push('Exact-value disclosure expands populated lane and defender tables');
 const downloaded=page.waitForEvent('download');await page.click('#download');const download=await downloaded;assert.equal(download.suggestedFilename(),'lane-obstruction-results.json');const file=await download.path();assert.equal(JSON.parse(fs.readFileSync(file)).pooled.n,832);checks.push('JSON download contains the executed 832-label result');
 for(const href of ['results.md','../docs/methodology.md','../docs/limitations.md','../docs/source/SkillCorner-LICENSE']){
  const link=page.locator(`a[href="${href}"]`);const response=await page.request.get(new URL(href,base).href);assert.equal(response.status(),200);assert.equal(await link.count(),1);
 }
 checks.push('Four local results/methodology/limitations/licence links resolve HTTP 200');
 await page.locator('.skip').click();assert.equal(new URL(page.url()).hash,'#replay');checks.push('Skip link navigates to the replay anchor');
 await page.screenshot({path:path.join(root,'outputs/viewer-desktop.png'),fullPage:true});
 for(const width of [320,390,640,820,1060,1365]){
  await page.setViewportSize({width,height:1000});await page.waitForTimeout(60);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Overflow at ${width}`);
 }
 checks.push('No document horizontal overflow at 320/390/640/820/1060/1365 px');
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(root,'outputs/viewer-mobile.png'),fullPage:true});
 await page.evaluate(()=>document.documentElement.style.fontSize='200%');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));checks.push('200% root text size at 390 px reflows without page overflow');
 const html=fs.readFileSync(path.join(root,'outputs/viewer.html'),'utf8');
 const errorPage=await browser.newPage();await errorPage.setContent(html.replace(/(<script id="payload" type="application\/json">)[\s\S]*?(<\/script>)/,'$1{invalid json$2'));
 assert((await errorPage.locator('#status').textContent()).includes('could not load'));checks.push('Malformed embedded payload shows actionable error state');
 const emptyPage=await browser.newPage(),emptyPayload={replays:{examples:[]}};await emptyPage.setContent(html.replace(/(<script id="payload" type="application\/json">)[\s\S]*?(<\/script>)/,`$1${JSON.stringify(emptyPayload)}$2`));
 assert((await emptyPage.locator('#status').textContent()).includes('No eligible replay'));checks.push('Empty export shows actionable empty state');
 assert.equal(errors.length,0);
 const output={status:'passed',checks,console_errors:errors,scope:'Chromium desktop and emulated widths; no physical-device or screen-reader audit'};
 fs.writeFileSync(path.join(root,'outputs/browser-validation.json'),JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output,null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
