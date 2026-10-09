#!/usr/bin/env python3
"""
Patch for notebooklm-sdk (darakcheeff v0.3.5 build of 0.3.4), applied to the unpacked `package/` folder:
  1. VideoFormat.SHORT = 4 (vertical short-form video)
  2. VideoStyle integer codes follow notebooklm-py (verified against the live NotebookLM web client); CUSTOM = 0
  3. createVideo builds the same request as notebooklm-py: Custom style + style prompt as 7th item,
     Short/Cinematic rules, no style slot for Cinematic
  4. _callGenerate replaces the legacy client options [2] with the full capability envelope (notebooklm-py #1594)
  5. Type declarations (.d.ts/.d.cts) are updated
Usage: python3 apply-sdk-patch.py <path to the unpacked package folder>   (edits in place)
Reproduce: unpack the upstream tarball, run this script, `npm pack`, compare the SHA-256 listed in vendor/README.md.
"""
import re
import sys
from pathlib import Path

KOK = Path(sys.argv[1])

ZARF = "[2, null, null, [1, null, null, null, null, null, null, null, null, null, [1]], [[1, 4, 8, 2, 3, 6]]]"

NORMALIZE = (
    "    if (Array.isArray(params) && Array.isArray(params[0]) && params[0].length === 1 && params[0][0] === 2) {\n"
    "      params = [" + ZARF + ", ...params.slice(1)];\n"
    "    }\n"
)

CREATE_VIDEO = """  async createVideo(notebookId, opts = {}) {
    const format = opts.format ?? {VF}.EXPLAINER;
    const style = opts.style ?? null;
    const stylePrompt = typeof opts.stylePrompt === "string" ? opts.stylePrompt.trim() : "";
    const language = opts.language ?? "en";
    if (format === {VF}.CINEMATIC && stylePrompt) {
      throw new Error("stylePrompt is not supported for cinematic videos");
    }
    if (format === {VF}.SHORT && (style !== null && style !== {VS}.AUTO_SELECT || stylePrompt)) {
      throw new Error("style and stylePrompt are not supported for short videos (short has a fixed visual style)");
    }
    if (style === {VS}.CUSTOM && !stylePrompt) {
      throw new Error("stylePrompt is required when style is CUSTOM");
    }
    if (stylePrompt && style !== {VS}.CUSTOM) {
      throw new Error("stylePrompt requires style CUSTOM");
    }
    const sourceIds = opts.sourceIds ?? await this.rpc.getSourceIds(notebookId);
    const triple = tripleNest(sourceIds);
    const double = doubleNest(sourceIds);
    let config;
    if (format === {VF}.CINEMATIC) {
      config = [double, language, opts.instructions ?? null, null, format];
    } else {
      const styleCode = style === {VS}.CUSTOM ? null : style ?? {VS}.AUTO_SELECT;
      config = [double, language, opts.instructions ?? null, null, format, styleCode];
      if (style === {VS}.CUSTOM) config.push(stylePrompt);
    }
    const params = [
      [2],
      notebookId,
      [
        null,
        null,
        {ATC}.VIDEO,
        triple,
        null,
        null,
        null,
        null,
        [null, null, config]
      ]
    ];
    return this._callGenerate(notebookId, params);
  }
"""

YENI_STIL = (
    "VideoStyle = {\n      AUTO_SELECT: 1,\n      CUSTOM: 0,\n      CLASSIC: 2,\n      WHITEBOARD: 3,\n"
    "      KAWAII: 9,\n      ANIME: 7,\n      WATERCOLOR: 6,\n      RETRO_PRINT: 8,\n      HERITAGE: 4,\n"
    "      PAPER_CRAFT: 5\n    };"
)


def js_yama(dosya: Path, esm: bool):
    t = dosya.read_text(encoding="utf-8")
    ek = "" if esm else "exports."

    t, n = re.subn(r"(VideoFormat = \{\s*EXPLAINER: 1,\s*BRIEF: 2,\s*CINEMATIC: 3)(\s*\};)", r"\1,\n      SHORT: 4\2", t)
    assert n == 1, (dosya.name, "VideoFormat", n)

    m = re.search(r"VideoStyle = \{[^}]*\};", t)
    assert m, (dosya.name, "VideoStyle")
    t = t[:m.start()] + YENI_STIL + t[m.end():]

    m = re.search(r"  async createVideo\(notebookId, opts = \{\}\) \{.*?\n  \}\n(?=  async createQuiz)", t, re.S)
    assert m, (dosya.name, "createVideo")
    yeni = (CREATE_VIDEO.replace("{ATC}", ek + "ArtifactTypeCode")
            .replace("{VF}", ek + "VideoFormat").replace("{VS}", ek + "VideoStyle"))
    t = t[:m.start()] + yeni + t[m.end():]

    eski = "  async _callGenerate(notebookId, params) {\n"
    assert t.count(eski) == 1, (dosya.name, "_callGenerate")
    t = t.replace(eski, eski + NORMALIZE)
    dosya.write_text(t, encoding="utf-8")


def tip_yama(dosya: Path):
    t = dosya.read_text(encoding="utf-8")
    t, n = re.subn(r"(declare const VideoFormat: \{\n(?:    readonly \w+: \d+;\n)+?)(\};)", r"\1    readonly SHORT: 4;\n\2", t)
    assert n == 1, (dosya.name, "VideoFormat tipi", n)
    t, n = re.subn(r"declare const VideoStyle: \{\n(?:    readonly \w+: \d+;\n)+\};",
                   "declare const VideoStyle: {\n    readonly AUTO_SELECT: 1;\n    readonly CUSTOM: 0;\n    readonly CLASSIC: 2;\n"
                   "    readonly WHITEBOARD: 3;\n    readonly KAWAII: 9;\n    readonly ANIME: 7;\n    readonly WATERCOLOR: 6;\n"
                   "    readonly RETRO_PRINT: 8;\n    readonly HERITAGE: 4;\n    readonly PAPER_CRAFT: 5;\n};", t)
    assert n == 1, (dosya.name, "VideoStyle tipi", n)
    t, n = re.subn(r"(interface CreateVideoOptions \{\n    format\?: VideoFormatValue;\n    style\?: VideoStyleValue;\n)",
                   r"\1    stylePrompt?: string;\n", t)
    assert n == 1, (dosya.name, "CreateVideoOptions", n)
    dosya.write_text(t, encoding="utf-8")


js_yama(KOK / "dist" / "index.js", esm=True)
js_yama(KOK / "dist" / "index.cjs", esm=False)
tip_yama(KOK / "dist" / "index.d.ts")
tip_yama(KOK / "dist" / "index.d.cts")

pk = KOK / "package.json"
s = pk.read_text(encoding="utf-8")
s, n = re.subn(r'("version":\s*")[^"]+(")', r'\g<1>0.3.5-nikolayco.1\2', s, count=1)
assert n == 1
pk.write_text(s, encoding="utf-8")
print("patch applied:", KOK)
