# Open Chinese text datasets with subject-like labels for Annif, and LLM-based synthetic labeled data

Research date: 2026-10-13. Scope: datasets usable as Annif train/eval corpora for a Chinese subject-indexing teaching/demo tool, how to align them to a controlled vocabulary, LLM synthetic data methods, and Annif evaluation and corpus-size guidance.

## Q1. CSL (Chinese Scientific Literature dataset, ydli-ai/CSL): license, fields, label counts, availability

### Takeaway
CSL is the best single fit for a Chinese Annif demo. It has 396,209 papers with title, abstract, author keywords, and a two-level discipline label (13 门类 / 67 学科). The GitHub repo says Apache-2.0, but there is no separate data license, and the data comes from a national S&T resource-sharing centre, so redistribution rights to the abstracts are not fully clear. Use it for teaching. Get it legally reviewed before any production or redistribution use.

### Cited Findings
- Size: 396,209 Chinese papers from 2010 to 2020. Fields: title, abstract, keywords, discipline (学科), category (门类). Some samples also carry a text2text "prompt" field. — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- Labels: 13 top-level categories (门类, e.g. Engineering, Science, Medicine) and 67 second-level disciplines (学科, e.g. Mechanics, Clinical Medicine). — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- Downloads:
  - 10k benchmark in the repo under `benchmark/`, split 0.8/0.1/0.1.
  - 40k sub-dataset on Google Drive.
  - Full 396k dataset on Google Drive.
  - Instruction version on HF: `P01son/instructions` (CSL folder).
  - Abstract-only pretraining corpus, about 1.5 GB: HF `Linly-AI/Chinese-pretraining-dataset` (csl.jsonl).
  - Source: [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- Benchmark tasks: title prediction (summarization), keyword generation, 13-way category classification from the title, and 67-way discipline classification from the abstract. — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- License: the repository states Apache License 2.0 and gives no separate data license. The data source is described as the National Science and Technology Resource Sharing Service Engineering Research Center. — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- The arXiv paper itself (arXiv:2209.05034) carries CC BY-NC-SA 4.0. That covers the paper, not the dataset. The abstract does not name the classification scheme behind the categories. — [arXiv 2209.05034](https://arxiv.org/abs/2209.05034)
- Citation: Li et al., "CSL: A Large-scale Chinese Scientific Literature Dataset", COLING 2022, pp. 3917–3923. — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- Related derivatives:
  - The CLUE "CSL" task is a binary keyword-recognition task: are all listed keywords genuine? Fake keywords were made with TF-IDF. Train 20,000 / dev 3,000 / test 3,000. It is built from core-journal abstracts and links to the original P01son6415/chinese-scientific-literature-dataset. — [CLUEbenchmark/CLUE GitHub](https://github.com/CLUEbenchmark/CLUE)
  - CSLDCP, the discipline classification task, appears in FewCLUE. — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL); [FewCLUE arXiv](https://arxiv.org/pdf/2107.07498)

### Inferences
- Use in Annif:
  - Discipline labels (67 学科, two levels) make a small, closed "vocabulary". That suits a fast demo with tfidf, fastText, Omikuji or SVC (SVC is multiclass only).
  - Author keywords give an open, large label set, like XMTC. Turning them into a vocabulary means clustering or normalising them, or linking them to Wikidata QIDs (see Q3).
- The 396k full set is well above Annif's recommended sizes for Omikuji and fastText (10k+). Even the 40k subset is enough for a demo.
- Apache-2.0 on a repo with scraped bibliographic abstracts is a common but weak license signal. The rights holders of the abstracts (publishers and journals) never granted it. Treat CSL as "research/teaching use, attribution, do not re-host" until confirmed.

### Gaps
- Could not confirm from the paper text which official scheme the 13/67 labels follow. Candidates are the MoE 学位授予和人才培养学科目录 or GB/T 13745. The PDF could not be text-extracted in this session, so check the paper's Section 3 manually.
- No statement found on keywords-per-paper distribution, average abstract length, or whether a keyword vocabulary or frequency list is released.
- Google Drive links: current availability as of Oct 2026 not tested.

## Q2. Other candidate datasets (CLUE, THUCNews, Wikipedia/Wikidata, Baidu Baike, keyword sets, patents/IPC, etc.)

### Takeaway
After CSL, the most practical options are:
- Chinese Wikipedia with Wikidata, under clear CC BY-SA / CC0 licences.
- CLUE TNEWS and IFLYTEK, small, single-label, no stated licence.
- THUCNews, 14 classes, licence unclear.
- The CAKE medical keyphrase set.

No public Chinese-patent-with-IPC dataset was found on Hugging Face. Avoid Baidu Baike: it blocks most crawlers and has no open licence.

### Cited Findings
**CLUE classification sets**
- TNEWS' (Toutiao news titles): 15 categories; train 53,360 / dev 10,000 / test 10,000. — [CLUE GitHub](https://github.com/CLUEbenchmark/CLUE)
  - Download: `https://storage.googleapis.com/cluebenchmark/tasks/tnews_public.zip`
  - The apostrophe marks a version filtered with ALBERT-tiny.
- IFLYTEK' (app descriptions): 119 categories (0–118); train 12,133 / dev 2,599 / test 2,600. — [CLUE GitHub](https://github.com/CLUEbenchmark/CLUE)
  - Download: `https://storage.googleapis.com/cluebenchmark/tasks/iflytek_public.zip`
- CLUE licence:
  - The repository has no LICENSE file and states no dataset licence. Its pre-training corpus is described as "for research purposes". — [CLUE GitHub](https://github.com/CLUEbenchmark/CLUE)
  - The HF/TFDS mirror lists "No known license" for the TNEWS and IFLYTEK configs. — [TFDS community catalog: clue](https://tensorflow.google.cn/datasets/community_catalog/huggingface/clue?hl=en)
- The CLUE paper describes TNEWS as 73,360 titles of Toutiao news published before May 2018. IFLYTEK has 17,332 app descriptions across 119 categories. — [CLUE paper arXiv 2004.05986](https://arxiv.org/pdf/2004.05986)

**THUCNews**
- Built from Sina News 2005–2011: about 740k documents in 14 categories (财经, 彩票, 房产, 股票, 家居, 教育, 科技, 社会, 时尚, 时政, 体育, 星座, 游戏, 娱乐). — [HyperAI dataset page](https://hyper.ai/cn/datasets/9277)
  - The official site is cited as http://thuctc.thunlp.org/ but was not verified live.
  - The licence field on the HyperAI mirror says "Other".
- Size is reported inconsistently:
  - Papers with Code says about 840k documents. — [Papers with Code: THUCNews](https://paperswithcode.com/dataset/thucnews)
  - The HyperAI zip is 1.45 GB, while other secondary sources say 2.19 GB.

**Chinese keyphrase datasets**
- CAKE (Chinese medical abstracts keyphrase extraction), from the Chinese Science Citation Database. — [JDIS 2021 article](https://reference-global.com/article/10.2478/jdis-2021-0013)
  - 100k train / 6,000 dev / 3,094 test abstracts.
  - Character-level IOB tagging; BERT baseline F1 59.80%.
  - GitHub: possible1402/Dataset-For-Chinese-Medical-Keyphrase-Extraction.
  - Extractive only, so absent keyphrases are not modelled.
- No dedicated CNKI-derived Chinese keyword dataset was found on Hugging Face beyond the CSL derivatives. — (search result; [HF Nickyang/Unsupervised_Keyphrase_Extraction](https://huggingface.co/datasets/Nickyang/Unsupervised_Keyphrase_Extraction) could not be confirmed as Chinese)

**Wikipedia / Wikidata**
- Wikidata structured data (main, Property, Lexeme, EntitySchema namespaces) is CC0 1.0. Text in other namespaces is CC BY-SA 4.0. — [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
- Chinese Wikipedia article text is CC BY-SA. That follows Wikimedia's standard licensing; this session did not separately verify it for zh.wikipedia.

**Baidu Baike**
- Baidu Baike's robots.txt allows only a few crawlers (Baidu, Sogou, Chinaso, YYSpider, EasouSpider) and blocks Google, Bing and others. Press reports read this as a move against unauthorised AI-training scraping. — [ifeng tech report](https://tech.ifeng.com/c/8cFdsd8yDPe)
- Other wikis (e.g. Moegirlpedia) treat Baidu Baike content as licence-incompatible. — [Moegirl Template:著作权侵犯](https://zh.moegirl.org.cn/Template:%E8%91%97%E4%BD%9C%E6%9D%83%E4%BE%B5%E7%8A%AF/doc)

**Patents / IPC**
- No Hugging Face dataset of Chinese patent abstracts with IPC labels was found. The closest is English: `datalyes/class_text2ipc3` (PatenTEB), with 109 IPC3 classes, a 30k train subset, CC BY-NC-SA 4.0. — [HF datalyes/class_text2ipc3](https://huggingface.co/datasets/datalyes/class_text2ipc3/blob/main/README.md)
- Chinese patent IPC datasets in papers (CNPatents, using IPC 4-digit labels; CNPTD-200K, 2010–2019 company patents) show no confirmed public release. — [Data Analysis & Knowledge Discovery 2022](https://manu44.magtech.com.cn/Jwk_infotech_wk3/EN/Y2022/V6/I2/3/129); [Connection Science 2024 via DOAJ](https://doaj.org/article/1484ecfec3914def9b8667d2c9cccc2b)
- IPC 2026.01 took effect on 1 January 2026. It revised 1,615 symbols (517 new, 206 deleted) versus 2025.01. — [WIPO: New version of the IPC (2026.01)](https://www.wipo.int/zh/web/classification-ipc/w/new-version-of-the-ipc-2026.01); [Mondaq](https://webiis10.mondaq.com/china/trademark/1790296/china-launches-new-versions-of-ipc-and-nice-classification)
  - CNIPA translated and published the Chinese IPC scheme, definitions and a concordance at https://www.cnipa.gov.cn/col/col3161/index.html.
- WIPO's authentic IPC texts are English and French; the Chinese version is a translation. — [WIPO IPC FAQ (zh)](https://www.wipo.int/zh/web/classification-ipc/faq/)

### Inferences
- **CLUE (TNEWS, IFLYTEK) and THUCNews:**
  - All single-label with few classes (14–119). They demo "classification" well but not library-style multi-label subject indexing.
  - Fine for a first tfidf/fastText exercise and an eval walkthrough.
  - None has an explicit open licence: OK for classroom use, poor for redistribution.
- **Wikipedia plus Wikidata is the cleanest open-licence route:**
  - Article intros (CC BY-SA) can serve as documents.
  - Wikidata "main subject" (P921) statements, or category-to-QID mappings, give labels.
  - Labels are CC0, so a derived vocabulary can be republished.
  - This is an inference: the extraction pipeline itself was not researched here.
- **Patents:**
  - IPC is a natural hierarchical "vocabulary" with an official Chinese translation.
  - No ready open Chinese patent+IPC corpus was found. Building one would mean pulling from CNIPA or Google Patents public data, or using LLM-synthetic patent abstracts (see Q4).
  - The licence for redistributing CNIPA's Chinese IPC text was not found.

### Gaps
- Douban book tags: no source found this session. Douban has no open data licence that I could verify; assume scraping is off-limits.
- NLPCC shared-task datasets with keyword or topic labels (e.g. NLPCC 2017 news headline categorisation): not researched in this session.
- Chinese government open data (data.gov.cn portals) with subject labels: not researched.
- PubMed Chinese / CBM (中国生物医学文献数据库): no open dataset found or searched.
- THUCTC official site licence text: not verified, site not reachable from search results.
- CNIPA Chinese IPC licence or terms of reuse: not found.

## Q3. Which datasets map naturally to a library-style controlled vocabulary

### Takeaway
Three alignments look natural:
- CSL's 13/67 disciplines to a discipline code scheme: MoE 学科目录 or GB/T 13745. Which one is unverified.
- CSL or CAKE author keywords to Wikidata items, CC0, linked by label/alias matching.
- Patent text to IPC, using CNIPA's Chinese translation.

Wikidata is the only option with a clearly open licence for publishing the resulting SKOS vocabulary.

### Cited Findings
- CSL provides two-level discipline labels: 13 门类 and 67 学科. — [ydli-ai/CSL GitHub](https://github.com/ydli-ai/CSL)
- Wikidata structured data is CC0, so labels, aliases and QIDs can be reused freely. — [Wikidata:Licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)
- IPC exists in an official Chinese translation from CNIPA (2026.01, with definitions and a concordance). English and French are the authentic texts. — [Mondaq](https://webiis10.mondaq.com/china/trademark/1790296/china-launches-new-versions-of-ipc-and-nice-classification); [WIPO IPC FAQ](https://www.wipo.int/zh/web/classification-ipc/faq/)
- In SemEval-2025 the GND vocabulary had to be translated (GND preferred terms from German to English with GPT-4o-mini, batches of 100), because Annif's MLLM backend needs the vocabulary and the documents in the same language. — [Annif at SemEval-2025 (arXiv 2504.19675)](https://arxiv.org/html/2504.19675v1)

### Inferences
- **CSL disciplines to a scheme:**
  - The 67 学科 names probably correspond to 一级学科 in the MoE catalogue, as the 门类 count of 13 matches its 门类 count (pre-2022 version).
  - Mapping to GB/T 13745 would need manual alignment.
  - Either becomes a small SKOS concept scheme with broader/narrower links that Annif can load.
- **Keywords to Wikidata:**
  - Match exact zh labels and aliases in zh-hans/zh-cn (with simplified/traditional normalisation).
  - Keep only keywords that resolve to a QID; that yields a vocabulary of CC0 concepts.
  - Coverage of technical keywords will be partial. Expect many unmatched long-tail terms; this is an inference, not measured.
- **The MLLM lesson carries over:**
  - The vocabulary must have Chinese prefLabels and altLabels.
  - Annif needs a Chinese-aware analyzer/tokeniser for lexical matching to work.

### Gaps
- No measured Wikidata coverage rate for Chinese scientific keywords was found.
- Licence status of the GB/T 13745 and MoE catalogue texts as reusable vocabularies: not researched. Chinese national standards are copyrighted publications; recommended standards (GB/T) may be free to view but not to republish.
- Whether CSL's labels are officially tied to any national standard: unverified.

## Q4. LLM-based synthetic data: published work, recipe, pitfalls, cost

### Takeaway
The best evidence comes from the Annif team (National Library of Finland) at SemEval-2025 Task 5 and GermEval-2025 LLMs4Subjects. One-shot LLM synthesis of new title+abstract records from existing records, keeping the gold labels plus one random extra vocabulary term, gave about +0.02–0.04 nDCG for Omikuji Bonsai. Gains plateaued after a few synthetic sets. Small 4–8B open models on one A100 were enough. Pure LLM-assigned labels carry systematic, non-random noise, so validate them against a gold subset.

### Cited Findings
**SemEval-2025 Task 5 (LLMs4Subjects)**
- Setup:
  - Subject tagging of English/German TIBKAT technical-library records with the GND vocabulary.
  - Top-k subject recommendation, scored by precision, recall and F1, plus qualitative review by subject specialists.
  - Over 200 teams made final submissions; 93 system papers.
  - Data and code: https://github.com/jd-coderepos/llms4subjects.
  - Source: [Task overview arXiv 2504.07199](https://arxiv.org/pdf/2504.07199); [ACL Anthology 2025.semeval-1.328](https://aclanthology.org/2025.semeval-1.328)
- The overview concludes that synthetic data and retrieval-augmented pipelines improved performance. Multilingual models and training data beat monolingual ones, and smaller well-engineered systems often rivalled large instruction-tuned LLMs. A second edition focused on energy- and compute-efficient systems was planned. — [Task overview arXiv 2504.07199](https://arxiv.org/pdf/2504.07199)
- Annif placed 1st on all-subjects and 2nd on tib-core-subjects (quantitative), and 4th in the qualitative evaluation. — [arXiv 2504.19675](https://arxiv.org/abs/2504.19675)

**Annif SemEval-2025 recipe** (all items: [arXiv 2504.19675 HTML](https://arxiv.org/html/2504.19675v1))
- Model and compute: Llama-3.1-8B-Instruct served with vLLM on 1× A100 80GB. Synthesis ran at about 8 records/s; translation at about 4 records/s.
- Prompt: give the LLM an existing train record (title+abstract) with its gold GND labels plus one randomly chosen extra GND term, and ask for a similar new record covering all those subjects. The extra term pushes it toward "a novel record, not just to rephrase".
- Mix: 1 part original to 3 parts synthetic. Generation ran 3× per language and vocabulary variant.
- Gain: the first synthetic batch gave Bonsai about +0.02 nDCG@10. Later batches added little; another passage says "~0.03".
- Synthetic data was not used for MLLM (needs little training data). XTransformer did not improve with it.
- Corpus sizes:
  - all-subjects: 81,937 train / 13,666 dev / 27,986 test.
  - tib-core: 41,923 / 7,001 / 6,119.
- Pitfalls:
  - The LLM made small unrequested edits during translation.
  - Records often mixed languages.
  - Translation quality propagates to indexing quality.
  - Traditional XMTC needs far less compute than LLMs.

**Annif GermEval-2025 recipe, "efficient LLMs"** (all items: [arXiv 2508.15877 HTML](https://arxiv.org/html/2508.15877v1))
- Models: mainly 3–12B LLMs (Aya-expanse-8B, EuroLLM-9B, Gemma-3 4B/12B, Llama 3.x 3B/8B, Ministral-8B, Mistral-Nemo-12B, Qwen3 4B/8B, etc.), compared with 24–30B models.
- Synthesis:
  - One-shot prompting, as at SemEval; the extra random GND term must appear in at least one training record.
  - Four synthetic sets per language, each the size of the train set (90,452 records), so about 360k synthetic records per language.
- Training mix: Bonsai used the original data doubled plus all four synthetic sets. XTransformer used the original plus two synthetic sets.
- Gains (dev nDCG@20): Bonsai German 0.5122 → 0.5513 (+0.039, Aya-8B data); English 0.5595 → 0.5896 (+0.030, Qwen3-4B data).
- LLM re-ranking:
  - The top-100 candidates from the ensemble go to an LLM, which returns 0–100 relevance scores, combined as f = w·r^p + (1−w)·x.
  - With Mistral-Small-24B: +0.025 (en) and +0.036 (de) nDCG@20. With Qwen3-4B: smaller gains, e.g. +0.017 (en).
  - The test-set result ranked 1st (0.5697 nDCG@20).
- Compute: everything ran on 1× A100 80GB with vLLM. No wall-clock or energy totals reported.
- Pitfalls:
  - The random extra term "may cause seemingly unrelated subjects to appear together".
  - Gains plateau after a few sets.
  - XTransformer benefits less.
  - The best re-ranking needed the larger 24B model.
- Vocabulary: GND, 200,035 subjects.

**LLM-assigned labels (no human gold)**
- Training BERT-style classifiers on LLM annotations instead of gold labels:
  - Lowers accuracy and F1.
  - Makes training runs less stable and causes early plateaus.
  - The errors are non-random and not fully fixed by entropy filtering or ensembling.
  - Larger labelling models did not solve it (e.g. Krippendorff's α 84.30 gold → 52.72 with 3B-model labels → 43.75 with 7B-model labels on one dataset).
  - Source: [Feeding LLM Annotations to BERT Classifiers at Your Own Risk (arXiv 2504.15432)](https://arxiv.org/html/2504.15432v1)
- In XMLC skill extraction, a fully synthetic LLM-generated labelled dataset gave +15 to 25 points R-Precision@5 over distant-supervision baselines. — [arXiv 2307.10778](https://arxiv.org/abs/2307.10778v1)
- A biomedical digital-library study of label noise notes that its noise was injected at random, not as systematic bias, which limits how far its results transfer to LLM labelling. — [arXiv 2411.12752](https://arxiv.org/pdf/2411.12752)

### Inferences
- **Recipe for a Chinese demo, adapted from the Annif papers:**
  1. Start from CSL records (title+abstract+keywords or disciplines) mapped to the demo vocabulary.
  2. Prompt a Chinese-capable 4–8B instruct model (e.g. Qwen3-4B/8B, which was used and worked well at GermEval) with one example record plus its labels plus one random extra concept. Ask for a new 中文 title+abstract covering all of them.
  3. Use the synthetic records only for associative backends (Omikuji/fastText), at a 1:1 to 1:3 original-to-synthetic ratio.
  4. Keep dev/test sets purely human-labelled.
- **Throughput estimate:** about 8 records/s on one A100 with vLLM (Llama-8B). On that basis, 10k–50k synthetic records is roughly 20 minutes to under 2 hours of single-A100 time.
  - This extrapolates from the SemEval figure; Chinese token counts and output length will change it.
  - On a laptop or Apple Silicon without vLLM, expect far slower throughput.
  - A hosted API would cost tokens instead (not costed here).
- **Fully synthetic corpora (LLM invents documents and assigns labels):** fine for a demo that illustrates the pipeline. Any reported metrics would mostly reflect the LLM's own labelling habits; label it clearly as synthetic in teaching materials.
- **Use the LLM as a re-ranker rather than a labeller:** about +0.02–0.04 nDCG with a 24B model. This is a good teaching extension that shows "traditional XMTC plus LLM".

### Gaps
- No published work found on LLM synthetic data specifically for Chinese subject indexing or Chinese library vocabularies (CLC/中图法, 汉语主题词表).
- Exact total synthetic counts and wall-clock time for SemEval are not reported. GermEval reports no throughput.
- No cost figures (USD per 10k records) for hosted LLM APIs were researched.
- Effect of synthetic data on lexical backends (MLLM) for Chinese is unknown; the Annif team didn't use it there.

## Q5. Annif evaluation metrics and minimum corpus sizes per backend

### Takeaway
`annif eval` computes a full set of metrics by default (`--metric` defaults to "all"), with `--limit` and `--threshold` controlling the cut-off. The LLMs4Subjects work reports nDCG@10/20 and P/R/F1@k.

Annif's wiki gives these training-size guidelines:
- fastText and Omikuji: 10,000+ documents.
- MLLM: 100–10,000 documents.
- NN-ensemble: 1,000–10,000 documents.
- TF-IDF: suited only to a baseline or setup test.

### Cited Findings
- Backend guidance from the [Annif wiki: Backends](https://github.com/NatLibFi/Annif/wiki/Backends):

| Backend | Type | Recommended training documents | Wiki notes |
|---|---|---|---|
| TF-IDF | associative | no size stated | baseline only |
| fastText | associative | 10,000+ | |
| Omikuji | associative, tree-based XMTC | 10,000+ | |
| SVC | associative | no size stated | multiclass, not multilabel |
| MLLM | lexical | 100–10,000 | best on long texts |
| STWFSA | lexical | no size stated | |
| YAKE | lexical | none (unsupervised) | |
| NN-ensemble | ensemble | 1,000–10,000 | |
| PAV | ensemble | no size stated | |
| Ensemble | ensemble | no training (averaging) | |

- The wiki suggests starting with TF-IDF, then combining fastText, Omikuji and MLLM in ensembles for best results. — [Annif wiki: Backends](https://github.com/NatLibFi/Annif/wiki/Backends)
- `annif eval` options:
  - `--limit` (max subjects) and `--threshold` (min score).
  - `--metric` (default "all").
  - `--metrics-file` (JSON output) and `--results-file` (per-subject results).
  - `--docs-limit` and `--jobs`.
  - PATHS are directories or (gzipped) TSV files.
  - Source: [Annif docs: Commands](https://annif.readthedocs.io/en/latest/source/commands.html)
- Metrics in the LLMs4Subjects work:
  - Annif's papers report nDCG@10 (SemEval) and nDCG@20 (GermEval). — [arXiv 2504.19675](https://arxiv.org/html/2504.19675v1); [arXiv 2508.15877](https://arxiv.org/html/2508.15877v1)
  - The task overview reports precision, recall and F1 at k. — [arXiv 2504.07199](https://arxiv.org/pdf/2504.07199)
- Reference scale for strong results: GermEval Bonsai trained on 90,452 records against a 200k-concept vocabulary reached dev nDCG@20 ≈ 0.57–0.60. — [arXiv 2508.15877](https://arxiv.org/html/2508.15877v1)

### Inferences
- **Corpus sizes for a Chinese demo:**
  - About 10k–40k CSL records (the 40k subset) for Omikuji/fastText.
  - A separate 1–5k held-out set for NN-ensemble training and for eval.
  - About 1–2k records suffice for MLLM.
- **What to teach:** P@k, R@k, F1@5 and nDCG@k from `annif eval --limit 5`, plus the per-subject `--results-file` to show long-tail weakness.

### Gaps
- The exact list of metric names `annif eval` outputs (e.g. Precision/Recall/F1 at doc/subject/micro/macro averaging, NDCG, NDCG@5/10, LRAP, true/false positives, AP) was not confirmed from the current docs page in this session. Verify with `annif eval --help` or the Annif source.
- The Backends wiki page has no content on XTransformer or EBM (draft pages only), so no minimum sizes are available for them.
- Annif's Chinese tokenisation/analyzer support is not covered here (may be in another researcher's scope). It is critical for Chinese lexical (MLLM) and associative backends.
