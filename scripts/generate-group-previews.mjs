import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const baseUrl = "https://simonh68.github.io/module-e-vocab";
const font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
const bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf";

const esc = (value) => value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");

function metaBlock({ list, group, count, previewUrl, pageUrl }) {
  const title = `List ${list} · Group ${group} | E-Vocab Band III`;
  const description = `${count} Band III vocabulary words for Module E, with Hebrew support, examples, audio and spelling practice.`;
  const alt = `E-Vocab Band III, List ${list}, Group ${group}`;
  return `\n<meta name="description" content="${esc(description)}">\n<link rel="canonical" href="${pageUrl}">\n<meta property="og:type" content="website">\n<meta property="og:site_name" content="English for Noar">\n<meta property="og:title" content="${esc(title)}">\n<meta property="og:description" content="${esc(description)}">\n<meta property="og:url" content="${pageUrl}">\n<meta property="og:image" content="${previewUrl}">\n<meta property="og:image:secure_url" content="${previewUrl}">\n<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n<meta property="og:image:alt" content="${esc(alt)}">\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="${esc(title)}">\n<meta name="twitter:description" content="${esc(description)}">\n<meta name="twitter:image" content="${previewUrl}">`;
}

function renderCard({ output, list, group, count, samples }) {
  mkdirSync(path.dirname(output), { recursive: true });
  const accents = { A: "#38e8ff", B: "#8b5cf6", C: "#ffcf38", D: "#ff5f8f" };
  const accent = accents[list];
  const sampleLine = samples.join("   •   ").replaceAll("'", "’");
  const draw = [
    "fill '#06142f' rectangle 0,0 1200,630",
    `fill '${accent}' fill-opacity 0.18 circle 1060,95 745,95`,
    "fill '#19235a' fill-opacity 0.9 circle 1120,625 785,625",
    `fill '#0d214d' fill-opacity 1 stroke '${accent}' stroke-width 4 roundrectangle 690,70 1125,560 42,42`,
    `fill '${accent}' stroke none roundrectangle 86,185 410,258 34,34`,
    "fill '#172542' stroke '#4cc9ff' stroke-opacity 0.55 stroke-width 2 roundrectangle 82,282 610,430 34,34",
    "fill '#202e4c' stroke '#5865f2' stroke-width 2 roundrectangle 82,466 610,542 26,26",
    "fill-opacity 1 stroke-opacity 1",
    "fill '#ffffff' circle 111,91 105,91",
    `fill '${accent}' circle 132,91 126,91`,
  ].join(" ");
  const args = [
    "-size", "1200x630", "xc:#06142f", "-draw", draw,
    "-font", bold, "-fill", "white", "-pointsize", "37", "-draw", "text 155,104 'ENGLISH FOR NOAR'",
    "-font", bold, "-fill", "#061029", "-pointsize", "43", "-draw", `text 126,238 'BAND III'`,
    "-font", bold, "-fill", "white", "-pointsize", "72", "-draw", `text 112,375 'LIST ${list}'`,
    "-font", bold, "-fill", "white", "-pointsize", "250", "-gravity", "center", "-draw", `text 305,0 '${group}'`, "-gravity", "northwest",
    "-font", bold, "-fill", "white", "-pointsize", "29", "-draw", `text 115,514 '${count} WORDS   ·   HEBREW SUPPORT'`,
    "-font", font, "-fill", "#bed5ff", "-pointsize", "25", "-draw", `text 86,590 '${sampleLine}'`,
    "-quality", "88", "-sampling-factor", "4:2:0", output,
  ];
  const result = spawnSync("convert", args, { encoding: "utf8" });
  if (result.status !== 0) throw new Error(result.stderr || `convert failed for ${output}`);
}

for (const list of ["A", "B", "C", "D"]) {
  for (let group = 1; group <= 3; group += 1) {
    const file = `${list}${group}.html`;
    const pagePath = path.join(root, file);
    let html = readFileSync(pagePath, "utf8");
    const match = html.match(/const words\s*=\s*(\[.*?\]);/s);
    if (!match) throw new Error(`Vocabulary data not found in ${file}`);
    const words = JSON.parse(match[1]);
    const samples = [...new Set(words.map((word) => word.en).filter((word) => word.length <= 15))].slice(0, 3);
    const previewRelative = `assets/group-previews/${list.toLowerCase()}${group}.jpg`;
    const previewUrl = `${baseUrl}/${previewRelative}`;
    const pageUrl = `${baseUrl}/${file}`;
    renderCard({ output: path.join(root, previewRelative), list, group, count: words.length, samples });
    html = html.replace(/\n?<meta name="description"[\s\S]*?<meta name="twitter:image"[^>]*>/, "");
    html = html.replace(/\n?<link rel="canonical"[^>]*>/, "");
    const titleEnd = html.indexOf("</title>") + "</title>".length;
    html = `${html.slice(0, titleEnd)}${metaBlock({ list, group, count: words.length, previewUrl, pageUrl })}${html.slice(titleEnd)}`;
    writeFileSync(pagePath, html);
  }
}

console.log("Generated and wired 12 unique Band III group preview cards.");
