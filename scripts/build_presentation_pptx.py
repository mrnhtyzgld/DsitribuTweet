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
        "subtitle": "A Distributed Content-Based Feed Recommendation Prototype",
        "presenter": "Presenter 1",
        "bullets": [
            "Arda Onat Acar, Nihat Emre Yuzuguldu",
            "Goal: turn tweet-like stream events into personalized semantic feeds.",
            "Stack: Kafka, Spark Structured Streaming, multilingual embeddings, Qdrant, Scala API.",
        ],
    },
    {
        "title": "Presentation Roadmap",
        "presenter": "Presenter 1",
        "bullets": [
            "Part 1: problem, dataset, ingestion, cleaning, scalability.",
            "Part 2: embeddings, Qdrant, ranking, API, demo, evaluation.",
            "Live demo: RecSys subset conversion -> Kafka replay -> dashboard feed.",
            "Target: 20 minutes including demo.",
        ],
    },
    {
        "title": "Problem Motivation",
        "presenter": "Presenter 1",
        "bullets": [
            "A social feed receives more posts than a user can read.",
            "Chronological order is simple but often irrelevant.",
            "Follow graphs and historical engagement are not always available.",
            "Cold-start users need a recommendation signal before behavior history exists.",
            "We use content semantics as the first recommendation signal.",
        ],
    },
    {
        "title": "Scope And Design Decisions",
        "presenter": "Presenter 1",
        "bullets": [
            "Included: streaming ingestion, validation, deduplication.",
            "Included: multilingual text embeddings and vector retrieval.",
            "Included: transparent reranking with semantic similarity, freshness, author penalty.",
            "Excluded in v1: collaborative filtering and learned ranking.",
            "Excluded in v1: authentication, moderation, and production-grade operations.",
        ],
    },
    {
        "title": "Dataset: ACM RecSys Challenge 2020",
        "presenter": "Presenter 1",
        "bullets": [
            "External data source: Twitter-sponsored ACM RecSys Challenge 2020.",
            "Task: tweet engagement prediction in Twitter Home Timeline.",
            "Reported size: 160M public tweets for training.",
            "Reported size: 40M public tweets for validation/testing.",
            "Dataset is linked in the report, not included in the zip.",
        ],
    },
    {
        "title": "Dataset Adaptation Strategy",
        "presenter": "Presenter 1",
        "bullets": [
            "Original file: headerless Ctrl-A-separated training.tsv.",
            "Adapter maps tweet_id -> postId and a_user_id -> authorId.",
            "Unix timestamp becomes ISO-8601 createdAt.",
            "text_tokens, hashtags, domains, links, and tweet type become text.",
            "Supports --limit and --offset for first 10, 100, 10000 rows.",
            "Optional BERT vocab.txt improves token decoding.",
        ],
    },
    {
        "title": "End-To-End Architecture",
        "presenter": "Presenter 1",
        "bullets": [
            "RecSys TSV subset -> JSONL converter.",
            "JSONL replay source -> Kafka posts.raw.",
            "Spark stream cleaner -> Kafka posts.cleaned + Parquet archive.",
            "Embedding worker -> Qdrant vector database.",
            "Scala recommendation API + dashboard -> personalized feed.",
        ],
    },
    {
        "title": "Kafka And Spark Cleaning Layer",
        "presenter": "Presenter 1",
        "bullets": [
            "Kafka decouples producer, Spark, embedding worker, and API.",
            "Topics: posts.raw, posts.cleaned, recommendation.events.",
            "Spark parses JSON and checks required fields.",
            "Spark filters unsupported language, short text, and malformed timestamps.",
            "Spark applies watermarking and deduplicates by postId.",
            "Clean records go to Kafka and Parquet archive.",
        ],
    },
    {
        "title": "Distributed Scalability Story",
        "presenter": "Presenter 1",
        "bullets": [
            "Kafka topics can be partitioned for parallel consumers.",
            "Spark can scale by adding executors.",
            "Embedding workers can scale as one Kafka consumer group.",
            "Qdrant separates vector storage from API logic.",
            "Recommendation API can run as multiple replicas.",
            "Docker Compose is local; Kubernetes manifests show cluster direction.",
        ],
    },
    {
        "title": "Embeddings And Qdrant",
        "presenter": "Presenter 2",
        "bullets": [
            "Model: intfloat/multilingual-e5-small.",
            "Vector size: 384 dimensions.",
            "Posts use E5 passage prefix; interests use query prefix.",
            "Embeddings are normalized for cosine similarity.",
            "Qdrant collections: posts and users.",
            "Deterministic UUIDs make replay idempotent.",
        ],
    },
    {
        "title": "User Profile Construction",
        "presenter": "Presenter 2",
        "bullets": [
            "User submits explicit interest phrases.",
            "API removes empty interests.",
            "Each phrase is embedded by the embedding worker.",
            "Vectors are averaged and normalized.",
            "Result is stored in Qdrant users collection.",
            "Feed requests reuse stored user vectors.",
        ],
    },
    {
        "title": "Candidate Retrieval And Ranking",
        "presenter": "Presenter 2",
        "bullets": [
            "Candidate retrieval: cosine search over Qdrant post vectors.",
            "Candidate count is larger than final feed size.",
            "Stale posts are filtered by max post age.",
            "Final score = 0.85 semantic + 0.15 recency - author penalty.",
            "Author penalty reduces repeated authors.",
            "API returns semantic, recency, and final scores for inspection.",
        ],
    },
    {
        "title": "API And Dashboard",
        "presenter": "Presenter 2",
        "bullets": [
            "Scala 2.13 API with cats-effect and http4s.",
            "POST /users/{userId}/interests creates profiles.",
            "GET /users/{userId}/feed returns personalized feed items.",
            "GET /posts and /demo/users support inspection and demos.",
            "Dashboard shows indexed posts, demo users, feed cards, score breakdowns.",
        ],
    },
    {
        "title": "Live Demo Script",
        "presenter": "Presenter 2",
        "bullets": [
            "make up && make create-topics",
            "make convert-recsys RECSYS_LIMIT=100",
            "make replay",
            "make seed-demo-users && make get-feed",
            "Open http://localhost:8080",
            "Show indexed count, demo feed, and custom profile form.",
        ],
    },
    {
        "title": "Evaluation And Test Coverage",
        "presenter": "Presenter 2",
        "bullets": [
            "Evaluation type: functional and qualitative.",
            "Producer tests: RecSys conversion, limits, JSONL replay validation.",
            "Spark tests: malformed records, unsupported language, short text, duplicates.",
            "API tests: profile seeding, vector averaging, routes, ranking behavior.",
            "No CTR, NDCG, or online A/B result is claimed.",
        ],
    },
    {
        "title": "Limitations And Future Work",
        "presenter": "Presenter 2",
        "bullets": [
            "Limitations: rule-based ranking, no collaborative filtering, no impression history.",
            "RecSys token text needs vocabulary/preprocessing for best semantic quality.",
            "Future: use engagement columns for learned ranking.",
            "Future: larger RecSys runs and full-corpus experiments.",
            "Future: latency metrics, Kafka lag monitoring, multi-replica Kubernetes tests.",
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


def text_shape(shape_id: int, x: int, y: int, cx: int, cy: int, lines: list[tuple[str, int, str, bool]]) -> str:
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

    lines = [(title, 3800 if index > 1 else 5200, "0F766E", True)]
    if subtitle:
        lines.append((subtitle, 2600, "17201C", False))
    title_shape = text_shape(2, 620000, 360000, 10900000, 1050000, lines)

    bullet_lines = [(f"- {item}", 1900, "17201C", False) for item in bullets]
    body_shape = text_shape(3, 800000, 1750000, 10600000, 3900000, bullet_lines)
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
