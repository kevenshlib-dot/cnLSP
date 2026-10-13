# Openly available Chinese-language bibliographic records with subjects/classification (Annif training data)

Research date: 2026-10-13. About 18 tool calls. Each item is marked as **confirmed** (read on a primary page, or checked locally), **estimate**, or **inference / background knowledge, not verified this session**. Several primary pages would not give sizes or counts. Those are listed under Gaps rather than guessed.

---

## Q1. CNMARC: are there public CNMARC datasets with 606/690, and can CNMARC be harvested legally?

### Takeaway
I found no openly licensed, downloadable CNMARC dataset with 606 (topical subject) and 690 (中图分类号) fields. I checked GitHub, HuggingFace, Kaggle, data portals and recent papers. Mainland bibliographic data services (CALIS, and by analogy the 国家图书馆 联合编目中心) are fee-based and licensed. Their terms ban passing data to third parties, so harvesting CNMARC through Z39.50 to build a training set you share is not cleared for redistribution. At most it is a private, internal use. Treat it as "ask for written permission".

### Cited Findings
- A web search for CNMARC datasets with 606/690 on GitHub or elsewhere found nothing. The closest hits were US GPO MARC21 records on GitHub (1,022,882 CGP records as of 2022-03-30), which are not CNMARC — [FDLP/GPO](https://fdlp.gov/gpo-posts-all-cgp-records-as-of-june-29-2021-on-github)
- A HuggingFace/Kaggle-oriented search found no hosted Chinese library catalog dataset labeled with CLC (中图法) — search results only ([BARTOC CLC entry](https://bartoc.org/en/node/893), [ISKO CLC](https://isko.org/cyclo/clc))
- **Research use exists, but the data is not released:** Yang, Jia & Liu (DCMI-2026, published 2026-09-10) used **32,837 CNMARC records**. They extracted titles, abstracts and series, plus the full CLC 5th ed. as 53,326 notation–caption pairs, and built 36,786 train / 2,019 validation instances. The paper names neither the source library nor a dataset URL or license. Only the article itself is CC BY 4.0 — [DCMI paper](https://dcpapers.dublincore.org/article/952629699)
- A Peking University study (北京大学学报自然科学版 2023, 59(1):11-20) noted a lack of books annotated with CLC labels and used an LCC→CLC mapping to add training data — [PKU journal](https://xbna.pku.edu.cn/CN/Y2023/V59/I1/11)
- **CALIS terms (confirmed from the agreement text):** non-university member service is priced per record (for example 3.00 元 per basic-level 古籍 record). Services are limited to the member's registered users and its own system building, and the data "不得用于任何商业行为或转交第三方使用". University members may download without limit for their own cataloging, but only to build their own bibliographic database, with no commercial use or transfer — [CALIS 非高校成员馆服务协议 (lawinsider)](https://lawinsider.com/zh/contracts/amXDAsuA25k); [CALIS agreement PDF (sdu)](https://calis.sdu.edu.cn/lhbm/3.pdf)
- 国家图书馆 联合编目中心: IFLA material confirms that NLC is the national bibliographic control agency and that its online cataloging center gathers records from member libraries. **I found no official public page on download pricing, Z39.50 open access, or license terms** — [IFLA national bibliography practices (zh)](https://repository.ifla.org/bitstream/123456789/2189/1/common-practices-for-national-bibliographies-in-the-digital-age-zh.pdf)
- General Z39.50 directories warn that some servers need authentication and that listed parameters may be out of date — [Koha Z39.50 directory](https://kohasupport.com/?p=9241)
- Ex Libris Alma documentation: in **MARC21** records, mainland Chinese classification is read from 090 $a / 093 $a, and **in CNMARC from 690 $a**. Taiwan's classification is read from 084 $a when $2 = `ncsclt` — [Ex Libris Alma "Other Classifications"](https://knowledge.exlibrisgroup.com/Media_Repository/Alma/Analytics_Reused_Content/Other_Classifications)

### Inferences
- CNMARC with 606/690 is the ideal label source for Chinese Annif (中图法 + 汉语主题词). But the available paths are (a) partner with a library that owns the records and get an internal-use agreement, or (b) a purchased NLC/CALIS service. Neither allows public release of a training set, so neither fits an open teaching demo.
- Harvesting a public OPAC or Z39.50 server for a few records to teach the format (for example 50–200 records as a sample) is low-risk in practice. Bulk harvesting (10k+) would likely conflict with CALIS-style "不得转交第三方" terms and with the copyright claims commonly made over cataloging data. That is my inference, not legal advice.
- For a paper replication, contact the DCMI-2026 authors (Xin Yang, Junzhi Jia, Ying-Hsang Liu) to ask about data access.

### Gaps
- No primary-source NLC (nlc.cn) terms for Z39.50, SRU or OAI-PMH were found. Whether NLC runs a public anonymous Z39.50 endpoint today was not verified.
- 国家图书馆 Linked Open Data (an earlier "国家图书馆 关联数据" pilot) was not checked this session.
- Mainland university open-data portals (for example 北大开放研究数据平台) were not searched for catalog dumps.

---

## Q2. MARC21 open datasets that contain Chinese books (LC, Harvard, Open Library, HathiTrust, POD, etc.)

### Takeaway
The cleanest large source is the **Harvard Library Bibliographic Dataset** (CC0, 12.7M+ MARCXML records, on Dataverse). It almost certainly holds a large Harvard-Yenching Chinese subset with LCSH/LCC and 880 vernacular fields. **LC MDSConnect Books All** (2016 retrospective, free download) is just as rich. However, LC states that its records are **copyrighted for use outside the United States**, which matters for a China- or Taiwan-based project. POD (Ivy Plus) is closed. Labels from these sources are LCSH/LCC in English, not Chinese subject terms.

### Cited Findings
**Harvard Library Bibliographic Dataset (confirmed)**
- More than 12.7 million bibliographic records with holdings, in **MARCXML**, split into files of about 200,000 records each, with a datasheet on Dataverse (file ID 7036110). DOI **10.7910/DVN/I8L0ZZ** — [Harvard open metadata](https://library.harvard.edu/open-metadata); [Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/I8L0ZZ)
- License: **CC0 1.0**, with no legally binding conditions. Harvard asks for credit to Harvard Library, OCLC and LC, and asks users of WorldCat-derived records to follow the OCLC WorldCat Rights and Responsibilities — [Harvard open metadata](https://library.harvard.edu/open-metadata)
- Separate from this, Harvard's LibraryCloud corpus (positioned partly for LLM training) is **request-only and limited to non-profit, educational and research use**. It is not CC0 — [Harvard APIs & datasets](https://library.harvard.edu/services-tools/harvard-library-apis-datasets)
- Harvard sends daily incremental files to POD — [Harvard wiki (POD aggregator)](https://harvardwiki.atlassian.net/wiki/spaces/LibraryStaffDoc/pages/43377234/POD+Aggregator+IvyPlus+data+set+and+mapping+aka+Data+Lake)

**Library of Congress MDSConnect "Books All" (confirmed)**
- The MDSConnect open-access service as a whole holds "nearly 25 million MARC records" from the 2016 Retrospective file sets, made available "primarily for research and development usage". Formats are UTF8 and XML — [LC CDS marcDist](https://www.loc.gov/cds/products/marcDist.php)
- The Books All page lists 211 files: 2016 UTF8 (44 = combined + parts 01–43), 2016 XML (44), and 2014 UTF8, MARC8 and XML (41 each). URL pattern: `https://www.loc.gov/cds/downloads/MDSConnect/BooksAll.2016.part01.utf8.gz` (also `.combined.`, `.xml.gz`). No sizes, counts or license are shown on the page — [LC Books All](https://www.loc.gov/cds/products/MDSConnect-books_all.html)
- **Rights:** CDS pages state that "MARC records originating with LC are copyrighted by the Library for use outside the United States". Subscribers may redistribute selectively outside the US after contacting LC — [LC MDS FTP page](https://loc.gov/cds/mdsftp.html); [order form](https://www.loc.gov/cds/forms/mdsftp_form.php)
- LC records cover materials in hundreds of languages in original scripts, Chinese included. Historically LC sold a separate "Books CJK" product — [LC ILS FAQ](https://loc.gov/ils/ilsfaq.html)
- LC metadata is already used for Chinese-subject research: a 2026 Information Research paper analyzed **18,564 LC books on Chinese history**. This is a subject-based subset, not all Chinese-language records — [Information Research / publicera.kb.se](https://publicera.kb.se/ir/article/view/64266). (The full text would not load. The paper's data source and method were not verified.)
- A 2017 InfoDocket report on the release says the records include title, author, date, subject headings, genre, related names, summaries and other notes — [InfoDocket 2017](https://www.infodocket.com/2017/05/16/a-lot-of-data-library-of-congress-releases-25-million-free-records-of-bibliographic-metadata/)

**POD (Platform for Open Data, Ivy Plus) (confirmed: closed)**
- About 435M records (100M unique) from 16 institutions. A CNI 2025 slide calls it "A Closed Lake, for Now". Sharing is limited to designated purposes such as ILL and linked-data conversion — [CNI 2025 slides](https://www.cni.org/wp-content/uploads/2025/05/CNI_Why_Warner.pdf)
- Yale releases its own metadata as CC0, but WorldCat-derived records go out under **ODC-BY with credit to OCLC** — [Yale guide](https://guides.library.yale.edu/c.php?g=923429)

**Open Library dumps (partly confirmed)**
- Dumps are published monthly as TSV with a JSON column. Editions about 9.2 GB, works about 2.9 GB, all types about 12.4 GB compressed. The dumps page gives no license and no description of subject or LCC/DDC fields — [Open Library dumps](https://openlibrary.org/developers/dumps)

**CLC in MARC21 084**
- Confirmed only for Taiwan's scheme: `084 $2 ncsclt` (Alma docs, above). **I found no source confirming `084 … $2 clc` usage in OCLC, LC or Harvard records** — [Ex Libris](https://knowledge.exlibrisgroup.com/Media_Repository/Alma/Analytics_Reused_Content/Other_Classifications)
- In 2002, OCLC required Chinese contributors to add pinyin, DDC or LCC, and LCSH or MeSH to records — [Niu, "Building a national or international China bibliographic utility"](https://www.emerald.com/insight/content/doi/10.1108/10650750210450112/full/html)

### Inferences
- **Estimate (not verified):** Harvard-Yenching and LC both have very large Chinese collections. The Chinese-language subset (008/35-37 = `chi`) is probably in the **hundreds of thousands** of records in each of Harvard and LC Books All, most with LCSH 650 and LCC 050/090. Count it yourself (see the script sketch below) before quoting a number.
- Background knowledge, not verified this session: CJK records in LC and Harvard (RLIN/OCLC heritage) normally carry romanized 245/260/490 plus **880 vernacular fields** linked by $6, so Chinese-script titles are available. LCSH are English strings, so an Annif demo would map Chinese titles to English LCSH (or to LCC classes). That works for teaching. To get Chinese-language labels you would need an LCSH→Chinese crosswalk.
- **Text per record is thin**: mostly the title (245 $a $b plus 880), series 490, notes 500, sometimes contents 505. Summary 520 is uncommon on Chinese-language academic-library records. Plan on "title (+ subtitle + series + 505)" as the Annif text.
- A few "clc" 084 fields may exist where catalogers kept vendor-supplied CLC numbers. Measure with a filter on `084$2 == "clc"` (the source code "clc" should be checked against LC's Classification Scheme Source Codes list).
- Practical extraction (Harvard, CC0):
  1. Download the MARCXML parts from Dataverse DOI 10.7910/DVN/I8L0ZZ, one directory per download.
  2. Stream-parse with `pymarc.parse_xml_to_array` or an iterparse loop. Keep records where `008[35:38] == 'chi'` (or 041 $a contains `chi`).
  3. Text = 880 fields whose $6 starts with `245` (Chinese-script title), else the romanized 245. Optionally add 880-490, 880-505 and 520.
  4. Labels = 650 with ind2 = 0 (LCSH) $a and its subdivisions, and/or 050/090 $a class stems (for example the first letters plus digits).
  5. Write an Annif TSV corpus (`text<TAB><uri1> <uri2>`). LCSH URIs come from id.loc.gov (`http://id.loc.gov/authorities/subjects/shXXXX`), which needs heading→URI reconciliation against the LCSH dump.
- LC Books All works with the same pipeline (UTF8 MARC21 binary, so use `pymarc.MARCReader`). Treat it as US-only or internal use given the copyright statement.

### Gaps
- Exact Chinese-record counts for Harvard, LC, Open Library and HathiTrust were not found and must be measured.
- Books All file sizes and record counts are not on the LC page. The CDS FAQ and "Getting Started" PDFs were not read.
- Open Library's license (often described as public domain or CC0 elsewhere) was not confirmed on a primary page.
- **HathiTrust Hathifiles, Michigan, Princeton, Stanford, BnF and NDL were not examined this session** (tool budget). Background knowledge, unverified: Hathifiles are tab-delimited and lack subject headings, and full MARC comes from Zephir or OAI under separate terms. NDL Search offers bibliographic downloads in MARC, TSV, JSON and other formats — [NDL data service](https://www.ndl.go.jp/en/data/data_service). Its Chinese-language holdings and license were not checked.

---

## Q3. Taiwan: 國家圖書館 / NBINet / data.gov.tw datasets with 中文圖書分類號 and 主題詞

### Takeaway
Taiwan has the **clearest open license** (政府資料開放授權條款 v1, explicitly compatible with CC BY 4.0). However, it has **no large open MARC dump with subjects**. What exists is (a) small agency library catalogs as CSV with 中文圖書分類法 call numbers or class numbers (about 20k rows each) and (b) the NCL 中文主題編目規範 vocabulary (subject terms ↔ class numbers). There are also (c) the ISBN Center's monthly 新書書目 PDFs, which list **主題詞 + 分類號 per new book**. They are rich but semi-structured, and their license is unclear. NBINet itself has no downloadable file.

### Cited Findings
- **License (confirmed):** the Open Government Data License v1.0 grants a perpetual, worldwide, royalty-free license for any purpose, including derivatives and sublicensing. Attribution in the prescribed format is required, and the license states that it is **compatible with CC BY 4.0** (§4.2) — [data.gov.tw license](https://data.gov.tw/license)
- **國家圖書館 中文主題編目規範** (dataset 27190): fields include 主題詞, 類號八版 and 類號2007版. CSV, OGDL v1, free, irregular updates. This is a vocabulary/authority file (useful as the Annif vocabulary), not book records — [data.gov.tw/dataset/27190](https://data.gov.tw/dataset/27190)
- **國發會圖書室 中文圖書清單** (dataset 28528): CSV, OGDL v1, updated every 6 months, last updated 2026-06-02 — [data.gov.tw/en/datasets/28528](https://data.gov.tw/en/datasets/28528). **Checked locally:** a 3.9 MB CSV (served as .xls), header `序號,題名,作者,出版者/出版地,出版年(民國年),版次,索書號,ISBN,頁數`, and **about 21,276 data lines**. The 索書號 field carries the 中文圖書分類法 number (for example `book 445.103 0032`). There is no subject column, and titles are often duplicated within the field (download URL from the dataset page: `ws.ndc.gov.tw/Download.ashx?...`).
- **經濟部智慧財產局圖書室館藏目錄** (dataset 123143): fields 登錄號, 題名, 作者, 出版者, 出版年, ISBN, 資料別, 語文別, **分類號**. CSV, updated yearly, OGDL v1 — [data.gov.tw/dataset/123143](https://data.gov.tw/dataset/123143) (from the search summary; the page was not opened and the row count is unknown)
- **檔案管理局 圖書自動化系統書目資料** (dataset 31293): no classification field — [data.gov.tw/dataset/31293](https://data.gov.tw/dataset/31293)
- **國家圖書館 客家研究文獻書目資訊** (22092): title, author, publisher, year and journal fields. No class number was seen in the summary — [data.gov.tw/dataset/22092](https://data.gov.tw/dataset/22092)
- **NBINet** (union catalog of NCL and partners, including ISBN Center new-book records): the SciDM mirror lists it under OGDL v1 but shows "This dataset has no data" — [SciDM NBINet](https://scidm.nchc.org.tw/en/dataset/best_wish7502)
- **ISBN Center monthly 新書書目 (PDF)**: each record lists 書名, 作者, 版次, 出版項, 稽核項, 集叢項, ISBN, 冊次號, 裝訂, 價格, **主題詞, 分類號**. 主題詞 follow 《中文主題詞表》2005 rev. and classes follow 中文圖書分類法 2007. Coverage is each month's ISBN applicants, with PDFs seen for about 2018–2024. Example: 《科技創新書目》 ISBN 978-957-678-687-7 → 主題詞「推薦書目」, 012.4 — [isbn.ncl.edu.tw PDF example](https://isbn.ncl.edu.tw/FCKEDITOR_UploadFiles/1596771809.pdf); [another month](https://isbn.ncl.edu.tw/FCKEDITOR_UploadFiles/1700204316.pdf)
- Background: the ISBN Center renamed its site 全國新書資訊網 (ISBNnet) in 1998 and began a bibliographic download service in October 1998. A 2017 NCL article describes Aleph X-Service data exchange and a cover-image API, but no open new-book API — [NCL 館訊 PDFs via nclfile.ncl.edu.tw](https://nclfile.ncl.edu.tw/files/201708/8827fbbf-d5b6-472a-beee-ea061fe29b63.pdf)

### Inferences
- The 新書書目 PDFs are the best Taiwan source for **Chinese text → Chinese subject terms + class number**. Taiwan publishes on the order of tens of thousands of ISBN titles a year (an estimate, not sourced here), so parsing several years of PDFs could give a corpus of 50k–200k records. However: (1) the PDFs are hosted on isbn.ncl.edu.tw, not data.gov.tw, so OGDL is not confirmed to apply; check the site's copyright notice or ask NCL. (2) PDF table parsing is fiddly. (3) Text is title only.
- The agency CSVs (國發會 about 21k, 智慧局 unknown) give **Chinese title → 中文圖書分類法 class**. These are good for a small, fully licensed CC-BY-compatible classification demo. Truncate class numbers to 3 digits (for example 445, 553) to reduce sparsity. Labels must be mapped to URIs that you mint yourself, because there is no public SKOS for 中文圖書分類法. Pair them with the 中文主題編目規範 CSV to build the vocabulary.

### Gaps
- No primary page confirms a bulk MARC download from NCL or NBINet, or OAI-PMH access for third parties.
- The row count of the 智慧局 dataset, and other ministry or public library CSVs on data.gov.tw (for example 臺北市立圖書館), were not enumerated.
- The license of the ISBN Center PDFs and of 全國新書資訊網 is unverified.

---

## Q4. Other sources: Douban, NLC Linked Open Data, OCLC WorldCat

### Takeaway
Douban has no open book-tag dataset. The only routes are third-party scrapers, which carry ToS risk. WorldCat is not open (OCLC terms, and ODC-BY attribution where member libraries re-release records). NLC linked open data was not verified.

### Cited Findings
- No Kaggle or GitHub Douban book-tag dataset was found. Apify scrapers extract Douban book tags, genres and ratings, and these are paid tools — [Apify Douban Scraper](https://apify.com/poetsc/douban-scraper)
- Research on Douban book tags (陈婵 2020, 文献与数据学报) reports Douban's 6 top tag categories and 143 popular tags. Raw data release is unclear — [paper PDF](https://wxysjxb.ajcass.com/Admin/UploadFile/Issue/1yeaaycx.pdf)
- The closest open tag datasets are Goodreads-based (goodbooks-10k; the Tag Genome for Books), which are English — [goodbooks-10k](https://baselight.app/u/kaggle/dataset/zygmunt_goodbooks_10k); [Tag Genome for Books](https://research.abo.fi/sv/publications/the-tag-genome-dataset-for-books/)
- WorldCat-derived records re-released by Yale go out under ODC-BY with OCLC credit. Harvard asks users to follow the WorldCat Rights and Responsibilities — [Yale](https://guides.library.yale.edu/c.php?g=923429); [Harvard](https://library.harvard.edu/open-metadata)

### Inferences
- Douban tags are folksonomy, not controlled subjects, and scraping at scale likely breaches Douban's ToS. Not recommended, even for teaching.

### Gaps
- 国家图书馆 linked data / 中文名称规范 open services were not checked this session.
- The HuggingFace hub was not browsed directly (search only).

---

## Q5. Which single source is most practical for a demo (about 10k–200k Chinese records with subjects)?

### Takeaway
For a **legally clean, scalable** demo: the **Harvard Library Bibliographic Dataset (CC0)**, filtered to `008/35-37 = chi`. Text is the 880 Chinese-script title (plus series and contents); labels are LCSH 650 (or LCC 050 class stems). For a **small demo with Chinese-language labels**: Taiwan OGDL CSVs (國發會 about 21k titles with 中文圖書分類法 call numbers, plus the 智慧局 catalog), with the NCL 中文主題編目規範 CSV as the vocabulary. Both are license-safe. Only the Taiwan route gives Chinese labels, and only the Harvard route gives subject headings at scale.

### Cited Findings
- Harvard: CC0, 12.7M+ MARCXML, files of about 200k each, Dataverse DOI 10.7910/DVN/I8L0ZZ — [Harvard](https://library.harvard.edu/open-metadata)
- LC Books All: free, but LC claims copyright outside the US — [LC CDS](https://loc.gov/cds/mdsftp.html)
- Taiwan OGDL v1 is CC BY 4.0 compatible — [data.gov.tw license](https://data.gov.tw/license); 國發會 catalog CSV — [28528](https://data.gov.tw/en/datasets/28528); vocabulary — [27190](https://data.gov.tw/dataset/27190)
- CNMARC has no open source; CALIS forbids transfer to third parties — [CALIS agreement](https://lawinsider.com/zh/contracts/amXDAsuA25k)

### Inferences
- Suggested demo plan:
  - **Step A.** Download 3–5 Harvard MARCXML parts (about 1M records). Filter Chinese, which should yield tens of thousands of records (estimate, needs measuring). Build `train.tsv` with Chinese titles and LCSH or LCC labels. Train Annif `tfidf`/`omikuji` with a Chinese analyzer (jieba or a character n-gram analyzer).
  - **Step B.** For the Chinese-vocabulary track, use the 國發會 CSV, keeping rows where 索書號 starts with `book ` + digits. Truncate the class number to 3 digits and use the 中文主題編目規範 CSV for class labels.
  - Measure before committing: count `chi` records, the share with 880-245, the share with 650 _0, the share with 050, and any 084 $2 values (to find stray CLC or `ncsclt`).
- Production path: negotiate a CNMARC export (606/690/330) from a partner mainland library under a written internal-use agreement. Or pursue NCL Taiwan for structured 新書書目 data (主題詞 + 分類號) under OGDL.

### Gaps
- No measured Chinese-record counts for any MARC21 source. All counts above are estimates until the filter script is run.
- Whether Harvard's Chinese records carry 084 CLC numbers is unknown.
