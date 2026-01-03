# BÁO CÁO LAB 02: HIERARCHICAL PARSING & REFERENCE MATCHING

**Môn học:** Nhập môn Khoa học Dữ liệu  
**Giảng viên:** Huỳnh Lâm Hải Đăng  
**Sinh viên:** [Họ và tên]  
**MSSV:** 23127332  
**Lớp:** [Mã lớp]

---

## 1. TỔNG QUAN HỆ THỐNG

### 1.1. Mục tiêu
- Xây dựng pipeline xử lý và phân tích dữ liệu LaTeX từ arXiv
- Chuyển đổi dữ liệu không cấu trúc (LaTeX) thành cấu trúc phân cấp
- Áp dụng Machine Learning để matching references

### 1.2. Kiến trúc tổng thể

```
Input: LaTeX files, metadata, references
    ↓
[Module 1: LaTeX Parser] → Gather multi-files
    ↓
[Module 2: Hierarchy Builder] → Build tree structure
    ↓
[Module 3: Content Cleaner] → Standardization
    ↓
[Module 4: BibTeX Processor] → Extract & deduplicate
    ↓
[Module 5: ML Pipeline] → Feature engineering & matching
    ↓
Output: hierarchy.json, refs.bib, pred.json
```

---

## 2. PHẦN 1: HIERARCHICAL PARSING & STANDARDIZATION

### 2.1. Multi-file Gathering

**Vấn đề:** Mỗi publication có nhiều file .tex, cần xác định file chính và các file được include.

**Giải pháp:**
1. Tìm file chứa `\begin{document}` → Main file
2. Parse đệ quy tất cả `\input{}` và `\include{}`
3. Assemble content theo đúng thứ tự

**Xử lý trường hợp đặc biệt:**
- **Nhiều files có `\begin{document}`**: Ưu tiên `main.tex`, nếu không có thì chọn file lớn nhất
  - Ví dụ: Publication 2310-XXXXX có 2 files → Chọn `main.tex`
  
**Kết quả:**
- Tổng số publications xử lý: [X]
- Tổng số versions: [Y]
- Tỷ lệ thành công: [Z%]

### 2.2. Hierarchy Construction

**Cấu trúc cây phân cấp:**

```
Document (Root)
├── Section 1
│   ├── Subsection 1.1
│   │   ├── Paragraph 1
│   │   │   ├── Sentence 1
│   │   │   └── Sentence 2
│   │   ├── Equation 1
│   │   └── Figure 1
│   └── Subsection 1.2
└── Section 2
    └── List
        ├── Item 1
        ├── Item 2
        └── Item 3
```

**Quy tắc parsing:**
- **Smallest elements**: Sentences (split by `.`), Block formulas, Figures/Tables
- **Lists**: `\begin{itemize}` là node cha, mỗi `\item` là node con
- **Exclusions**: References section
- **Inclusions**: Acknowledgements, Appendices (kể cả `\section*`)

**Thống kê:**
- Trung bình số sections per publication: [X]
- Trung bình số sentences per section: [Y]
- Trung bình số equations per publication: [Z]
- Trung bình số figures per publication: [W]

### 2.3. Standardization & Cleaning

**LaTeX cleaning operations:**

| Operation | Description | Example |
|-----------|-------------|---------|
| Remove formatting commands | Loại bỏ `\centering`, `\vspace`, etc. | `\centering` → `` |
| Normalize inline math | Convert `\(...\)` to `$...$` | `\(x^2\)` → `$x^2$` |
| Normalize display math | Convert `$$...$$` to `\begin{equation*}` | `$$x^2$$` → `\begin{equation*}x^2\end{equation*}` |
| Clean whitespace | Remove excessive spaces/newlines | `   ` → ` ` |

**Ví dụ trước và sau cleaning:**

```latex
% Trước
\centering
Some text with $x^2$ and $$y = mx + b$$.

% Sau
Some text with $x^2$ and \begin{equation*}y = mx + b\end{equation*}.
```

### 2.4. Content Deduplication

**Phương pháp:**
1. Compute SHA256 hash của normalized content
2. Nếu hash trùng giữa versions → Reuse element ID
3. Structural nodes (sections) giữ riêng nếu titles khác

**Kết quả deduplication:**
- Tổng elements trước dedup: [X]
- Tổng elements sau dedup: [Y]
- Tỷ lệ dedup: [Z%]

**Ví dụ deduplication:**
```
Version 1: "Introduction section" → ID: 2310-15395-v1-section-1
Version 2: "Introduction section" (same content) → Reuse ID: 2310-15395-v1-section-1
Version 2: "Background section" (new) → ID: 2310-15395-v2-section-2
```

### 2.5. BibTeX Processing

**Xử lý nhiều formats:**
- Ưu tiên `.bib` files
- Fallback sang `.bbl` files (convert về BibTeX)

**BibTeX deduplication:**
1. Extract key fields: title, author, year, journal
2. Compute content hash
3. Merge duplicates (union của fields)

**Ví dụ merge:**
```bibtex
% Entry 1
@article{Smith2020,
  title = {Machine Learning},
  author = {Smith, John}
}

% Entry 2 (same paper, different key)
@article{Smith:2020abc,
  title = {Machine Learning},
  author = {Smith, John},
  journal = {Nature}
}

% Merged (keep all fields)
@article{Smith2020,
  title = {Machine Learning},
  author = {Smith, John},
  journal = {Nature}
}
```

**Key mapping:** `Smith:2020abc` → `Smith2020`

**Thống kê:**
- Tổng BibTeX entries: [X]
- Entries sau dedup: [Y]
- Tỷ lệ dedup: [Z%]

---

## 3. PHẦN 2: REFERENCE MATCHING PIPELINE

### 3.1. Bài toán và Phương pháp

**Định nghĩa bài toán:**
- **Input**: BibTeX entry (từ refs.bib) và references.json (metadata từ API)
- **Output**: Top-5 arXiv IDs candidates
- **Evaluation**: Mean Reciprocal Rank (MRR)

**Phương pháp:**
- Supervised Learning - Binary Classification
- Random Forest Classifier
- Ranking based on prediction probabilities

### 3.2. Data Labeling

**Manual labeling:**
- Số publications gán nhãn thủ công: [5+]
- Tổng số pairs đã gán nhãn: [20+]

**Publications được chọn cho manual labeling:**
1. 2310-XXXXX: [X pairs]
2. 2310-XXXXX: [Y pairs]
3. ...

**Auto labeling (10% remaining data):**
- Phương pháp: Regex matching arXiv ID trong BibTeX
- Heuristic: Title similarity > 0.9 AND author overlap > 0.5
- Số pairs auto-labeled: [Z]

### 3.3. Feature Engineering

**Features được sử dụng:**

| Feature ID | Feature Name | Description | Rationale |
|------------|--------------|-------------|-----------|
| F1 | Title Token Overlap | Jaccard similarity of title words | Titles giống nhau → Same paper |
| F2 | Title Levenshtein | Normalized edit distance | Handle typos and variations |
| F3 | Title Length Ratio | min(len1,len2)/max(len1,len2) | Very different lengths → Different papers |
| F4 | Author Similarity | Exact + partial (last name) matching | Same authors → Likely same paper |
| F5 | Author Count Diff | abs(count1 - count2) | Author list completeness |
| F6 | Year Similarity | 1.0 if same, 0.5 if ±1 year | Papers published around same time |
| F7 | Has arXiv ID | arXiv ID present in BibTeX text | Strong indicator of match |

**Feature Distribution Analysis:**

[Histogram/Box plots showing feature distributions for positive vs negative examples]

**Feature Importance:**

[Bar chart showing feature importance from trained model]

**Top 3 most important features:**
1. F7 (Has arXiv ID): [importance score]
2. F1 (Title Token Overlap): [importance score]
3. F4 (Author Similarity): [importance score]

### 3.4. Model Training & Evaluation

**Data Split:**
- Training set: [X publications, Y pairs]
- Validation set: [A publications, B pairs]
- Test set: [C publications, D pairs]

**Model Configuration:**
```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42
)
```

**Training Results:**
- Training accuracy: [X%]
- Validation accuracy: [Y%]
- Training time: [Z seconds]

**Test Set Evaluation:**

**Mean Reciprocal Rank (MRR):**
$$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{rank_i}$$

- **Test MRR**: [Score]
- **Validation MRR**: [Score]

**Breakdown by rank position:**
| Rank | Count | Percentage |
|------|-------|------------|
| 1 (Perfect match) | [X] | [Y%] |
| 2 | [X] | [Y%] |
| 3 | [X] | [Y%] |
| 4 | [X] | [Y%] |
| 5 | [X] | [Y%] |
| Not in top-5 | [X] | [Y%] |

**Example predictions:**

Publication: 2310-15395
```
BibTeX key: Krnjaic:2023odw
Ground truth: 2307.00041
Predictions:
  1. 2307.00041 (score: 0.95) ✓
  2. 2306.09142 (score: 0.72)
  3. 2305.12345 (score: 0.68)
  4. 2304.56789 (score: 0.55)
  5. 2303.98765 (score: 0.51)
```

### 3.5. Error Analysis

**Common failure cases:**

1. **Incomplete metadata**: BibTeX thiếu title or authors
   - Example: [cite key] - only has "et al." for authors
   - Proposed solution: Use additional features from content

2. **Preprints vs Published versions**: Same paper, different metadata
   - Example: arXiv version vs journal version
   - Proposed solution: DOI matching if available

3. **Similar titles**: Different papers with very similar titles
   - Example: "Deep Learning for X" vs "Deep Learning for Y"
   - Current accuracy: [X%]

---

## 4. KẾT QUẢ VÀ ĐÁNH GIÁ

### 4.1. Thống kê tổng thể

| Metric | Value |
|--------|-------|
| Total publications processed | [X] |
| Total versions processed | [Y] |
| Total hierarchy elements | [Z] |
| Total BibTeX entries | [W] |
| Total reference pairs in test set | [V] |
| Test MRR Score | [Score] |

### 4.2. Thời gian xử lý

| Phase | Time |
|-------|------|
| LaTeX parsing (all pubs) | [X seconds] |
| Hierarchy building | [Y seconds] |
| BibTeX processing | [Z seconds] |
| ML training | [W seconds] |
| **Total** | [Total seconds] |

### 4.3. Challenges & Solutions

**Challenge 1:** [Description]
- **Solution:** [What we did]
- **Result:** [Outcome]

**Challenge 2:** [Description]
- **Solution:** [What we did]
- **Result:** [Outcome]

---

## 5. KẾT LUẬN

### 5.1. Những gì đã đạt được
- ✅ Successfully parsed [X] publications with [Y] versions
- ✅ Built hierarchical structure with [Z] elements
- ✅ Deduplicated [W%] of duplicate content
- ✅ Achieved MRR score of [Score] on test set

### 5.2. Hạn chế và cải tiến trong tương lai

**Hạn chế:**
1. LaTeX parser chưa xử lý tốt một số custom commands
2. BBL to BibTeX conversion có thể mất một số metadata
3. Feature engineering còn đơn giản, chưa dùng embeddings

**Cải tiến:**
1. Sử dụng pre-trained models (BERT, SciBERT) cho title matching
2. Thêm features từ abstract và full-text content
3. Ensemble methods để tăng accuracy
4. Handle cross-references giữa publications

### 5.3. Bài học kinh nghiệm
- [Key takeaway 1]
- [Key takeaway 2]
- [Key takeaway 3]

---

## 6. TÀI LIỆU THAM KHẢO

1. Course materials - Lab 02 specification
2. Python regex documentation
3. Scikit-learn documentation
4. [Any other references used]

---

## PHỤ LỤC

### A. Cấu trúc thư mục output

```
23127332/
├── 2310-15395/
│   ├── metadata.json
│   ├── references.json
│   ├── refs.bib
│   ├── hierarchy.json
│   └── pred.json
├── 2310-15396/
│   └── ...
```

### B. Sample hierarchy.json

```json
{
  "elements": {
    "2310-15395-v1-section-1": "Introduction",
    "2310-15395-v1-paragraph-1": "",
    "2310-15395-v1-sentence-1": "Dark matter is a mystery.",
    ...
  },
  "hierarchy": {
    "1": {
      "2310-15395-v1-sentence-1": "2310-15395-v1-paragraph-1",
      "2310-15395-v1-paragraph-1": "2310-15395-v1-section-1",
      ...
    }
  }
}
```

### C. Sample pred.json

```json
{
  "partition": "test",
  "groundtruth": {
    "Krnjaic:2023odw": "2307.00041",
    "Caputo:2020msf": "2012.09179"
  },
  "prediction": {
    "Krnjaic:2023odw": ["2307.00041", "2306.12345", ...],
    "Caputo:2020msf": ["2012.09179", "2011.54321", ...]
  }
}
```

---

**Ngày hoàn thành:** [Date]  
**Video Demo:** [YouTube link]
