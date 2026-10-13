# Empirical measurements: Harvard Library Bibliographic Metadata (Chinese records) and NCL 中文主題詞表 CSV

Measured 2026-10-13 by direct API calls and file downloads. All numbers below come from files or API responses retrieved that day, unless explicitly labelled "estimate" or "extrapolation".

## Q1. Harvard Library Bibliographic Dataset (doi:10.7910/DVN/I8L0ZZ): how many usable Chinese records with subject headings?

### Takeaway
**No Chinese-record counts could be measured.** Every MARCXML file in the dataset sits behind a mandatory Dataverse guestbook. The guestbook requires name, email, institution and position. Submitting personal data in a form needs the user's explicit permission, so no data file was downloaded, and the Chinese-subset counts, the LCSH and LCC coverage figures, the top-30 headings and the sample records are all still open. What could be measured is the file inventory: 67 unique files, about 7.2 GB compressed, and 200,000 records per file. From those, the total size of the dataset can be estimated at about 13.3 million records.

### Cited Findings
- **Dataset version and licence:** version 1.0, released 2023-03-31, licence CC0 1.0. The snapshot is dated 2022-02-15 (productionDate) and has not been updated since, so as of October 2026 the data is about 4.7 years old. — [Dataverse dataset API](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/I8L0ZZ)
- **File inventory (measured from the API):**
  - The API lists **68 file entries totalling 7,229,160,049 bytes (about 7.23 GB, gzip)**.
  - One entry is a duplicate: `20220215_022.bib.xml-1.gz` (id 7028674) has exactly the same size (107,189,763 bytes) as `20220215_022.bib.xml.gz` (id 7019265). That leaves **67 unique files, `_001` to `_067`**, about 7.12 GB.
  - Files `_001` to `_065` each hold about 105–108 MB compressed. `_066` is 127.0 MB and `_067` is 61.8 MB.
  - No single file is close to the 1.5 GB limit.
  - The content type is labelled `application/zip`, but the files are gzip.
  - — [Dataverse dataset API](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/I8L0ZZ)
- **Inconsistent part count:** the description of file 7019243 says "File part: 34 of 46", which conflicts with the 67 files actually listed. Treat the "of 46" label as stale. — [Dataverse file API, id 7019243](https://dataverse.harvard.edu/api/files/7019243)
- **Download is blocked by a guestbook:**
  - `GET /api/access/datafile/7019243` (and 7019253) returned HTTP 400: "You may not download this file without the required Guestbook response for guestbookID 514."
  - Guestbook 514 ("Open metadata user survey") has `emailRequired`, `nameRequired`, `institutionRequired` and `positionRequired` all set to true. It also has 4 optional questions (planned use, questions, follow-up yes/no, role).
  - The files are not marked restricted (`"restricted":false`), but `fileAccessRequest` is true.
  - — [Dataverse guestbook API](https://dataverse.harvard.edu/api/guestbooks/514); [file API](https://dataverse.harvard.edu/api/files/7019243)
- **Alternative route also failed:** Harvard's public LibraryCloud Item API (`api.lib.harvard.edu/v2/items`), which could have returned `languageCode=chi` counts for the whole catalogue, returned **HTTP 429 from the AWS load balancer** on every attempt. It failed over both https and http and with a browser user agent, so it gave no data from this network on 2026-10-13. — [Harvard Library APIs & Datasets page](https://library.harvard.edu/services-tools/harvard-library-apis-datasets)
- **LibraryCloud scale (Harvard's own description):** "records from Harvard's Alma instance (over 12.7M bib records)", with Alma metadata "enriched with … LC classification subject headings". — [Harvard Library APIs & Datasets](https://library.harvard.edu/services-tools/harvard-library-apis-datasets)
- **What the official datasheet says** (v1.0, 2 Feb 2023; downloadable without a guestbook from the companion "Detailed Content Inventory" dataset doi:10.7910/DVN/Y5WUTU):
  - "Each XML file except the last contains 200,000 <records>."
  - Total instance count: "This information is not currently available."
  - Scope: all active, non-suppressed Alma bib records with at least one active holding.
  - The datasheet gives **no language breakdown**.
  - Every record has the leader, 001, 008 and 245. Holdings data is embedded in each record.
  - Harvard notes that similar datasets "have been used … as training sets for automated subject heading assignment".
  - Community norms ask for attribution to Harvard Library and OCLC, and point to the WorldCat Rights and Responsibilities norms for records that came from WorldCat.
  - The dataset was first shared with the POD aggregator (pod.stanford.edu).
  - — [Datasheet PDF, Dataverse file 7036110](https://dataverse.harvard.edu/api/access/datafile/7036110); [Content-inventory dataset](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/Y5WUTU)

### Inferences
- **Estimated total size of the dataset (my estimate, not a measurement):** 66 files × 200,000 = 13,200,000 records, plus the last file. If `_067` (61.8 MB) is scaled by the average size of the full files (about 106.5 MB per 200k records), it holds roughly 116,000 records. That gives **about 13.3 million records** in total, which is consistent with Harvard's "over 12.7M" Alma figure.
- Note that `_066` is about 19% larger than the other files for the same nominal 200k records. Records near the end of the sequence are probably longer, for example because of more 880 or holdings fields.
- **Not done: Chinese-share extrapolation.** I made none, because I had no measured Chinese share to work from. Any figure for Harvard Chinese records in this dataset would be invented. The Harvard-Yenching collection is known to be large, but that is a holdings count, not a count of `chi` records with LCSH in this dump.
- **The block is easy to clear.** Once the user (or someone with their consent) submits the guestbook in a browser, or calls the access API with a `guestbookResponse` JSON body, the measurement can run unchanged. A streaming parser is ready at `/private/tmp/claude-501/-Users-keven-Documents-kimi-Workspaces-cnLSP/126ccda3-eb43-4966-95ba-65faf8dcf519/scratchpad/scripts/harvard_chi_stats.py`, with a pymarc venv in `.../scratchpad/venv`. Run it as `venv/bin/python -I harvard_chi_stats.py <file.gz>`. It produces every count requested in the brief: total, `chi`, 650 with second indicator 0, 050/090, 084 by $2, 880/245 in Chinese script, 520, 505, the distribution of 650s per record, top 30 $a, and 5 samples.
- **Recommendation for sampling:** files probably follow MMS ID order, which roughly tracks load or creation date. Chinese records may therefore cluster in certain files, so sample at least two files that are far apart (for example `_010` and `_060`) before extrapolating.

### Gaps
- Not measured, because the guestbook blocked every data file:
  - Total record count per file
  - Count of `chi` records
  - Coverage of LCSH, LCC, 084, 880 titles, 520 and 505 among Chinese records
  - Distribution of 650s per Chinese record
  - Top 30 headings
  - Sample records
- POD (pod.stanford.edu) carries the same Harvard data, but its organisation page redirects (HTTP 302), probably to a login. Access tokens are issued to participants, so it was not tried as a substitute.
- I could not check whether Harvard has published a newer snapshot outside this DOI. The Dataverse dataset is still at version 1.0.

## Q2. NCL (Taiwan) 中文主題編目規範 CSV, data.gov.tw dataset 27190

### Takeaway
The file downloaded and parsed cleanly. It contains **19,325 heading rows**: 17,125 preferred terms and 2,200 non-preferred "用" entries. Encoding is UTF-8 with BOM, line endings are CRLF, and there are 12 columns, 2 of them blank. **18,406 rows (95.2%) carry at least one 中文圖書分類法 number** (8th edition and/or 2007 edition). Equivalence relations (用/不用) and associative see-also relations (參見) are present. **There are no broader/narrower (BT/NT) hierarchy columns.**

### Cited Findings
- **Dataset metadata:**
  - Title 中文主題編目規範 (English: "Chinese Subject Headings Standard"), identifier A09050000E-000031, publisher National Central Library (NCL).
  - Licence code "1": Open Government Data License v1.0, free of charge.
  - Format CSV, declared encoding UTF-8.
  - First published 2016-02-17, last modified **2026-09-23 09:25:57**, coverage dates 2000-01-01 to 2016-01-04, update frequency irregular.
  - Related URL: https://catsmart.ncl.edu.tw/
  - The declared field list matches the actual header.
  - — [data.gov.tw API, dataset 27190](https://data.gov.tw/api/v2/rest/dataset/27190)
- **Download:**
  - Download URL: `https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137`
  - The first plain-curl attempt returned HTTP 503. The retry, with a browser user agent and a data.gov.tw referer, returned HTTP 200.
  - File size **1,472,821 bytes**, SHA-256 `0987613b4b7fb8d97364b72d122c5104a41481c9912b0dd8e3c96a632c5b2974`.
  - — [NCL OpenDataFile](https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137)
- **Encoding and shape (measured):**
  - UTF-8 with BOM, CRLF line endings, 19,326 lines (1 header + 19,325 data rows).
  - Every row has exactly 12 fields. No embedded newlines were found.
  - Header: `序號, 主題詞, 類號八版, 類號2007版, 原文, 注釋文字, 用, 不用, 參見, 網址, '', ''`. The last two columns are empty in every row.
  - 序號 runs from 1 to 19325. All 19,325 主題詞 values are unique, and 19,255 of them contain CJK characters.
  - Headings are short: mean 3.7 characters, maximum 12. Almost none are pre-coordinated: only 1 heading contains a "--" or "－" subdivision.
  - Script is **Traditional Chinese**.
  - The 網址 column holds the same constant value in every row (`https://catsmart.ncl.edu.tw/`), so there are **no per-heading URIs**.
  - — [NCL OpenDataFile](https://www.ncl.edu.tw/OpenDataFile/0Q159425757879451103/5c096f68-de74-4793-9fb7-df1328d88137)
- **Column fill counts (non-empty cells, out of 19,325 rows):**
  - 類號八版: 17,036
  - 類號2007版: 16,270
  - 原文 (English or original-language equivalent): 3,614
  - 注釋文字 (scope note): 332
  - 用: 2,200
  - 不用: 1,851
  - 參見: 1,288
  - — same file
- **Classification numbers (中文圖書分類法):**
  - Rows with at least one class number (either edition): **18,406** (95.2%). Rows with both editions: 14,900.
  - **Among the 17,125 preferred terms**, 17,087 have a class number in at least one edition and 14,984 have a 2007-edition number.
  - The 1,319 non-preferred rows also carry class numbers.
  - Many rows hold several numbers, with inconsistent separators: in 類號2007版, "；" appears in 327 rows and ";" in 3,467. Some values have a trailing "; ".
  - Some values are bracketed, e.g. `[312.1161]`, `[956.6 ; 947.41 ; 997.82]`, which marks an alternative or obsolete number.
  - First digit of the 2007 number (main class) across all rows:
    - 0: 102
    - 1: 901
    - 2: 761
    - 3: 3,534
    - 4: 4,197
    - 5: 4,319
    - 6: 390
    - 7: 379
    - 8: 639
    - 9: 1,023
    - blank: 3,057
  - Coverage is therefore heavily weighted towards 3 (natural science), 4 (applied science) and 5 (social science). History/geography (6/7) and literature (8) are thin.
  - — same file
- **Relations:**
  - **用 (USE) / 不用 (UF):**
    - 2,200 rows are non-preferred entries that point to a preferred term via 用. 2,187 of those targets exist as 主題詞 rows.
    - The 不用 column splits into 2,197 UF terms (separators are mostly ",", plus "、", "；" and ";"). For 2,149 of them a reciprocal 用 row exists.
  - **參見 (see also, RT):**
    - 1,596 pairs.
    - 1,370 are reciprocal.
    - When split only on semicolons, 1,083 of 1,300 targets resolve to a heading row.
  - **No BT/NT columns exist.** The hierarchy cannot be reconstructed from this file.
  - — same file
- **First 10 rows, verbatim** (only columns 序號 | 主題詞 | 類號八版 | 類號2007版 | 原文 | 用 | 不用 | 參見 are shown):
  1. 1 | 301貿易法案 | 558.2 | 558.2 | Section 301 of Trade Act | – | 三Ο一條款 | –
  2. 2 | 5羥色胺接受器 | 361.28；398.33；398.911 | 398.29 | Serotonin receptor | – | – | –
  3. 3 | AIDS | – | – | Acquired Immunodeficiency Syndrome | 愛滋病 | – | –
  4. 4 | APEC | – | – | – | 亞太經濟合作會議 | – | –
  5. 5 | ATM | – | – | Automatic Teller Machine | 自動櫃員機 | – | –
  6. 6 | A型肝炎 | 415.2684；415.533 | 415.5332 | Hepatitis A | – | – | –
  7. 7 | B B Call | – | – | – | 傳呼機 | – | –
  8. 8 | BBS | – | – | – | 電子佈告欄 | – | –
  9. 9 | Blog | – | – | – | 部落格 | – | –
  10. 10 | BOT | – | – | – | 公辦民營 | – | –
- **Additional random rows** (seed 42, chosen from rows that have a 2007 number plus a relation):
  - 嬰兒搖晃症候群 | 417.59 | Shaken baby syndrome | 參見 兒童虐待
  - 左聯 | 820.6 | 不用 左翼作家聯盟
  - 大腸癌 | 415.569 | Colon cancer；Colonic neoplasm | 參見 大腸直腸癌
  - 伊斯蘭教 | 250; 254.4 | 不用 回教
  - 柬埔寨文學 | 868.4 | 不用 高棉文學
  - 鞏皮症 | 415.763 | 不用 硬皮症
  - 比較文字學 | 800.9；801.41 | 參見 文字學
  - 動漫 (the last row, #19325) | 8th ed. `[956.6 ; 947.41 ; 997.82]` | 2007 `947.41; 956.6`
- **Example scope notes:** HTML → "文件標記語言。"; WAP → "無線應用通訊協定。"; MIDI → "Musical instrument digital interface".

### Inferences
- **Usable vocabulary for Annif: about 17,125 preferred concepts**, with about 2,200 alternative labels from the 用 rows. That is a small but workable SKOS vocabulary (prefLabel, altLabel, related, plus a notation from 中文圖書分類法).
- **Building a SKOS file needs some work first:**
  - Mint URIs, because the source has none.
  - Normalise the class-number separators (";", "；", ",", "/") and the brackets.
  - Accept a flat vocabulary with no broader/narrower links.
- **Format mismatch with Harvard.** Headings are short Traditional-Chinese single concepts. They do not line up with LCSH-style English strings carrying "--" subdivisions, so mapping Harvard LCSH onto this vocabulary is not straightforward.
- **The coverage dates (2000–2016) clash with the 2026-09-23 modification date.** The latter may only be a metadata or quality-check refresh (resourceQualityCheckTime is the same day). I cannot tell whether any headings were added after 2016.

### Gaps
- **Dataset size, conflicting figures:** data.gov.tw reports `resourceAmount: 1000`, while the file has 19,325 rows. The platform field looks like a placeholder.
- **No training data:** this CSV contains no bibliographic records tagged with these headings, so it supplies no training documents for Annif.
- **CatSmart not checked:** I did not check whether catsmart.ncl.edu.tw offers a fuller vocabulary with BT/NT or URIs (an API or SKOS export).

## Files and housekeeping
- **Kept in scratchpad (small):**
  - `scratchpad/downloads/ncl/csh.csv` (1.47 MB)
  - `scratchpad/downloads/harvard/datasheet.pdf` (120 KB)
  - In `scratchpad/scripts/`: `dv.json`, `inv.json`, `dg27190.json` (API responses), `datasheet.txt`, `ncl_stats.py`, `harvard_chi_stats.py`
- **No large Harvard files were downloaded.** Only two 122-byte error stubs were created, and both were deleted.
