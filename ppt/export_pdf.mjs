#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '..');
const defaultInput = path.join(repoRoot, 'ppt', 'index.html');
const defaultOutput = path.join(repoRoot, 'ppt', 'preview.pdf');
const defaultTempDir = path.join(repoRoot, 'tmp', 'pdfs');
const pageWidthIn = 13.333333333;
const pageHeightIn = 7.5;

function readArgument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

function existingDirectory(candidate) {
  return Boolean(candidate && fs.existsSync(candidate) && fs.statSync(candidate).isDirectory());
}

function findNodeModules() {
  const candidates = [
    process.env.CODEX_NODE_MODULES,
    path.resolve(path.dirname(process.execPath), '..', 'node_modules')
  ].filter(Boolean);

  const windowsApps = process.env.ProgramFiles
    ? path.join(process.env.ProgramFiles, 'WindowsApps')
    : null;
  if (existingDirectory(windowsApps)) {
    try {
      const runtimes = fs.readdirSync(windowsApps, { withFileTypes: true })
        .filter(entry => entry.isDirectory() && entry.name.startsWith('OpenAI.CodexPrimaryRuntime.v'))
        .map(entry => entry.name)
        .sort()
        .reverse();
      for (const name of runtimes) {
        candidates.push(path.join(windowsApps, name, 'dependencies', 'node', 'node_modules'));
      }
    } catch (error) {
      if (!process.env.CODEX_NODE_MODULES) {
        throw new Error(
          `无法列举 WindowsApps，且未设置 CODEX_NODE_MODULES：${error.message}`
        );
      }
    }
  }

  const found = candidates.find(candidate =>
    existingDirectory(candidate) &&
    fs.existsSync(path.join(candidate, 'playwright')) &&
    fs.existsSync(path.join(candidate, 'pdf-lib'))
  );
  if (!found) {
    throw new Error('找不到随附的 Playwright/pdf-lib；请设置 CODEX_NODE_MODULES 指向 node_modules。');
  }
  return found;
}

function findEdge() {
  const candidates = [
    process.env.EDGE_PATH,
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
  ].filter(Boolean);
  const found = candidates.find(candidate => fs.existsSync(candidate));
  if (!found) {
    throw new Error('找不到 Edge/Chrome；请设置 EDGE_PATH。');
  }
  return found;
}

function findPoppler(nodeModules) {
  const candidates = [
    process.env.POPPLER_BIN,
    path.resolve(nodeModules, '..', '..', 'native', 'poppler', 'Library', 'bin')
  ].filter(Boolean);
  return candidates.find(candidate =>
    existingDirectory(candidate) &&
    fs.existsSync(path.join(candidate, 'pdftoppm.exe'))
  ) || null;
}

function validatePathInside(candidate, parent) {
  const resolvedCandidate = path.resolve(candidate);
  const resolvedParent = path.resolve(parent);
  const relative = path.relative(resolvedParent, resolvedCandidate);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error(`输出路径越出工作区：${candidate}`);
  }
  return resolvedCandidate;
}

function rmFile(filePath) {
  fs.rmSync(filePath, { force: true });
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: 'utf8',
    windowsHide: true,
    ...options
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(
      `${path.basename(command)} 退出码 ${result.status}\n${result.stdout || ''}\n${result.stderr || ''}`
    );
  }
  return result;
}

const printCss = `
@page { size: ${pageWidthIn}in ${pageHeightIn}in; margin: 0; }
@media print {
  html, body {
    width: ${pageWidthIn}in !important;
    height: ${pageHeightIn}in !important;
    min-width: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    background: #fff !important;
  }
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  #deck {
    position: absolute !important;
    inset: 0 auto auto 0 !important;
    display: block !important;
    width: ${pageWidthIn}in !important;
    height: ${pageHeightIn}in !important;
    min-width: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    transform: none !important;
    transition: none !important;
  }
  #deck > .slide {
    position: absolute !important;
    inset: 0 auto auto 0 !important;
    display: none !important;
    width: ${pageWidthIn}in !important;
    height: ${pageHeightIn}in !important;
    min-width: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
    transform: none !important;
    opacity: 1 !important;
    visibility: visible !important;
    break-after: auto !important;
    page-break-after: auto !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  #deck > .slide[data-pdf-selected="true"] {
    display: flex !important;
    align-items: stretch !important;
    justify-content: stretch !important;
  }
  #deck > .slide > .canvas-card {
    width: 100% !important;
    height: 100% !important;
    max-width: none !important;
    max-height: none !important;
    margin: 0 !important;
  }
  #deck [data-anim],
  #deck .motion-ready [data-anim] {
    opacity: 1 !important;
    visibility: visible !important;
    transform: none !important;
    animation: none !important;
    transition: none !important;
  }
  #hint, #nav, #ppt-presenter, #overview, .ppt-presenter, .ppt-ui-toast {
    display: none !important;
  }
  .viz-toolbar {
    display: none !important;
  }
  .viz-poster {
    display: block !important;
  }
  #deck > .slide[data-slide-id="insertion"] .tree-node {
    width: 0.9vw !important;
    min-width: 0.9vw !important;
    height: 0.9vw !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 0.52vw !important;
    line-height: 1 !important;
  }
}
`;

async function main() {
  const input = validatePathInside(
    path.resolve(readArgument('--input', defaultInput)),
    repoRoot
  );
  const output = validatePathInside(
    path.resolve(readArgument('--output', defaultOutput)),
    repoRoot
  );
  const tempDir = validatePathInside(
    path.resolve(readArgument('--temp-dir', defaultTempDir)),
    repoRoot
  );
  const renderQa = process.argv.includes('--render');

  if (!fs.existsSync(input)) {
    throw new Error(`输入 HTML 不存在：${input}`);
  }

  const nodeModules = findNodeModules();
  const requireBundled = createRequire(path.join(path.dirname(nodeModules), 'export_pdf_require.cjs'));
  const { chromium } = requireBundled(path.join(nodeModules, 'playwright'));
  const { PDFDocument } = requireBundled(path.join(nodeModules, 'pdf-lib'));
  const edgePath = findEdge();
  const popplerBin = findPoppler(nodeModules);

  fs.mkdirSync(tempDir, { recursive: true });
  fs.mkdirSync(path.dirname(output), { recursive: true });

  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  const browser = await chromium.launch({
    executablePath: edgePath,
    headless: true,
    args: [
      '--allow-file-access-from-files',
      '--enable-webgl',
      '--enable-unsafe-swiftshader',
      '--ignore-gpu-blocklist',
      '--use-angle=swiftshader',
      '--disable-gpu-sandbox'
    ]
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 1,
      colorScheme: 'light'
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30_000);
    page.on('console', message => {
      if (message.type() === 'error') {
        consoleErrors.push(message.text());
      }
    });
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('requestfailed', request => {
      failedRequests.push(`${request.url()} :: ${request.failure()?.errorText || 'unknown'}`);
    });

    await page.goto(pathToFileURL(input).href, { waitUntil: 'load' });
    await page.waitForFunction(() =>
      window.KD_DATA &&
      window.KDViz &&
      document.querySelectorAll('#deck > .slide').length > 0
    );
    await page.evaluate(async () => {
      await document.fonts.ready;
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });

    const slides = await page.evaluate(() => {
      const data = window.KD_DATA;
      const maxima = {
        overview: 0,
        build: (data.buildEvents || []).length,
        range: data.range?.events?.length || 0,
        nearest: data.nearest?.events?.length || 0,
        insertion: data.dynamic?.steps?.length || 0,
        dynamic: data.dynamic?.steps?.length || 0
      };
      return [...document.querySelectorAll('#deck > .slide')].map((slide, index) => {
        const viz = slide.querySelector('.viz');
        const kind = viz?.dataset.demo || null;
        let step = maxima[kind] || 0;
        if (kind === 'insertion') {
          step = Math.min(16, Math.max(1, Math.ceil(maxima[kind] / 2)));
        }
        return {
          index,
          id: slide.dataset.slideId,
          kind,
          maxStep: maxima[kind] || 0,
          step
        };
      });
    });

    if (slides.length !== 18) {
      throw new Error(`预期 18 页，实际读取到 ${slides.length} 页。`);
    }
    if (slides.some(slide => !slide.id)) {
      throw new Error('存在缺少 data-slide-id 的页面。');
    }
    if (slides.some(slide => slide.kind && slide.kind !== 'overview' && slide.step < 1)) {
      throw new Error('存在无法确定静态回放步骤的页面。');
    }

    const vizSlides = slides.filter(slide => slide.kind);
    const requestedSteps = vizSlides.map(slide => ({
      id: slide.id,
      step: slide.step,
      ...(slide.kind === 'insertion'
        ? { camera: { yaw: 2.25, pitch: 0.28, zoom: 1 } }
        : {})
    }));
    await page.evaluate(states => window.KDViz.receive(states), requestedSteps);

    const frozenFrames = [];
    const postersToApply = [];
    const freezeOrder = [...vizSlides].sort((left, right) =>
      Number(right.kind === 'insertion') - Number(left.kind === 'insertion')
    );
    for (const slide of freezeOrder) {
      await page.evaluate(({ index, id }) => {
        const deck = document.getElementById('deck');
        deck.style.transition = 'none';
        deck.style.transform = `translateX(${-index * 100}vw)`;
        window.__currentSlideIndex = index;
        document.body.classList.remove('dark-bg', 'accent-bg');
        window.KDViz.activate(index);
        const slide = document.querySelector(`#deck > .slide[data-slide-id="${id}"]`);
        const canvas = slide.querySelector('.viz-3d canvas');
        const labels = slide.querySelector('.viz-labels');
        if (canvas) canvas.style.display = '';
        if (labels) labels.style.display = '';
      }, { index: slide.index, id: slide.id });
      const requestedState = requestedSteps.find(state => state.id === slide.id);
      await page.evaluate(state => window.KDViz.receive([state]), requestedState);
      if (slide.kind === 'insertion') {
        await page.evaluate(id => {
          const labels = document.querySelector(
            `#deck > .slide[data-slide-id="${id}"] .viz-labels`
          );
          for (const label of labels.querySelectorAll('.viz-label')) {
            if (label.textContent.trim() === 'T15') {
              label.style.display = 'none';
            }
          }
        }, slide.id);
      }
      await page.waitForTimeout(500);
      await page.evaluate(() => new Promise(resolve =>
        requestAnimationFrame(() => requestAnimationFrame(resolve))
      ));

      const debug = await page.evaluate(() => window.KDViz.debug());
      const stage = page.locator(
        `#deck > .slide[data-slide-id="${slide.id}"] .viz-3d`
      );
      if (await stage.count()) {
        const canvasStats = await page.evaluate(id => {
          const canvas = document.querySelector(
            `#deck > .slide[data-slide-id="${id}"] .viz-3d canvas`
          );
          if (!canvas || !canvas.width || !canvas.height) {
            return { width: 0, height: 0, nonWhite: 0 };
          }
          const probe = document.createElement('canvas');
          probe.width = canvas.width;
          probe.height = canvas.height;
          const context = probe.getContext('2d', { willReadFrequently: true });
          context.drawImage(canvas, 0, 0);
          const pixels = context.getImageData(0, 0, probe.width, probe.height).data;
          let nonWhite = 0;
          for (let offset = 0; offset < pixels.length; offset += 4) {
            if (
              pixels[offset] < 248 ||
              pixels[offset + 1] < 248 ||
              pixels[offset + 2] < 248
            ) {
              nonWhite += 1;
            }
          }
          return { width: probe.width, height: probe.height, nonWhite };
        }, slide.id);
        if (canvasStats.nonWhite < 500) {
          throw new Error(`${slide.id} 的 WebGL canvas 近似空白：${JSON.stringify(canvasStats)}`);
        }
        const screenshotPath = path.join(
          tempDir,
          `viz-${String(slide.index + 1).padStart(2, '0')}-${slide.id}.png`
        );
        rmFile(screenshotPath);
        const image = await stage.screenshot({
          animations: 'disabled',
          timeout: 30_000,
          type: 'png'
        });
        fs.writeFileSync(screenshotPath, image);
        const dataUrl = `data:image/png;base64,${image.toString('base64')}`;
        postersToApply.push({ id: slide.id, dataUrl });
        if (debug.renderer !== 'webgl') {
          throw new Error(`${slide.id} 未能使用 WebGL 静态渲染。`);
        }
        frozenFrames.push({
          page: slide.index + 1,
          id: slide.id,
          kind: slide.kind,
          step: slide.step,
          maxStep: slide.maxStep,
          renderer: debug.renderer,
          canvasStats,
          image: path.relative(repoRoot, screenshotPath).replaceAll('\\', '/')
        });
      } else {
        frozenFrames.push({
          page: slide.index + 1,
          id: slide.id,
          kind: slide.kind,
          step: slide.step,
          maxStep: slide.maxStep,
          renderer: 'tree',
          image: null
        });
      }
    }
    for (const posterData of postersToApply) {
      await page.evaluate(({ id, dataUrl }) => {
        const host = document.querySelector(
          `#deck > .slide[data-slide-id="${id}"] .viz-3d`
        );
        let poster = host.querySelector('.viz-poster');
        if (!poster) {
          poster = document.createElement('img');
          poster.className = 'viz-poster';
          poster.alt = '三维场景静态帧';
          host.prepend(poster);
        }
        poster.src = dataUrl;
        poster.style.display = 'block';
        const canvas = host.querySelector('canvas');
        const labels = host.querySelector('.viz-labels');
        if (canvas) canvas.style.display = 'none';
        if (labels) labels.style.display = 'none';
      }, posterData);
    }

    await page.emulateMedia({ media: 'print' });
    await page.addStyleTag({ content: printCss });
    await page.evaluate(() => {
      const deck = document.getElementById('deck');
      deck.style.transition = 'none';
      document.documentElement.classList.add('pdf-export');
      document.body.classList.add('pdf-export');
    });

    const slidePdfs = [];
    for (const slide of slides) {
      await page.evaluate(index => {
        const allSlides = [...document.querySelectorAll('#deck > .slide')];
        allSlides.forEach((element, elementIndex) => {
          if (elementIndex === index) {
            element.setAttribute('data-pdf-selected', 'true');
          } else {
            element.removeAttribute('data-pdf-selected');
          }
        });
      }, slide.index);
      await page.waitForTimeout(80);
      const selectedState = await page.evaluate(index => {
        const selected = document.querySelectorAll('#deck > .slide')[index];
        const style = getComputedStyle(selected);
        const rect = selected.getBoundingClientRect();
        return {
          display: style.display,
          visibility: style.visibility,
          opacity: style.opacity,
          width: rect.width,
          height: rect.height
        };
      }, slide.index);
      if (
        selectedState.display === 'none' ||
        selectedState.visibility !== 'visible' ||
        Number(selectedState.opacity) === 0 ||
        selectedState.width < 1000 ||
        selectedState.height < 500
      ) {
        throw new Error(
          `第 ${slide.index + 1} 页在打印媒体下不可见或尺寸异常：${JSON.stringify(selectedState)}`
        );
      }
      const slidePdf = path.join(
        tempDir,
        `slide-${String(slide.index + 1).padStart(2, '0')}-${slide.id}.pdf`
      );
      rmFile(slidePdf);
      await page.pdf({
        path: slidePdf,
        width: `${pageWidthIn}in`,
        height: `${pageHeightIn}in`,
        margin: { top: '0', right: '0', bottom: '0', left: '0' },
        printBackground: true,
        preferCSSPageSize: true,
        pageRanges: '1'
      });
      slidePdfs.push(slidePdf);
    }

    const merged = await PDFDocument.create();
    for (const slidePdf of slidePdfs) {
      const source = await PDFDocument.load(fs.readFileSync(slidePdf));
      const [copiedPage] = await merged.copyPages(source, [0]);
      merged.addPage(copiedPage);
    }
    merged.setTitle('KD-tree：多维空间查询与动态维护 · PDF 预览');
    merged.setAuthor('KD-tree 课程汇报项目');
    merged.setCreator('ppt/export_pdf.mjs + Playwright + Edge');
    merged.setProducer('Microsoft Edge printToPDF + pdf-lib');
    merged.setCreationDate(new Date());
    fs.writeFileSync(output, await merged.save());

    const verification = await PDFDocument.load(fs.readFileSync(output));
    if (verification.getPageCount() !== 18) {
      throw new Error(`合并 PDF 页数错误：${verification.getPageCount()}`);
    }
    for (const [index, pdfPage] of verification.getPages().entries()) {
      const { width, height } = pdfPage.getSize();
      if (Math.abs(width / height - 16 / 9) > 0.002) {
        throw new Error(`第 ${index + 1} 页比例不是 16:9：${width} x ${height}`);
      }
    }

    if (renderQa) {
      if (!popplerBin) {
        throw new Error('找不到 pdftoppm，无法生成 QA PNG。');
      }
      for (let pageNumber = 1; pageNumber <= 18; pageNumber += 1) {
        rmFile(path.join(tempDir, `page-${String(pageNumber).padStart(2, '0')}.png`));
      }
      run(
        path.join(popplerBin, 'pdftoppm.exe'),
        ['-png', '-r', '120', '-f', '1', '-l', '18', output, path.join(tempDir, 'page')]
      );
    }

    const manifest = {
      exportedAt: new Date().toISOString(),
      input: path.relative(repoRoot, input).replaceAll('\\', '/'),
      output: path.relative(repoRoot, output).replaceAll('\\', '/'),
      browser: edgePath,
      pageCount: verification.getPageCount(),
      pageSizePoints: verification.getPage(0).getSize(),
      aspectRatio: 16 / 9,
      frozenFrames,
      consoleErrors,
      pageErrors,
      failedRequests
    };
    fs.writeFileSync(
      path.join(tempDir, 'export-manifest.json'),
      `${JSON.stringify(manifest, null, 2)}\n`,
      'utf8'
    );

    console.log(`已导出 ${verification.getPageCount()} 页：${output}`);
    console.log(`静态回放槽：${frozenFrames.length} 个；WebGL：${frozenFrames.filter(frame => frame.renderer === 'webgl').length} 个`);
    if (renderQa) {
      console.log(`QA PNG：${path.join(tempDir, 'page-01.png')} … ${path.join(tempDir, 'page-18.png')}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
