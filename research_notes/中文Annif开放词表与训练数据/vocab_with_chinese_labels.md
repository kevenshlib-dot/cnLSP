# Openly licensed vocabularies with Chinese (简体/繁体) labels usable as an Annif vocabulary

Research date: 2026-10-13. Concept counts marked "(live query 2026-10-13)" were obtained by the researcher running SPARQL/API queries against the publishers' official endpoints on that date. They are exact for that date but depend on how each query was written; the query logic is noted. Counts not marked that way come from the publisher pages that are cited.

## Q1. Which candidate vocabularies have Chinese labels, how complete, and under what license?

### Takeaway
Five sources have **open licenses, good Chinese coverage and machine-readable data**: FAO AGROVOC, GEMET, the Taiwan National Central Library (NCL) 中文主題詞表 CSV, Getty AAT (Traditional Chinese for about half its concepts) and Wikidata. AGROVOC (CC BY 4.0) has zh labels on almost all of its ~42k concepts. GEMET (CC BY 4.0) has about 5.2k of ~5.6k. The NCL 中文主題詞表 (Taiwan Open Government Data License v1.0) has ~17k preferred headings, all general-domain, in 繁体, with 中文圖書分類法 class numbers. Four vocabularies **lack Chinese entirely**: the UNESCO Thesaurus, EuroVoc, MeSH and UDC Summary in practice (UDC Summary also became NC-licensed). The mainland Chinese national schemes (中图法, 中分表/汉语主题词表, CMeSH, STKOS, GB/T 13745) have **no open license** that I could find.

### Inventory table (summary)

| Vocabulary | Publisher | License (production OK?) | Concepts total | Concepts with zh | Script | Relations | Access |
|---|---|---|---|---|---|---|---|
| AGROVOC | FAO + community | CC BY 4.0 for en/fr/es/ar/ru/**zh** content (yes, commercial OK) | 41,999 skos:Concept | 41,855 with zh prefLabel; 8,677 zh altLabels | 简体 | broader/narrower (42,446 skos:broader triples), related, many external mappings | SPARQL https://agrovoc.fao.org/sparql, monthly RDF/NT dumps, Skosmos |
| GEMET 4.2.3 | European Environment Agency (Eionet) | CC BY 4.0 (yes) | ~5,573 (en prefLabels in the export) | ~5,208 zh-CN prefLabels, with zh definitions | 简体 | groups/themes, broader/narrower, related | SKOS RDF dump gemet.rdf.gz, per-language RDF, REST API |
| NCL 中文主題詞表 (中文主題編目規範) | National Central Library, Taiwan (國家圖書館) | 政府資料開放授權條款 第1版 (Taiwan OGDL v1.0), free | 19,325 rows | all zh: 17,125 preferred + 2,200 non-preferred (USE) entries | 繁体 | USE/UF, 參見 (RT-like), class numbers (中文圖書分類法 8th ed. and 2007 ed.) | CSV download from data.gov.tw / ncl.edu.tw |
| Getty AAT | Getty Research Institute | ODC-By 1.0 (yes, attribution; **not re-verified this session**, see Gaps) | 57,572 gvp:Concept | 27,472 with zh-hant skos:prefLabel; 674,330 term objects tagged Chinese language (includes pinyin/Wade-Giles variants) | 繁体 (+pinyin) | full polyhierarchy, facets, guide terms | SPARQL https://vocab.getty.edu/sparql, LOD dumps |
| Wikidata | Wikimedia | CC0 (yes) | millions | e.g. 40,912 LCSH-linked items have a zh label (of 59,154 LCSH-"sh"-linked items); 6,659 of 6,724 NLC-authority-linked items have zh | 简/繁 variants (zh, zh-hans, zh-hant, zh-cn, zh-tw…) | P279/P31/P361; no thesaurus-grade hierarchy | SPARQL query.wikidata.org, JSON dumps |
| UNESCO Thesaurus | UNESCO | CC BY-SA 3.0 IGO | 4,500 | **0** | — | BT/NT/RT, microthesauri | SPARQL, Skosmos |
| EuroVoc | EU Publications Office | (EU reuse) | 7,515 en prefLabels in scheme | **0** | — | — | SPARQL |
| UDC Summary | UDC Consortium | **CC BY-NC 4.0** (non-commercial; blocks production) | ~2,600 classes | a Chinese (中文) interface/translation exists; completeness unverified | ? | hierarchy | exports by email request only |
| 中图法 CLC 5th ed. | NLC + 编委会 | none (copyrighted, paid Web版 with login) | — | all zh | 简体 | hierarchy | clc.nlc.cn (login); unofficial GitHub scrapes |
| 中分表 / 汉语主题词表 | NLC / ISTIC | none found | — | all zh | 简体 | full thesaurus | Web版 with login |
| STKOS 超级科技词表 | NSTL / 中科院文献情报中心 | none found | — | all zh | 简体 | — | sharestkos.las.ac.cn ("customized download") |
| CMeSH | 中国医学科学院医学信息研究所 (per common knowledge; unverified) | subscription e-resource | — | all zh | 简体 | MeSH tree | institutional login |
| GB/T 13745 学科分类与代码 | SAMR/SAC | recommended standard: copyrighted per 1998/1999 official replies | ~ (not counted) | all zh | 简体 | 3-level codes | read-only view at openstd.samr.gov.cn (not verified this session) |

### Cited Findings

**AGROVOC (FAO)**
- AGROVOC content in English, Russian, French, Spanish, Arabic and Chinese is "licensed under the Creative Commons Attribution 4.0 International (CC-BY-4.0)", which allows sharing and adaptation "for any purpose, even commercially". Copyright for the FAO-language content is with FAO; other languages rest with their authoring institutions. — [FAO AGROVOC maintenance page](https://www.fao.org/agrovoc/index.php/maintenance)
- Conflict: FAO's access page instead describes the content as CC-BY IGO 3.0. The maintenance page (CC BY 4.0) is more explicit and is corroborated by the download page as reported by Bioregistry. — [Access to AGROVOC](https://aims.fao.org/standards/agrovoc/access-agrovoc); [Bioregistry](https://bioregistry.io/agrovoc)
- Live query 2026-10-13: 41,999 `skos:Concept`; 41,855 concepts have a `skosxl:prefLabel` with language tag `zh`. The only zh-family tag is plain `zh`, with 41,858 zh prefLabels. There are 8,677 zh altLabels and 42,446 `skos:broader` triples. Example: c_8373 has the prefLabel "小麦". The scheme's dct:modified is 2026-10-07. — [AGROVOC SPARQL endpoint](https://agrovoc.fao.org/sparql)
- Two distributions exist: CORE (concepts only, RDF/NT) and LOD (concepts plus external links, NT/NQ). Updates are released monthly. — [Access to AGROVOC](https://aims.fao.org/standards/agrovoc/access-agrovoc)
- Annif's own tutorial/demo ecosystem already uses AGROVOC, so the tooling fit is proven (general knowledge; not re-verified this session).

**GEMET (EEA/Eionet)**
- GEMET version 4.2.3 is licensed CC BY 4.0. It offers a full SKOS dump (`/gemet/latest/gemet.rdf.gz`), per-language label/definition RDF, broader/narrower RDF, and backbone (groups/themes) RDF. It has 37 languages, including Chinese. — [GEMET RDF exports page](https://www.eionet.europa.eu/gemet/en/exports/rdf/latest)
- Live query 2026-10-13: the zh-CN definitions export contains 5,208 `skos:prefLabel` lines; the English export contains 5,573. The API returns zh-CN prefLabel and definition, e.g. concept 7970 = "太空旅行". The language code is `zh-CN`, not `zh`. — [GEMET getConcept API](https://www.eionet.europa.eu/gemet/getConcept?concept_uri=http://www.eionet.europa.eu/gemet/concept/7970&language=zh-CN)

**Taiwan NCL 中文主題詞表 (dataset "中文主題編目規範 / Chinese Subject Headings Standard")**
- The publisher is the National Central Library. The license is the Open Government Data License, version 1.0. The data is a free CSV, updated irregularly. The metadata was last updated 2026-09-23 (first published 2016-02-17). The dataset is described as providing Chinese subject headings and 中文圖書分類法. — [data.gov.tw dataset 27190](https://data.gov.tw/en/datasets/27190)
- Direct CSV URL: https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137 (about 1.4 MB, UTF-8 with BOM). Columns: 序號, 主題詞, 類號八版, 類號2007版, 原文, 注釋文字, 用, 不用, 參見, 網址. — [NCL CSV](https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137)
- Researcher's parse of the CSV (2026-10-13):
  - 19,325 rows: 17,125 preferred headings (empty 用 field) and 2,200 lead-in (USE) entries.
  - Class numbers: 16,869 preferred headings have an 8th-ed. class number and 14,984 have a 2007-ed. number.
  - Other fields: 1,848 have 不用 (UF), 1,288 have 參見 (see-also), 327 have scope notes, and 3,305 have an English/original-language equivalent.
  - Data quality: there are some issues, such as mixed `；`/`;` separators, bracketed multi-class values and occasional malformed numbers. — [NCL CSV](https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137)
- The headings are general-domain (examples: 301貿易法案, A型肝炎, 部落格, 動漫). The file has no explicit BT/NT, but the 中文圖書分類法 class numbers can serve as a pseudo-hierarchy. — same source
- The NCL catalog-standards site is catsmart.ncl.edu.tw (catbase.ncl.edu.tw is also mentioned). The 2007 edition of 中國圖書分類法 (賴永祥 ed., 9th ed.) was first released on the 中文主題編目規範 website. — [data.gov.tw search result / dataset 27190](https://data.gov.tw/dataset/27190)

**Getty AAT**
- Live query 2026-10-13 at the Getty SPARQL endpoint:
  - 57,572 `gvp:Concept` in the AAT scheme.
  - 27,472 concepts have a `skos:prefLabel` tagged `zh-hant`.
  - 674,330 term objects have `dct:language` = aat:300388113 (Chinese). These include pinyin (`zh-latn-pinyin-x-hanyu`, `-x-notone`) and Wade-Giles (`zh-latn-wadegile`) forms.
  - Example: aat:300011914 (wood) has "木材 (植物材料)" and "木" (zh-hant). — [Getty Vocabularies SPARQL](https://vocab.getty.edu/sparql)
- The Chinese is Traditional only and art/architecture/material-culture oriented, so it fits poorly for general books. A 簡體 conversion (e.g. OpenCC) would be needed for mainland users. — inference from the data above
- License: Getty LOD has long been published under ODC-By 1.0. I could not re-load the Getty licensing page this session because of a redirect to a truncated page. — [Getty data services page](http://www.getty.edu/research-conservation/tools-databases/vocabularies/data-services/) (unverified)

**Wikidata**
- Live query 2026-10-13 (query.wikidata.org):
  - 59,154 items carry an LCSH subject ID (P244 starting "sh"); 40,912 of them (~69%) have a `zh` label.
  - 6,724 items carry NLC authorities (P1213); 6,659 of them have a `zh` label.
  - Only 47 items carry Chinese Library Classification (P1189), so Wikidata is not a usable CLC source.
  - 14,207 items with a DDC (P1036) value have a zh label. — [Wikidata Query Service](https://query.wikidata.org/sparql)
- Wikidata labels exist in multiple zh variants. Example: Q11660 has "人工智能" under zh/zh-hans/zh-cn and "人工智慧" under zh-tw/zh-hant. — same source
- License: Wikidata structured data is CC0 (general knowledge; Wikidata:Licensing not fetched this session).

**UNESCO Thesaurus**
- Live query 2026-10-13: 4,500 concepts with prefLabels in en/fr/es/ar (4,459 ru). **Zero** literals with any zh language tag in the whole endpoint. License: `dct:license` CC BY-SA 3.0 IGO; dct:modified 2026-08-31. — [UNESCO vocabularies SPARQL](https://vocabularies.unesco.org/sparql)

**EuroVoc**
- Live query 2026-10-13 on the EU Publications Office endpoint: 7,515 concepts in scheme 100141 with en prefLabels, and **no zh/zh-hans/zh-cn prefLabels**. — [EU Publications Office SPARQL](https://publications.europa.eu/webapi/rdf/sparql)

**UDC Summary**
- The UDC Summary has ~2,600 classes and lists "Chinese (中文)" among its languages. Its data is "released under the Creative Commons Attribution-NonCommercial 4.0 International license". Export files (txt/Word/Excel/XML/linked data) are "available on demand" by emailing udcs@udcc.org. Many translations are "not proofread". — [UDC Summary exports page](https://udcsummary.info/exports.htm); [UDC Summary zh page](https://udcsummary.info/php/index.php?lang=zh)
- The fetched page summary stated the NC license applies "starting in 2026". Earlier UDC Summary releases were CC BY-SA 3.0 (general knowledge). The exact change date should be confirmed before relying on an older copy. — [UDC Summary](https://udcsummary.info/php/index.php?lang=zh)

**中国图书馆分类法 (中图法) / 中国分类主题词表 (中分表) / 汉语主题词表**
- clc.nlc.cn is the official 《中图法》 site. It has sections for the 第五版简表 (abridged table), 电子版 and Web版, and a username/password login for the Web版. The 5th edition was published in 2010; the Web试用版 launched in 2011-12; the Web版 and 《中分表》Web2.1版 were updated in 2014-01. 《中分表》 was built from 《中图法》 and 《汉语主题词表》; it was first published in 1994, with a 2nd edition in 2005-09. — [《中图法》网站 clc.nlc.cn](http://clc.nlc.cn/)
- The site offers an "出版征订" (subscription/ordering) section. I found no open-license statement for the full schedules or for 中分表. — [clc.nlc.cn](http://clc.nlc.cn/); search found no license info ([lis.ac.cn article on 中分表 networking](https://www.lis.ac.cn/CN/Y2005/V49/I7/25), [图书馆研究 2018 on 中分表 Web版](https://tsgyj.jxlibrary.net/CN/Y2018/V48/I5/7))
- The top 22 basic classes (A–Z) of 中图法 are widely reproduced publicly, e.g. on Wikipedia. — [Wikipedia: Chinese Library Classification](https://en.wikipedia.org/wiki/Chinese_Library_Classification)
- A 2008 DC-conference pilot encoded part of 中分表 (CCT) in SKOS and compared it with OWL-lite/RDFS. — [DC papers: SKOS for an Integrated Vocabulary Structure](https://dcpapers-past.dublincore.org/pubs/article/view/935)
- Chinese KOS researchers note that a Chinese classification scheme "would lose a considerable part of its original semantics if it is modeled only in SKOS". They propose a CNKOS (SKOS+CKOS) extension. — [Formal Semantic Description Standard Family for Chinese KOS (SZU NKOS 2025)](https://www.lib.szu.edu.cn/nkos2/sites/default/files/2025-06/Formal%20Semantic%20Description%20Standard%20Family%20for%20Chinese%20KOS.pdf)

**STKOS 超级科技词表 (NSTL)**
- STKOS has a term publishing and sharing platform at http://sharestkos.las.ac.cn/ with browse, retrieval and "customized download" functions. Papers describe standards-based open interfaces. I found no license statement. — [Construction of STKOS Term Publishing and Sharing Service Platform (现代图书情报技术 2015)](https://manu44.magtech.com.cn/Jwk_infotech_wk3/CN/Y2015/V31/I9/76); [STKOS service interface paper 2014](https://manu44.magtech.com.cn/Jwk_infotech_wk3/CN/Y2014/V30/I7/9)

**CMeSH**
- PolyU Library lists "CMeSH (Chinese Medical Subject Headings) 中文醫學主題詞表" as a database e-resource behind institutional login. It is not openly licensed. — [PolyU Library CMeSH](https://www.lib.polyu.edu.hk/node/25167)

**GB/T 13745 学科分类与代码 and other GB/T standards**
- Official replies distinguish two cases. Mandatory standards are regulatory technical norms and fall outside copyright. Recommended (推荐性, i.e. GB/T) standards "属于著作权法保护的范围" (国家版权局 权司〔1999〕50号; 最高人民法院 〔1998〕知他字第6号). GB/T 13745 is a recommended standard, so free online reading is not a license to redistribute its code table. — [elawcn summary of the replies](https://www.elawcn.com/rule/2022/1219/1208.html); [elawcn](https://www.elawcn.com/rule/2022/1219/1209.html)

### Inferences
- **Production-safe (permissive) licenses:**
  - AGROVOC: CC BY 4.0 for zh.
  - GEMET: CC BY 4.0.
  - Getty AAT: ODC-By, pending re-verification.
  - Wikidata: CC0.
  - Taiwan OGDL v1.0: an attribution-style government open data license, generally considered compatible with CC BY 4.0. I did not fetch the license text this session, so confirm its terms before production.
- **Blocks or complicates production:**
  - UDC Summary: CC BY-NC 4.0 blocks commercial use.
  - UNESCO: CC BY-SA 3.0 IGO is share-alike, and it has no zh anyway.
  - 中图法, 中分表, 汉语主题词表, CMeSH, STKOS, GB/T 13745: no open license; all-rights-reserved or subscription.
  - GitHub scrapes of 中图法: no license, and they derive from copyrighted schedules.
- **Annif language codes:** AGROVOC uses `zh` and GEMET uses `zh-CN`. Annif's `annif load-vocab --language` expects one language code, so normalize the tag (e.g. rewrite GEMET `zh-CN` → `zh`) before loading.

### Gaps
- I did not re-verify the Getty AAT license (ODC-By 1.0) from the primary page; the page redirected and the fetched content was truncated.
- I did not fetch the Wikidata CC0 statement or the Taiwan OGDL v1.0 license text.
- No zh completion statistics for UDC Summary (the "completion stats" page was not fetched). UDC exports require email, so the exact NC-change date is unconfirmed.
- DBpedia, ConceptNet, the Chinese Wikipedia category tree, ISO/ICS and MeSH were **not investigated** with live queries this session. From general knowledge, all unverified:
  - ConceptNet 5 is CC BY-SA 4.0 and has zh nodes, but it is a commonsense graph, not a subject vocabulary.
  - Wikipedia category structure is CC BY-SA and noisy.
  - MeSH (NLM) has no Chinese labels; CMeSH is a separate licensed product.
  - ICS is ISO-copyrighted, and its Chinese version is a SAC publication.
- No license, size or download information for STKOS beyond the platform description.
- The GB/T 13745 concept count and its openstd.samr.gov.cn read-only status were not checked this session.

## Q2. Which are best as a demo (broad general coverage, a few thousand to tens of thousands of concepts, clean zh labels)?

### Takeaway
For a **general Chinese books/papers** demo there are two candidates. The **NCL 中文主題詞表** is the only open, library-grade, general-domain Chinese subject heading list (~17k headings, 繁体, OGDL v1.0). **Wikidata-derived subject sets** (e.g. the ~41k LCSH-linked items with zh labels, CC0) are a 简体-friendly alternative. **AGROVOC** is the cleanest, most Annif-ready SKOS vocabulary with full zh coverage, but it is domain-specific (agriculture, food, environment). **GEMET** (~5.2k zh concepts, CC BY 4.0) is a small, tidy environment-domain demo.

### Cited Findings
- AGROVOC has zh prefLabels on 41,855 of 41,999 concepts (99.7%), plus hierarchy, a monthly release and CC BY 4.0. — [AGROVOC SPARQL](https://agrovoc.fao.org/sparql); [FAO maintenance](https://www.fao.org/agrovoc/index.php/maintenance)
- GEMET has ~5,208 zh-CN prefLabels of ~5,573, CC BY 4.0, and a SKOS dump. — [GEMET exports](https://www.eionet.europa.eu/gemet/en/exports/rdf/latest)
- NCL CSV: 17,125 general-domain preferred headings, 98.5% of them carrying a 中文圖書分類法 class number, under OGDL v1.0. The metadata was updated 2026-09-23. — [data.gov.tw 27190](https://data.gov.tw/en/datasets/27190); [NCL CSV](https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137)
- Wikidata: 40,912 LCSH-linked items have zh labels, and 6,659 NLC-authority-linked items have zh labels. — [Wikidata Query Service](https://query.wikidata.org/sparql)
- Getty AAT has 27,472 concepts with zh-hant prefLabels. — [Getty SPARQL](https://vocab.getty.edu/sparql)

### Inferences
- **Recommended demo stack:**
  1. **AGROVOC (zh)**: the first "it just works" demo. Annif loads it directly from the Turtle/NT dump with `--language zh`. Pair it with Chinese agricultural abstracts.
  2. **NCL 中文主題詞表 → TSV/SKOS**: the general-library demo.
     - URIs: there are no official URIs, so mint them, e.g. `https://catsmart.ncl.edu.tw/#<序號>` or a local namespace, and record the source and license.
     - Labels: 主題詞 becomes the prefLabel and 不用 becomes altLabels.
     - Relations: 參見 becomes skos:related, and the class-number prefixes can serve as a broader-like grouping.
     - Simplified version: convert with OpenCC (t2s) for 简体 users, keeping the 繁体 form as the `zh-Hant` label.
     - Annif's simple TSV format (`<URI>\tlabel`) is the fastest route; SKOS is needed only for hierarchy-aware features and the web UI's display.
  3. **Wikidata subset**: e.g. items with P244 (LCSH sh-IDs) or P2163 (FAST) and a zh label give a CC0, general-domain vocabulary of tens of thousands of concepts, with zh-hans/zh-hant variants. The hierarchy is weak (P279 is noisy), and the subject granularity mirrors LCSH.
- GEMET is a good small, clean SKOS sample for classroom exercises (load times of seconds).
- Getty AAT suits only art/museum demos. Its zh-hant coverage is about 48% of concepts.
- None of the open options gives 简体 general-library subject headings aligned with mainland practice (中图法/中分表). This gap could only be filled under a license from NLC.

### Gaps
- I did not test-load any of these into Annif this session, and I did not check training-corpus availability for each vocabulary (another researcher covers training data).
- The FAST-linked Wikidata zh count (P2163) query timed out, so it is unknown.
- I did not assess the quality of NCL zh headings against mainland usage, e.g. 部落格 vs 博客, beyond spot checks.

## Q3. Are there existing SKOS conversions on GitHub of any Chinese classification/thesaurus?

### Takeaway
I found **no SKOS/RDF conversion** of any Chinese classification or thesaurus on GitHub. There are only JSON/Markdown scrapes of 中图法 (unlicensed) and a JSON of the 中文圖書分類法 index. The only published SKOS work on 中分表 is a 2008 pilot paper, which did not release a dataset. Converting the NCL CSV to SKOS would be new work.

### Cited Findings
- GitHub search for 中图法 / 中国图书馆分类法 / chinese library classification (run with `gh search repos`, 2026-10-13) found these repos:
  - `acdzh/Chinese-Library-Classification` (28★, no license): clc.json is 6.5 MB and clc.md is 1.7 MB, apparently the full CLC.
  - `amoblin/BookTree` (27★, no license).
  - `tinycourses/library_classification` (75★, no license): includes 中国图书馆分类法（第5版）.md (607 KB) and LCC.
  - `sunshineplan/go-clc` (MIT code).
  - `FeiH36/library-classification` (Apache-2.0 code).
  - `sheoguo/CLC-data-scraping` (MIT): scraping code.
  - `abc202306/obsidian-example-vault-chinese-library-classification` and `abc202306/obsidian-example-vault-chinese-thesaurus`: Obsidian vaults of 中图法 classes and 汉语主题词表 terms.

  None of them is SKOS. — [GitHub: acdzh/Chinese-Library-Classification](https://github.com/acdzh/Chinese-Library-Classification); [GitHub: tinycourses/library_classification](https://github.com/tinycourses/library_classification); [GitHub: abc202306/obsidian-example-vault-chinese-thesaurus](https://github.com/abc202306/obsidian-example-vault-chinese-thesaurus)
- `galaxy4552/ChineseBookClassificationSystem` holds 中文圖書分類法索引 as JSON: 11 small files, about 3.5 KB each, apparently the top two levels. It has no license. — [GitHub: galaxy4552/ChineseBookClassificationSystem](https://github.com/galaxy4552/ChineseBookClassificationSystem)
- Searches for "skos chinese thesaurus", "學科分類 skos" and "GB/T 13745" returned no relevant repos. — `gh search repos` (researcher's run)
- The Zeng/Fan/Lin 2008 CCT SKOS pilot exists as a conference paper. — [DC papers](https://dcpapers-past.dublincore.org/pubs/article/view/935)
- A Bliss Classification SKOS conversion (Python + RDFLib, Code4Lib Journal 2024) is a methodological template, not Chinese. — [Code4Lib Journal Issue 59](https://journal.code4lib.org/articles/18073)

### Inferences
- The GitHub 中图法 scrapes are useful for **private teaching experiments** only. Redistributing them, or using them in production, would be infringement-risky, because the source is copyrighted NLC material and the repos carry no license.
- Converting NCL CSV → SKOS (Turtle) plus a TSV is low effort, about 100 lines of Python/RDFLib. Publishing the result is permitted under OGDL v1.0 with attribution; confirm the license text first.

### Gaps
- GitHub code search (as opposed to repo search) for `.ttl`/`.rdf` files containing Chinese prefLabels was not run.
- Gitee (码云) was not searched; Chinese-hosted conversions may exist there.
