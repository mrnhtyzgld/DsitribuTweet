from __future__ import annotations

import html
import zipfile
from datetime import datetime, timezone
from pathlib import Path


OUT = Path("docs/distributweet_final_presentation.pptx")
SLIDE_W = 12192000
SLIDE_H = 6858000


SLIDES = [
    {
        "title": "DistribuTweet",
        "subtitle": "Pseudo-Distributed Content-Based Recommendation",
        "presenter": "Presenter 1",
        "bullets": [
            "Arda Onat Acar, Nihat Emre Yuzuguldu",
            "Goal: transform a tweet-like stream into personalized semantic feeds.",
            "Stack: Kafka, Spark, MiniLM embeddings, Qdrant, Scala/http4s API.",
        ],
    },
    {
        "title": "Presentation Roadmap",
        "presenter": "Presenter 1",
        "bullets": [
            "Problem and scope.",
            "RecSys 2021 schema and local data generation.",
            "Kafka ingestion and Spark cleaning.",
            "Embeddings, Qdrant, ranking, API, tests, and demo.",
            "Target duration: 20 minutes including live demo.",
        ],
    },
    {
        "title": "Problem Motivation",
        "presenter": "Presenter 1",
        "bullets": [
            "Social feeds receive more posts than users can read.",
            "Chronological order is simple but often irrelevant.",
            "Follow graphs and engagement history are not always available.",
            "Cold-start users need an initial recommendation signal.",
            "Content similarity gives a practical first baseline.",
        ],
    },
    {
        "title": "Scope And Design",
        "presenter": "Presenter 1",
        "bullets": [
            "Implemented: streaming ingestion, validation, token decode.",
            "Implemented: deduplication, embeddings, vector search.",
            "Implemented: transparent scoring and API feed serving.",
            "Not in v1: learned ranking and collaborative filtering.",
            "Not in v1: authentication, moderation, production operations.",
        ],
    },
    {
        "title": "Dataset Target",
        "presenter": "Presenter 1",
        "bullets": [
            "Target schema: Twitter RecSys Challenge 2021.",
            "Original task: tweet engagement prediction and fairness.",
            "Tweet text is distributed as multilingual BERT token IDs.",
            "Default demo uses feature-schema-compatible synthetic records.",
            "Compatible real TSV can be replayed with --input-tsv.",
        ],
    },
    {
        "title": "Data Generation",
        "presenter": "Presenter 1",
        "bullets": [
            "data-generator/generator.py creates RecSys-style feature TSV rows.",
            "Topic pools cover technology, sports, food, travel, finance, art, and more.",
            "text_tokens uses real bert-base-multilingual-cased token IDs.",
            "Rate and total message count are configurable.",
            "Extra engagement label columns can be ignored by the content pipeline.",
        ],
    },
    {
        "title": "End-To-End Pipeline",
        "presenter": "Presenter 1",
        "bullets": [
            "data-generator or optional TSV file.",
            "Kafka topic posts.raw.",
            "Scala Spark cleaner.",
            "Kafka topic posts.cleaned.",
            "Python embedding workers.",
            "Qdrant vector database and Scala recommendation API.",
        ],
    },
    {
        "title": "Kafka And Spark",
        "presenter": "Presenter 1",
        "bullets": [
            "Kafka 3.8.0 runs in KRaft mode.",
            "posts.raw and posts.cleaned use three partitions.",
            "Spark 3.5.4 runs with one master and two workers.",
            "Cleaner parses TSV, validates fields, decodes WordPiece tokens.",
            "Cleaner deduplicates by tweet ID and emits cleaned JSON.",
        ],
    },
    {
        "title": "Pseudo-Distributed Scale",
        "presenter": "Presenter 1",
        "bullets": [
            "One physical machine, separate service boundaries.",
            "Kafka partitions distribute stream records.",
            "Spark workers process the cleaning stage.",
            "Embedding replicas share one Kafka consumer group.",
            "Qdrant stores vectors outside the API process.",
            "Services can scale without changing the event schema.",
        ],
    },
    {
        "title": "Embeddings And Qdrant",
        "presenter": "Presenter 2",
        "bullets": [
            "Model: paraphrase-multilingual-MiniLM-L12-v2.",
            "Vector size: 384 dimensions.",
            "Embedding workers consume posts.cleaned.",
            "Qdrant collection: posts with cosine distance.",
            "A separate HTTP embedding service handles user interests.",
        ],
    },
    {
        "title": "User Profiles",
        "presenter": "Presenter 2",
        "bullets": [
            "User submits explicit interest phrases.",
            "API removes empty phrases.",
            "Each phrase is embedded.",
            "Vectors are averaged and normalized.",
            "Prototype stores profile vectors in API memory.",
            "Future version can persist profiles in Qdrant.",
        ],
    },
    {
        "title": "Retrieval And Ranking",
        "presenter": "Presenter 2",
        "bullets": [
            "Qdrant retrieves a larger candidate pool than the requested feed size.",
            "Cosine score is normalized from [-1,1] to [0,1].",
            "recencyScore = exp(-ageHours / 24).",
            "finalScore = 0.85 * semantic + 0.15 * recency.",
            "Near-duplicate text is filtered with Jaccard similarity.",
            "API returns score components for inspection.",
        ],
    },
    {
        "title": "API And Interfaces",
        "presenter": "Presenter 2",
        "bullets": [
            "POST /users/{userId}/interests creates profiles.",
            "GET /users/{userId}/feed?limit=20 returns recommendations.",
            "GET /health reports service health.",
            "Recommendation API: localhost:8081.",
            "Spark master UI: localhost:8080.",
            "Qdrant dashboard: localhost:6333/dashboard.",
        ],
    },
    {
        "title": "Live Demo",
        "presenter": "Presenter 2",
        "bullets": [
            "docker compose up -d --build.",
            "./scripts/smoke-test.sh.",
            "./scripts/demo.sh.",
            "./scripts/show-distribution.sh.",
            "Show Kafka partitions, Spark logs, embedding group, Qdrant count.",
            "Show different feeds for different interest profiles.",
        ],
    },
    {
        "title": "Evaluation And Tests",
        "presenter": "Presenter 2",
        "bullets": [
            "Evaluation is functional and qualitative.",
            "Scala tests run during Docker builds.",
            "Tested: TSV parsing and validation.",
            "Tested: WordPiece decoding.",
            "Tested: ranking formula and deterministic behavior.",
            "Smoke tests validate the running Compose environment.",
        ],
    },
    {
        "title": "Limitations And Future Work",
        "presenter": "Presenter 2",
        "bullets": [
            "Rule-based ranking, no learned model yet.",
            "No collaborative filtering or impression history yet.",
            "Local data are synthetic unless real compatible TSV is supplied.",
            "Future: use engagement labels, train ranking model, evaluate NDCG.",
            "Future: latency metrics, Kafka lag, multi-node Kubernetes tests.",
        ],
    },
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def paragraph(text: str, size: int, color: str = "17201C", bold: bool = False) -> str:
    b_attr = ' b="1"' if bold else ""
    return f"""
      <a:p>
        <a:r>
          <a:rPr lang="en-US" sz="{size}"{b_attr}>
            <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
          </a:rPr>
          <a:t>{esc(text)}</a:t>
        </a:r>
        <a:endParaRPr lang="en-US" sz="{size}"/>
      </a:p>"""


def text_shape(
    shape_id: int,
    x: int,
    y: int,
    cx: int,
    cy: int,
    lines: list[tuple[str, int, str, bool]],
) -> str:
    paras = "\n".join(paragraph(*line) for line in lines)
    return f"""
    <p:sp>
      <p:nvSpPr>
        <p:cNvPr id="{shape_id}" name="TextBox {shape_id}"/>
        <p:cNvSpPr txBox="1"/>
        <p:nvPr/>
      </p:nvSpPr>
      <p:spPr>
        <a:xfrm>
          <a:off x="{x}" y="{y}"/>
          <a:ext cx="{cx}" cy="{cy}"/>
        </a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        <a:noFill/>
        <a:ln><a:noFill/></a:ln>
      </p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" anchor="t"/>
        <a:lstStyle/>
        {paras}
      </p:txBody>
    </p:sp>"""


def slide_xml(slide: dict[str, object], index: int) -> str:
    title = str(slide["title"])
    presenter = str(slide["presenter"])
    subtitle = str(slide.get("subtitle", ""))
    bullets = [str(item) for item in slide["bullets"]]

    title_lines = [(title, 3800 if index > 1 else 5000, "0F766E", True)]
    if subtitle:
        title_lines.append((subtitle, 2450, "17201C", False))
    title_shape = text_shape(2, 620000, 360000, 10900000, 1150000, title_lines)

    bullet_lines = [(f"- {item}", 1800, "17201C", False) for item in bullets]
    body_shape = text_shape(3, 800000, 1700000, 10600000, 4050000, bullet_lines)
    footer_shape = text_shape(4, 800000, 6200000, 3500000, 300000, [(presenter, 1400, "66706B", True)])

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="{SLIDE_W}" cy="{SLIDE_H}"/>
        </a:xfrm>
      </p:grpSpPr>
      {title_shape}
      {body_shape}
      {footer_shape}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def slide_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def presentation_xml() -> str:
    slide_ids = "\n".join(
        f'<p:sldId id="{256 + i}" r:id="rId{2 + i}"/>' for i in range(len(SLIDES))
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    {slide_ids}
  </p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle/>
</p:presentation>"""


def presentation_rels_xml() -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ]
    rels.extend(
        f'<Relationship Id="rId{2 + i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i + 1}.xml"/>'
        for i in range(len(SLIDES))
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {' '.join(rels)}
</Relationships>"""


def content_types_xml() -> str:
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    overrides.extend(
        f'<Override PartName="/ppt/slides/slide{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(len(SLIDES))
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  {' '.join(overrides)}
</Types>"""


ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


SLIDE_LAYOUT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


SLIDE_LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


SLIDE_MASTER = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/><a:chOff x="0" y="0"/><a:chExt cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""


SLIDE_MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""


THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="DistribuTweet">
  <a:themeElements>
    <a:clrScheme name="DistribuTweet">
      <a:dk1><a:srgbClr val="17201C"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="315FBD"/></a:dk2>
      <a:lt2><a:srgbClr val="F6F7F2"/></a:lt2>
      <a:accent1><a:srgbClr val="0F766E"/></a:accent1>
      <a:accent2><a:srgbClr val="315FBD"/></a:accent2>
      <a:accent3><a:srgbClr val="B83C5A"/></a:accent3>
      <a:accent4><a:srgbClr val="B7791F"/></a:accent4>
      <a:accent5><a:srgbClr val="66706B"/></a:accent5>
      <a:accent6><a:srgbClr val="394150"/></a:accent6>
      <a:hlink><a:srgbClr val="315FBD"/></a:hlink>
      <a:folHlink><a:srgbClr val="B83C5A"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="DistribuTweet">
      <a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont>
      <a:minorFont><a:latin typeface="Aptos"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="DistribuTweet">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>DistribuTweet Final Presentation</dc:title>
  <dc:creator>DistribuTweet Team</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


APP_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>{len(SLIDES)}</Slides>
</Properties>"""


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", content_types_xml())
        pptx.writestr("_rels/.rels", ROOT_RELS)
        pptx.writestr("docProps/core.xml", core_xml())
        pptx.writestr("docProps/app.xml", APP_XML)
        pptx.writestr("ppt/presentation.xml", presentation_xml())
        pptx.writestr("ppt/_rels/presentation.xml.rels", presentation_rels_xml())
        pptx.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
        pptx.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", SLIDE_MASTER_RELS)
        pptx.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
        pptx.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", SLIDE_LAYOUT_RELS)
        pptx.writestr("ppt/theme/theme1.xml", THEME)
        for index, slide in enumerate(SLIDES, start=1):
            pptx.writestr(f"ppt/slides/slide{index}.xml", slide_xml(slide, index))
            pptx.writestr(f"ppt/slides/_rels/slide{index}.xml.rels", slide_rels_xml())

    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
