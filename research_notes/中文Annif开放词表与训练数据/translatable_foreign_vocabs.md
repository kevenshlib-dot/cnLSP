# Foreign (mainly English) subject vocabularies and classifications that could be translated into Chinese for an Annif demo

Research date: 2026-10-13. Wikidata counts are my own SPARQL queries, run on 2026-10-13 against QLever's Wikidata mirror (https://qlever.dev/api/wikidata). I cross-checked one count against the official WDQS (https://query.wikidata.org/sparql). WDQS timed out on every query that filtered on labels, so all Chinese-label counts come from QLever. The query text is given below so the counts can be re-run.

Count queries used (a "zh label" means a label in any of zh, zh-hans, zh-cn, zh-hant, zh-tw or zh-hk):
```sparql
SELECT (COUNT(DISTINCT ?item) AS ?n) WHERE {
  ?item wdt:P244 ?id . FILTER(STRSTARTS(?id,"sh"))      # LCSH IDs start with "sh"
  ?item rdfs:label ?l . FILTER(LANG(?l)="zh"||LANG(?l)="zh-hans"||LANG(?l)="zh-cn"||LANG(?l)="zh-hant"||LANG(?l)="zh-tw"||LANG(?l)="zh-hk") }
```
The same query with P2163 (FAST), P2347 (YSO), P3911 (STW), P486 (MeSH), P1014 (AAT), P1036 (DDC), P3916 (UNESCO) and P1149 (LCC).

## Q1. LCSH and LCC: public-domain status, bulk download, size and structure, and Chinese labels via Wikidata

### Takeaway
LCSH is a US-government work, available as free bulk SKOS or MADS RDF downloads from id.loc.gov (SKOS Turtle is about 40 MB gzipped). It has roughly 340k or more authority records, and its strings are heavily pre-coordinated. Only about 58.8k Wikidata items carry an LCSH "sh" ID, and about 40.8k of those have some Chinese label. That covers about 12% of LCSH, and only about half of those labels are tagged zh-hans. LCC has no bulk RDF download on id.loc.gov, only free PDF schedules. That makes LCC a poor choice of vocabulary, although it is useful as a hierarchy or context signal.

### Cited Findings
- id.loc.gov offers LCSH bulk exports in two models. MADS/RDF files are JSON-LD 141 MB, N-Triples 231 MB, Turtle 95 MB and RDF/XML 167 MB. SKOS/RDF files are JSON-LD 67 MB, N-Triples 101 MB, Turtle 40 MB and RDF/XML 72 MB. All are gzipped (e.g. `/download/authorities/subjects.skosrdf.ttl.gz`). The same page also has LC Children's Subject Headings (SKOS Turtle 2 MB), LCGFT genre/form terms (SKOS Turtle 337 KB) and LCDGT. Checked by parsing the live page on 2026-10-13. — [id.loc.gov download page](https://id.loc.gov/download/)
- The download page says decompressed files can be about 10 times larger than the gzipped ones. A bulk-export pilot made the JSON-LD and XML files newline-delimited (one self-contained record per line) and added a VoID file with the export date and MD5 hash. — [lcnetdev/lc-bulk-export-pilot](https://github.com/lcnetdev/lc-bulk-export-pilot); [id.loc.gov download](https://id.loc.gov/download/)
- The LC download page has no LCC bulk RDF file. The only LCC-related bulk items are "Experimental Embeddings Data by LCC": bibliographic embeddings split by LCC class letter (Amazon Titan embed v2), with the no-LCC file alone at 31 GB. These embeddings are not the LCC schedule. — [id.loc.gov download](https://id.loc.gov/download/)
- LC publishes free print-ready PDFs of the LCC schedules (data selected May 2024). Full functionality is in the paid Classification Web product. — [LC FreeLCC](https://loc.gov/aba/publications/FreeLCC/freelcc.html)
- Size: LCSH 40 (January 2018) had 342,947 subject authority records. I found no official 2025 or 2026 count. — [ALA LRTS article](https://journals.ala.org/lrts/article/download/5430/6667) (as summarized in search; not opened in full)
- Public-domain status: Wikipedia lists the LC Linked Data Service content license as public domain. An LC staff member described the service as making government data "publicly and freely available" in the spirit of the Open Government directive. I could not retrieve an explicit rights statement on id.loc.gov (WebFetch got HTTP 403). — [Wikipedia: LC Linked Data Service](https://en.wikipedia.org/wiki/Library_of_Congress_Linked_Data_Service); [Kevin Ford, public-lod 2013](https://lists.w3.org/Archives/Public/public-lod/2013Apr/0099.html)
- LCSH entries contain the corresponding LCC number, the heading and its non-preferred terms, scope or usage notes, and references (BT, NT, RT, UF). — [中国大百科全书《美国国会图书馆标题表》](https://www.zgbk.com/ecph/words?SiteID=1&Name=%E3%80%8A%E7%BE%8E%E5%9B%BD%E5%9B%BD%E4%BC%9A%E5%9B%BE%E4%B9%A6%E9%A6%86%E6%A0%87%E9%A2%98%E8%A1%A8%E3%80%8B&Type=bkzyb&subSourceType=000003000012000001&SourceID=80861)
- Wikidata counts (own queries, 2026-10-13):
  - 58,796 items have an LCSH "sh" ID (P244). WDQS returned 58,791 for the same query, so the two engines agree.
  - 40,793 of those items have any Chinese label.
  - Only 20,261 have a `zh-hans` label.
  - 7,219 items have an LCC (P1149) value, and 2,810 of them have a Chinese label.
  — [QLever Wikidata endpoint](https://qlever.dev/api/wikidata); [WDQS](https://query.wikidata.org/sparql)
- A sample of 25 LCSH–zh label pairs (offset 20000) shows these quality problems:
  - Simplified and traditional script are mixed under the generic `zh` tag (近場通訊, 牙醫, 宇宙暴脹 next to 化学合成, 结膜).
  - One Wikidata item can carry two LCSH IDs. "association football" → 足球 appears for both sh85123840 and sh2009000938.
  - Some labels are Wikipedia-article style: "Islam in the United States" → 在美國的伊斯蘭教, "memento mori" → 死亡象征, "dhimmi" → 齐米 (a transliteration).
  - Many matches are named entities or species (Pellaea calomelanos → 三角羽旱蕨) rather than topical concepts.
  — [QLever Wikidata endpoint](https://qlever.dev/api/wikidata) (own query)
- The Taiwan National Central Library cataloging site treats LCSH (「國會圖書館標題表」) as a reference standard and points to the weekly LCSH change lists. My search found no official full Chinese translation of LCSH from NCL or NLC. — [NCL 編目園地](https://catweb.ncl.edu.tw/standard/page/25589); [《美国国会图书馆标题表》第十版简介](https://ccj.pku.edu.cn/Article/info?aid=292882170)

### Inferences
- Wikidata covers about 58.8k of at least 343k LCSH records (about 17%), and about 40.8k of 343k (about 12%) have Chinese labels. The aligned items are biased toward entities and Wikipedia-worthy topics. Common pre-coordinated strings ("China—History—1949-1976", "Economic development—Social aspects") will almost never have a Wikidata match.
- For Annif, LCSH's pre-coordination is the main obstacle. Each heading-plus-subdivision string is a separate "concept", which explodes the label space and makes training data sparse. A demo would need to strip LCSH to main headings, or split each string into its main heading and subdivisions (essentially what FAST does).
- LCSH carries the least licensing risk for later production (US federal work). That point needs explicit confirmation from LC's legal pages.
- LCC is best used as the hierarchy or broad-class signal, or as a separate small Annif "class" vocabulary built from the top two or three levels translated by hand (a few hundred classes). It should not be the main concept vocabulary.

### Gaps
- No current (2025/26) official LCSH record count. The fix is to download `subjects.skosrdf.ttl.gz` and count `skos:Concept`. I did not download it in this session.
- I did not retrieve the exact rights or legal wording on id.loc.gov (HTTP 403 to the fetch tool). Check https://www.loc.gov/legal/ and the id.loc.gov "About" or terms pages manually.
- I found no published Chinese translation of the full LCSH (no 美国国会图书馆主题词表中译 project), whether in print or open data. Absence is not proof that none exists.

## Q2. OCLC FAST: license, size, download, why it is easier than LCSH, and Wikidata mappings

### Takeaway
FAST is ODC-By (attribution only). That is acceptable for production. It is downloadable in full or per facet as SKOS N-Triples or MARC XML, last updated 10 Oct 2024. It is derived from LCSH but faceted and post-coordinated, so each topical heading is a flat Annif concept. Wikidata has 464,839 items with FAST IDs. Most are people; 28,194 are non-person items, and 20,801 of those have Chinese labels.

### Cited Findings
- License: "made available by OCLC under the Open Data Commons Attribution License (ODC-By)". Users are asked to attribute FAST in derived works using a template ("contains information from FAST Data … made available by OCLC Online Computer Library Center, Inc. under the ODC Attribution License"). — [OCLC FAST Dataset Download](https://www.oclc.org/research/areas/data-science/fast/download.html); [FAST Linked Data](https://fast.oclc.org/fast)
- History: before 2012, full dumps were available only under a research licence. ODC-By applied first to the linked data release (Dec 2011), then to the dump. — [open-bibliography list, Jan 2012](https://lists-archive.okfn.org/pipermail/open-bibliography/2012-January/005331.html)
- Formats: MARC XML, RDF N-Triples and ISO MARC, as the full set or per facet. Zipped sizes are:
  - All: 266 MB (NT) / 198 MB (MARC XML)
  - Topical: 46 MB NT / 35 MB MARC XML
  - Geographic: 28 MB NT
  - Personal: 111 MB NT
  - Corporate: 67 MB NT
  - Uniform Titles: 9 MB NT
  - Event: 2 MB NT
  - FormGenre: 343 KB NT
  - Chronological: 48 KB NT
  - Meeting: 1 MB NT

  The page says FAST was "last updated on 10 October 2024". It gives no record counts per facet. — [OCLC FAST Dataset Download](https://www.oclc.org/research/areas/data-science/fast/download.html)
- Facets: Personal Names, Corporate Names, Events, Uniform Titles, Chronological, Topical, Geographic, Form/Genre (plus Meeting in the file list). — [OCLC FAST download](https://www.oclc.org/research/areas/data-science/fast/download.html); [bespacific announcement](https://www.bespacific.com/?p=29531)
- Wikidata counts (own queries, 2026-10-13):

  | FAST ID (P2163) items | Count |
  |---|---|
  | All items | 464,839 |
  | With any Chinese label | 115,314 |
  | Excluding instances of human (Q5) | 28,194 |
  | Non-human with a Chinese label | 20,801 |
  | Having both a FAST ID and an LCSH "sh" ID plus a Chinese label | 7,176 |

  — [QLever Wikidata endpoint](https://qlever.dev/api/wikidata)

### Inferences
- FAST is easier than LCSH for Annif for these reasons:
  1. Topical headings are standalone concepts. Subdivisions are split out as separate facets, so there is no combinatorial heading-string explosion.
  2. It is a flat concept list with `skos:broader`/`related`, which maps cleanly to Annif's TSV or SKOS vocabulary format.
  3. Records cataloged with LCSH can be converted to FAST mechanically. This is OCLC's FAST-from-LCSH conversion, which WorldCat applies at scale (my background knowledge, not verified this session). Chinese-language MARC records with LCSH therefore yield FAST training labels.
- The Wikidata FAST alignment is mostly people. The topical portion with zh labels is only about 20k items, and many are places or works. LLM translation will be needed for most topical FAST terms.
- For a demo, filter FAST Topical (and optionally Geographic) to headings that occur at least N times in the actual Chinese-book training set. That should give a few thousand to about 30k concepts.

### Gaps
- Per-facet record counts for FAST were not on the download page. Commonly cited figures (about 1.7M+ headings in total, several hundred thousand topical) are from memory and unverified. Count `skos:Concept` in `FASTTopical.nt` to get the real number.
- Whether FAST is still maintained beyond the 10 Oct 2024 update is not stated. It is worth checking OCLC news for 2025/26 updates.

## Q3. Other candidates: DDC, UDC Summary, YSO/KOKO, STW, GND, MeSH, Getty AAT, UNESCO Thesaurus

### Takeaway
Among the openly licensed vocabularies, YSO (about 33k concepts, CC BY 4.0, 20.5k with Wikidata zh labels) and STW (about 6k descriptors, CC BY 4.0, 4.1k with zh labels) are the cleanest and most Annif-native. They do not match how Chinese books are cataloged, though. DDC is proprietary, so it blocks production. UDC Summary and UNESCO are share-alike. CMeSH (the Chinese MeSH) is proprietary to the Chinese Academy of Medical Sciences (CAMS). AAT is ODC-By and has an official Chinese translation effort (AAT-Taiwan), but the licence of the Chinese data is unclear.

### Cited Findings
- **DDC:** OCLC owns all copyright in DDC. The DDC 22 Summaries can be downloaded only after accepting OCLC terms and conditions. The WebDewey schedule grants a "nonexclusive, nontransferable" licence for internal, noncommercial purposes (for example, posting the DDC23 Summaries on an institution's website, with a required copyright notice). — [OCLC DDC 22 Summaries T&C](https://oclc.org/research/activities/browser/terms.html); [OCLC Schedule 08 WebDewey](https://www.oclc.org/content/dam/legal/schedules/en_us/Schedule-08-WebDewey-EN-US.pdf). An EN–ZH-Hant dual-language WebDewey exists, so OCLC has a licensed traditional-Chinese Dewey. — [OCLC Schedule 08 WebDewey EN–ZH Hant](https://www.oclc.org/content/dam/legal/schedules/zh_tw/Schedule-08-WebDewey-Dual-Language-EN-ZH-Hant.pdf)
  - Wikidata: 19,046 items have a DDC (P1036) value, and 14,258 have zh labels (own query). These are Wikidata items, not OCLC captions, so they do not give you the DDC schedule.
- **UDC Summary:** about 2,600+ classes (from memory, unverified). The UDC Consortium FAQ says the data is released under CC BY-SA 3.0 and that no separate licence is needed. It is available as SKOS linked data (since 2011) at udcdata.info and on Finto. Conflicting labels exist: an EU Interoperable Europe record says CC BY 3.0, and an IFLA repository file says CC BY-NC-ND 4.0 for the 57-language summary. — [UDCC FAQ](https://udcc.org/index.php/faq/7); [Finto UDCS](https://finto.fi/udcs/fi/?clang=en); [Interoperable Europe](https://interoperable-europe.ec.europa.eu/collection/education-culture-and-sport/document/universal-decimal-classification-udc); [IFLA repository](https://repository.ifla.org/items/bf549f33-dfce-494b-89c5-9bbcc47f5794/full)
- **YSO:** Finto's API reports 33,237 `skos:Concept` (1,735 deprecated), including 30,596 general concepts and 821 individuals, plus 242 collections. Languages are en, fi, se and sv. — [Finto REST API YSO stats](https://api.finto.fi/rest/v1/yso/vocabularyStatistics); [Finto REST API YSO](https://api.finto.fi/rest/v1/yso/)
  - Licence: CC BY 4.0, maintained by the National Library of Finland, open data on avoindata.suomi.fi. — [Kansalliskirjasto YSO](https://www.kansalliskirjasto.fi/en/services/yso-general-finnish-ontology); [avoindata.suomi.fi YSO](https://avoindata.suomi.fi/data/en/dataset/yso)
  - Annif supports subject indexing with YSO in Finnish, Swedish and English. — [Kansalliskirjasto YSO](https://www.kansalliskirjasto.fi/en/services/yso-general-finnish-ontology)
- **KOKO** (YSO plus domain ontologies): 62,283 concepts. — [Finto REST API KOKO stats](https://api.finto.fi/rest/v1/koko/vocabularyStatistics)
- **YSO in Wikidata:** 29,323 items have a YSO ID (P2347), and 20,516 of them have zh labels (about 62% of YSO). 10,762 items carry both a YSO ID and an LCSH "sh" ID (own queries). — [QLever](https://qlever.dev/api/wikidata)
- **STW Thesaurus for Economics:** more than 6,000 descriptors and more than 22,000 entry terms. CC BY 4.0, RDF/XML and Turtle, latest version 9.20 (2025-12-16). — [ZBW STW about](https://zbw.eu/stw/version/latest/about)
  - Wikidata: 5,898 items with an STW ID (P3911), 4,064 with zh labels (own query).
- **GND:** nothing in this session confirmed its licence. My background knowledge is that DNB publishes GND under CC0 and that it is German-only, with mappings to LCSH and Wikidata. This is not verified here.
- **MeSH:** NLM provides MeSH data free; no licence is needed for FTP download. The conditions are:
  - acknowledge NLM ("Courtesy of the U.S. National Library of Medicine");
  - do not imply NLM endorsement;
  - keep redistributed copies current, or state that they may not reflect the latest MeSH.

  — [NLM Terms and Conditions MeSH](https://www.nlm.nih.gov/databases/download/terms_and_conditions_mesh.html)
  - CMeSH (中文医学主题词表) is the Chinese translation by the Institute of Medical Information & Library, CAMS. That institute owns the copyright, and access is institutional only. — [PolyU Library CMeSH](https://www.lib.polyu.edu.hk/node/25167)
  - Wikidata: 39,482 items with a MeSH descriptor ID (P486), 19,491 with zh labels (own query).
- **Getty AAT:** the Getty vocabularies are published as linked open data under ODC-By 1.0. Raw relational or XML files may require a licence. — [Getty CIDOC LOD presentation](https://www.getty.edu/research/tools/vocabularies/cidoc_getty_vocabs_lod.pdf)
  - Since 2008, Taiwan's TELDAP (Academia Sinica) has worked with the Getty Research Institute on a Chinese AAT (AAT-Taiwan), translating about 35,000 AAT records. — [Getty multilingual vocabs](https://www.getty.edu/research/tools/vocabularies/multilingual_vocabs.pdf); [Getty ITWG TELDAP update](https://www.getty.edu/research/tools/vocabularies/12_itwg_teldap_update.pdf)
  - Wikidata: 24,383 items with an AAT ID (P1014), 16,084 with zh labels (own query).
- **UNESCO Thesaurus:** CC BY-SA 3.0 IGO, with a required attribution sentence. SKOS, LOD, downloads and a SPARQL endpoint are available. The official languages are en, fr, es, ru (2005) and ar (2020); Chinese was not found. A volunteer Korean edition exists on a third-party Skosmos instance under CC BY-SA 3.0 IGO, which is a precedent for a community Chinese edition. — [UNESCO vocabularies about](https://vocabularies.unesco.org/browser/en/about); [Korean UNESCO edition](https://cloud.maeul.net/vocab/unescoKo/en-US/)
  - Wikidata: 4,398 items with a UNESCO ID (P3916), 3,258 with zh labels (own query).

### Inferences
- Production licence flags:
  - **Blocks production:** DDC (needs an OCLC licence), CMeSH (copyright CAMS), and TERMONLINE bulk use (licence unknown).
  - **Allowed, with share-alike:** UDC Summary and UNESCO (CC BY-SA). A derived Chinese vocabulary must stay under BY-SA. That is acceptable for an open demo but may complicate mixing with other data.
  - **Attribution only, fine for production:** FAST (ODC-By), AAT (ODC-By), YSO and STW (CC BY 4.0), and MeSH (NLM terms, including the currency notice).
  - **No restriction:** LCSH/LCC (public domain, to be confirmed).
  - **Licence of Chinese data unknown:** AAT-Taiwan.
- Wikidata zh coverage, from best to worst: DDC-linked items (75%), UNESCO (74%), AAT (66%), STW (69%), YSO (70% of linked items, 62% of all YSO), LCSH (69% of linked items but only about 12% of LCSH), MeSH (49%), LCC (39%), and FAST non-person items (74% of linked items but a small share of FAST).
- YSO is Annif's "home" vocabulary, so a zh-YSO would reuse a proven Annif configuration. However, Chinese books in MARC are not tagged with YSO. Training labels would have to be bridged through LCSH↔YSO mappings (10.8k items in Wikidata) or through Finto's own LCSH/LCC matches.
- STW is a good, small, single-domain demo (economics). It has CC BY 4.0, about 6k concepts and about 4k zh labels already available, and ZBW econ data exists. It does not match Chinese-book cataloging either.

### Gaps
- GND licence and size were not verified this session.
- UDC Summary class count and whether a Chinese UDC Summary translation exists were not verified (the udcc.org summary page returned 404).
- The AAT-Taiwan data licence and its download location (aat.teldap.tw) were not verified.
- I did not check whether YSO itself carries `skos:closeMatch` or `exactMatch` links to LCSH in the Finto dump. I believe it does, but this is unverified.

## Q4. How to obtain Chinese labels (existing mappings vs. MT/LLM) and how to control quality

### Takeaway
Use a layered pipeline:
1. Wikidata zh labels (CC0) via authority-ID properties. These are high precision for entities and lower precision for abstract topical concepts.
2. Normalize to zh-Hans with OpenCC.
3. Use an LLM with structured context (English label, alt labels, broader/narrower terms, scope note, LCC class, existing Wikidata label as a candidate) for everything else.
4. Run back-translation, collision detection and stratified human review.

TERMONLINE (术语在线) has no published open licence I could find. Use it only for manual spot verification, not for bulk scraping.

### Cited Findings
- WOKIE (CHR 2025, arXiv 2507.19537) is an open pipeline that translates SKOS thesauri by combining external MT services with LLM refinement. It is designed for commodity hardware and non-experts.
  - Evaluation: remove all labels in one language, regenerate them, and compare with the originals (back-translation), skipping the source language. The test set was several digital-humanities thesauri, 15 languages and 4 scripts (no Chinese).
  - Of 28 MT services, only 8 were usable (rate limits, unreliability).
  - Translated thesauri improved ontology matching (measured with OAEI MELT).
  - Invalid SKOS was cleaned with `skosify`.
  — [arXiv 2507.19537](https://arxiv.org/abs/2507.19537); [ACH Anthology](https://anthology.ach.org/volumes/vol0003/mind-language-gap-in-digital-humanities-llm-aided/); [Zenodo supplement](https://zenodo.org/records/15494760)
- The Skosmos/Annif team (National Library of Finland) reported at NKOS 2025 that they use LLMs for vocabulary translation and synthetic data generation. — [NKOS 2025 Skosmos and Annif slides](https://nkos.dublincore.org/2025NKOSworkshop/NKOS%20Skosmos%20and%20Annif.pdf)
- Survey background on multilingual ontologies and label translation: — [A Review of Multilingualism in and for Ontologies (arXiv 2210.02807)](https://arxiv.org/pdf/2210.02807)
- TERMONLINE (术语在线, run by 全国科学技术名词审定委员会/CNCTST): launched May 2016, with nearly 1M terms including approved standard terms, new terms, and cross-strait (海峡两岸) term comparisons. I found no official licence, API or bulk-download terms. — search summary; no primary page retrieved (gap)
- Existing Chinese counterparts under restricted licences: CMeSH (CAMS copyright), and the traditional-Chinese WebDewey (OCLC licence). — [PolyU CMeSH](https://www.lib.polyu.edu.hk/node/25167); [OCLC EN–ZH-Hant WebDewey schedule](https://www.oclc.org/content/dam/legal/schedules/zh_tw/Schedule-08-WebDewey-Dual-Language-EN-ZH-Hant.pdf)
- Observed Wikidata label issues: mixed script under `zh`, one item mapped to many LCSH IDs, Wikipedia-title-style labels, and transliterations. — own QLever sample (see Q1)
- Precedent for publishing a volunteer translation alongside an official vocabulary, with a disclaimer and the same licence: — [Korean UNESCO Thesaurus edition](https://cloud.maeul.net/vocab/unescoKo/en-US/)

### Inferences
Recommended pipeline for a demo vocabulary:

1. **Seed from Wikidata.** Run SPARQL joins on P244, P2163, P2347, P3911, P486 and so on. Take labels in priority order zh-cn > zh-hans > zh > zh-hant/zh-tw/zh-hk, convert them to Simplified with OpenCC (t2s or tw2sp), and keep zh aliases as `altLabel`. Flag a label for review when the Wikidata item is an entity class (person, species, building) but the vocabulary concept is topical, or when one Wikidata item maps to several concepts.
2. **Translate the rest with an LLM.** Use a prompt that includes the English prefLabel, altLabels, broader and narrower labels, scope note, LCC number range or FAST facet, and two or three Chinese example books. Ask for JSON with prefLabel_zh, altLabels_zh, a confidence score, an "untranslatable/culture-specific" flag and a short gloss. Batch siblings together so terminology stays consistent.
3. **Handle LCSH or FAST subdivisions** such as `—History`, `—Social aspects` or `—China`. Translate each subdivision once into a controlled table (e.g. 历史, 社会方面, 中国), then compose strings mechanically with "—". Do not translate whole strings freely.
4. **Quality control:**
   - Back-translate a sample and score it with chrF or an LLM judge, as WOKIE does.
   - Check that zh prefLabels are unique within the vocabulary. Duplicate zh labels on different concepts signal polysemy collisions, e.g. "Cells (Biology)" vs. "Prison cells", or "Bonds (Finance)" vs. chemical bonds.
   - Check hierarchy plausibility: the narrower term's zh label should be semantically subsumed by the broader one.
   - Compare against TERMONLINE or 中国分类主题词表 manually, on a stratified sample of 200–500 concepts per domain.
   - Measure where the Wikidata label and the LLM output disagree, and use disagreement as a review trigger.
   - Record provenance per label (e.g. `dct:source wikidata|llm-model-version|human`) so a later production pass can replace LLM labels.
5. **Watch for cultural mismatch.** US-centric headings ("African Americans", "Indians of North America", US law and government headings) and Western religion and history headings need Chinese conventions or scope notes. Chinese-specific topics, such as dynastic periods, 少数民族 (ethnic minorities) and CCP history, are poorly expressed in LCSH or FAST anyway. A demo should document this as a known limitation.
6. **Licensing of outputs.** Wikidata labels are CC0. LLM-generated labels inherit only the source vocabulary's licence and the LLM provider's terms. FAST requires ODC-By attribution on the derived zh vocabulary.

### Gaps
- No primary-source TERMONLINE licence or API terms were found. Check the termonline.cn footer or terms page, or ask CNCTST directly.
- I found no published study on LLM translation of LCSH or FAST into Chinese specifically, and no measured accuracy figures for EN→ZH thesaurus translation. WOKIE did not test Chinese.
- I found no openly licensed existing mapping between LCSH and 中国分类主题词表 (CCT). If one exists, it would be the best Chinese label source. It needs a targeted search, likely in Chinese library journals.

## Q5. Recommendation: one or two best candidates for a demo-sized Chinese vocabulary (a few thousand to about 50k concepts) that matches available training data

### Takeaway
Primary choice: **FAST Topical (plus Geographic), filtered by frequency in the Chinese-book MARC training set**, giving about 10k–30k concepts. It is ODC-By (fine for production), flat or faceted (fits Annif), and derivable from the LCSH already present in Chinese-book records. Seed zh labels from Wikidata (about 20.8k non-person FAST items have zh labels) and translate the rest with an LLM. Secondary choice: **a main-heading-only LCSH subset** if public-domain status matters most for production. A small, fast proof of concept could use **STW** (6k, CC BY 4.0, about 4k zh labels available) or **YSO** (33k, CC BY 4.0, about 20.5k zh labels), but these lack Chinese training data cataloged with them.

### Cited Findings
- FAST is ODC-By and downloadable per facet (Topical 46 MB NT zip). — [OCLC FAST Download](https://www.oclc.org/research/areas/data-science/fast/download.html)
- LCSH SKOS bulk is 40 MB (TTL.gz). — [id.loc.gov download](https://id.loc.gov/download/)
- Existing zh labels via Wikidata (own counts):
  - LCSH: 40,793
  - FAST non-person: 20,801
  - YSO: 20,516
  - STW: 4,064

  — [QLever Wikidata](https://qlever.dev/api/wikidata)
- YSO and STW are CC BY 4.0 and are already used with Annif (YSO). — [Kansalliskirjasto YSO](https://www.kansalliskirjasto.fi/en/services/yso-general-finnish-ontology); [ZBW STW](https://zbw.eu/stw/version/latest/about)

### Inferences
- Concrete demo recipe:
  1. From the Chinese-book MARC records (6XX fields with second indicator 0 = LCSH, or 6XX $2 fast), convert LCSH to FAST headings, or use FAST directly if it is present.
  2. Count heading frequencies and keep headings with at least 5–10 uses. That should land in the few-thousand to 30k range, depending on corpus size.
  3. Pull the matching FAST SKOS records (labels, broader terms, LCSH source links).
  4. Attach Wikidata zh labels through P2163 (and P244 via FAST's LCSH links), normalize with OpenCC, and translate the remainder with an LLM using hierarchy context.
  5. Export an Annif TSV or SKOS vocabulary with zh prefLabels and en altLabels. Keeping the English labels lets the same vocabulary also serve English Annif projects and makes debugging easier.
- Why not the full LCSH: pre-coordinated strings would turn a 50k demo into hundreds of thousands of sparse labels, and coverage of subdivided strings in Wikidata is negligible.
- Why not DDC or CMeSH: licence blockers for production. Why not UNESCO or UDC Summary as the main vocabulary: too coarse (a few thousand classes) and share-alike. They are acceptable as an extra coarse "subject area" vocabulary for a demo.
- For production later, FAST, LCSH, YSO and STW all allow redistribution with at most attribution. Production would need human review of the LLM-generated labels and a recorded provenance per label.

### Gaps
- I did not measure how many Chinese-book MARC records actually carry LCSH or FAST, or their heading frequency distribution. That depends on the training-data source covered by other researchers, and it determines the final vocabulary size.
- I did not verify the FAST Topical concept count or how many FAST Topical concepts have Wikidata links specifically (the Wikidata query cannot separate FAST facets by ID). That needs a local join of the FAST dump against Wikidata P2163.
