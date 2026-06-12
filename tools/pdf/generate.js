/* ============================================================
   NEXUM by Tigre — geração dos PDFs das páginas públicas
   Renderização fiel (Chrome headless via Puppeteer, JS habilitado)
   + PDF combinado (pdf-lib). Saída: tools/pdf/dist-pdf/*.pdf
   ============================================================ */
"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const { PDFDocument } = require("pdf-lib");

const PUBLIC = path.resolve(__dirname, "../../public");
const OUT = path.resolve(__dirname, "dist-pdf");

const MIME = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8", ".txt": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon",
};

// Ordem de páginas -> nome do PDF
const PAGES = [
  ["index.html", "01-inicio-war-room.pdf"],
  ["nexum.html", "02-nexum-institucional.pdf"],
  ["war-room.html", "03-war-room.pdf"],
  ["controladoria.html", "04-controladoria.pdf"],
  ["grafo.html", "05-grafo-evidencia-xai.pdf"],
  ["api.html", "06-api-openapi.pdf"],
  ["planos.html", "07-planos.pdf"],
];
const COMBINED = "00-NEXUM-completo.pdf";

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      let urlPath = decodeURIComponent(req.url.split("?")[0]);
      if (urlPath === "/") urlPath = "/index.html";
      const fp = path.join(PUBLIC, urlPath);
      if (!fp.startsWith(PUBLIC) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
        res.statusCode = 404; return res.end("404");
      }
      res.setHeader("Content-Type", MIME[path.extname(fp)] || "application/octet-stream");
      fs.createReadStream(fp).pipe(res);
    });
    srv.listen(0, "127.0.0.1", () => resolve(srv));
  });
}

(async () => {
  if (!fs.existsSync(PUBLIC)) { throw new Error("public/ não encontrado em " + PUBLIC); }
  fs.mkdirSync(OUT, { recursive: true });

  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}`;
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
  });

  const pdfMargin = { top: "12mm", bottom: "12mm", left: "10mm", right: "10mm" };

  for (const [src, out] of PAGES) {
    const page = await browser.newPage();
    await page.emulateMediaType("screen"); // preserva o tema escuro V18
    const resp = await page.goto(`${base}/${src}`, { waitUntil: "networkidle0", timeout: 90000 });
    await new Promise((r) => setTimeout(r, 1200)); // assenta animações/JS (grafo, viewer)
    await page.pdf({
      path: path.join(OUT, out), format: "A4",
      printBackground: true, preferCSSPageSize: true, margin: pdfMargin,
    });
    console.log(`OK  ${src} (${resp ? resp.status() : "?"}) -> ${out}`);
    await page.close();
  }

  await browser.close();
  srv.close();

  // PDF combinado (pdf-lib)
  const merged = await PDFDocument.create();
  for (const [, out] of PAGES) {
    const bytes = fs.readFileSync(path.join(OUT, out));
    const doc = await PDFDocument.load(bytes);
    const pages = await merged.copyPages(doc, doc.getPageIndices());
    pages.forEach((p) => merged.addPage(p));
  }
  fs.writeFileSync(path.join(OUT, COMBINED), await merged.save());
  console.log(`OK  combinado -> ${COMBINED}`);
  console.log("DONE · " + OUT);
})().catch((e) => { console.error("FAIL", e); process.exit(1); });
