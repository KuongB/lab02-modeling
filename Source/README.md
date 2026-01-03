# Lab 02 - Modeling: Hierarchical Parsing & Reference Matching

## Mô tả dự án

Pipeline xử lý dữ liệu LaTeX và matching tài liệu tham khảo cho bài tập Lab 02 - Môn Nhập môn Khoa học Dữ liệu.

### Chức năng chính:

1. **Phần 1: Hierarchical Parsing & Standardization**
   - Thu thập và hợp nhất các file LaTeX (multi-file gathering)
   - Xây dựng cấu trúc phân cấp (hierarchy tree)
   - Chuẩn hóa LaTeX content
   - Trích xuất và khử trùng BibTeX references

2. **Phần 2: Reference Matching Pipeline**
   - Feature engineering cho matching
   - Machine Learning model training
   - Đánh giá bằng MRR (Mean Reciprocal Rank)

## Cấu trúc thư mục

```
Source/
├── config.py                 # Configuration settings
├── utils.py                  # Utility functions
├── latex_parser.py           # LaTeX file parsing
├── latex_cleaner.py          # LaTeX content cleaning
├── hierarchy_builder.py      # Hierarchy construction
├── bibtex_processor.py       # BibTeX processing & deduplication
├── reference_matching.py     # ML reference matching
├── main.py                   # Main pipeline
├── requirements.txt          # Python dependencies
└── README.md                 # This file

<MSSV>/                       # Output directory
├── 2310-15395/
│   ├── metadata.json
│   ├── references.json
│   ├── refs.bib
│   ├── hierarchy.json
│   └── pred.json (for train/valid/test pubs)
├── 2310-15396/
│   └── ...
```

## Cài đặt

### 1. Cài đặt Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Tải dữ liệu NLTK (cho text processing):

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

## Sử dụng

### Bước 1: Xử lý tất cả publications

```bash
python main.py
```

Script này sẽ:
- Đọc tất cả publications từ thư mục `sample/`
- Parse LaTeX files từ tất cả versions
- Xây dựng hierarchy tree với deduplication
- Trích xuất và merge BibTeX references
- Tạo output files trong thư mục `<MSSV>/`

### Bước 2: Gán nhãn thủ công (Manual Labeling)

Tạo file `manual_labels.json` với format:

```json
{
  "2310-15395": {
    "Boddy:2022knd": "2207.12409",
    "Krnjaic:2023odw": "2307.00041",
    ...
  },
  "2310-15396": {
    ...
  }
}
```

**Yêu cầu:**
- Ít nhất 5 publications
- Tổng cộng ít nhất 20 cặp (bib_key, arxiv_id)

### Bước 3: Train ML Model

```python
from main import Pipeline

pipeline = Pipeline(SAMPLE_DIR, OUTPUT_DIR)
pipeline.train_and_evaluate_ml_model()
```

### Bước 4: Generate predictions

Sau khi train model, predictions sẽ được lưu vào `pred.json` cho mỗi publication.

## Format Output Files

### 1. `hierarchy.json`

```json
{
  "elements": {
    "element-id": "content or title",
    ...
  },
  "hierarchy": {
    "1": {
      "child-id": "parent-id",
      ...
    },
    "2": {
      ...
    }
  }
}
```

### 2. `refs.bib`

Standard BibTeX format với entries đã deduplicated.

### 3. `pred.json`

```json
{
  "partition": "train|valid|test",
  "groundtruth": {
    "bib_key": "arxiv_id",
    ...
  },
  "prediction": {
    "bib_key": ["cand1", "cand2", "cand3", "cand4", "cand5"],
    ...
  }
}
```

## Các quyết định thiết kế

### 1. Multi-file Gathering

- Tìm file chứa `\begin{document}` làm main file
- Nếu có nhiều files, ưu tiên `main.tex` hoặc file lớn nhất
- Recursively parse tất cả `\input{}` và `\include{}`

### 2. Hierarchy Construction

- **Document** là root node
- **Sections** (chapter, section, subsection, ...) tạo hierarchy levels
- **Smallest elements**: Sentences, Equations, Figures/Tables, List Items
- **Lists**: `\begin{itemize}` là higher component, mỗi `\item` là next level
- **Exclusions**: References section
- **Inclusions**: Acknowledgements, Appendices (kể cả unnumbered)

### 3. Content Deduplication

- Sử dụng SHA256 hash của normalized content
- Nếu content match giữa versions → reuse same element ID
- Structural nodes (sections, paragraphs) giữ riêng nếu titles khác

### 4. BibTeX Processing

- Ưu tiên `.bib` files, fallback sang `.bbl` files
- Deduplicate based on content similarity (title, author, year)
- Merge fields từ duplicate entries (union)

### 5. ML Feature Engineering

Features sử dụng:
1. Title token overlap (Jaccard similarity)
2. Title Levenshtein distance  
3. Title length ratio
4. Author similarity (exact + partial matching)
5. Author count difference
6. Year similarity
7. arXiv ID presence in BibTeX

Model: Random Forest Classifier

## Xử lý các trường hợp đặc biệt

### Case 1: Nhiều files có `\begin{document}`

**Giải pháp**: Chọn `main.tex` nếu có, nếu không chọn file lớn nhất.
**Log**: Ghi lại trong report file nào được chọn.

### Case 2: Không có file `.bib`

**Giải pháp**: Parse `.bbl` file và convert về BibTeX format.
**Hạn chế**: Một số metadata có thể bị mất trong `.bbl`.

### Case 3: Duplicate references với keys khác nhau

**Giải pháp**: Deduplicate dựa trên content matching, giữ một key canonical, map các keys khác về key canonical.

### Case 4: Sections có cùng children nhưng titles khác

**Giải pháp**: Giữ riêng biệt (không merge) theo instructor guidance.

## Evaluation Metrics

### Mean Reciprocal Rank (MRR)

$$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{rank_i}$$

Trong đó:
- $rank_i$ là vị trí của kết quả đúng trong top-5 predictions
- Nếu không nằm trong top-5, score = 0

## Testing

Chạy test trên một publication:

```python
from main import Pipeline

pipeline = Pipeline(SAMPLE_DIR, OUTPUT_DIR)
success = pipeline.process_publication('2310-15395')
print(f"Success: {success}")
```

## Troubleshooting

### Lỗi Unicode Decode

File LaTeX có encoding khác nhau. Pipeline tự động thử nhiều encodings:
- UTF-8
- Latin-1
- ISO-8859-1
- CP1252

### Lỗi Parse LaTeX

Một số constructs LaTeX phức tạp có thể không được parse đúng. Kiểm tra:
- Nested environments
- Unclosed braces
- Custom commands

## TODO

- [ ] Implement auto-labeling với regex và string matching
- [ ] Implement data splitting (train/valid/test)
- [ ] Train và evaluate ML model
- [ ] Generate `pred.json` files
- [ ] Compute final MRR scores
- [ ] Write detailed report

## Tác giả

- MSSV: 23127332
- Lớp: Nhập môn Khoa học Dữ liệu

## License

Academic use only - Lab 02 Assignment
