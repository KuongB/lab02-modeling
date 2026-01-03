# HƯỚNG DẪN SỬ DỤNG NHANH - LAB 02

## 📌 Tổng quan

Pipeline đã sẵn sàng sử dụng! Tất cả tests đã pass. Dưới đây là hướng dẫn từng bước.

## ✅ Đã hoàn thành

- [x] LaTeX Parser (multi-file gathering)
- [x] Hierarchy Builder (tree structure)
- [x] LaTeX Cleaner (standardization)
- [x] BibTeX Processor (extraction & deduplication)
- [x] ML Feature Extraction
- [x] Reference Matching Model
- [x] Test suite (4/4 tests passed ✅)

## 📋 Bước tiếp theo

### BƯỚC 1: Chạy Pipeline xử lý dữ liệu

```powershell
cd Source
python main.py
```

**Output**: Xử lý tất cả publications trong `sample/` và tạo files output trong `<MSSV>/`

**Files được tạo cho mỗi publication:**
- ✓ `metadata.json` (copied)
- ✓ `references.json` (copied)
- ✓ `refs.bib` (deduplicated BibTeX)
- ✓ `hierarchy.json` (tree structure)
- ⏳ `pred.json` (sẽ tạo sau khi train ML)

### BƯỚC 2: Manual Labeling (CẦN LÀM THỦ CÔNG)

**Yêu cầu:**
- Gán nhãn cho **ít nhất 5 publications**
- Tổng cộng **ít nhất 20 cặp** (bib_key, arxiv_id)

**Cách làm:**

1. Chọn 5 publications từ output directory
2. Mở `refs.bib` và `references.json` của mỗi publication
3. Matching các BibTeX entries với arXiv IDs
4. Tạo file `manual_labels.json`:

```json
{
  "2310-15395": {
    "Krnjaic:2023odw": "2307.00041",
    "Caputo:2020msf": "2012.09179",
    "Boddy:2022knd": "2207.XXXXX"
  },
  "2310-15396": {
    "Smith:2020": "2301.XXXXX",
    ...
  }
}
```

**Tips để matching:**
- Tìm arXiv ID trong BibTeX entry (field `eprint`)
- So khớp title giữa BibTeX và references.json
- So khớp authors và year
- Dùng Google Scholar để xác nhận

### BƯỚC 3: Auto Labeling & Data Splitting

Sau khi có `manual_labels.json`, chạy script auto labeling:

```python
# Tạo file auto_label.py trong Source/
from reference_matching import ReferenceMatchingModel
from pathlib import Path
import json

# Load manual labels
with open('manual_labels.json') as f:
    manual_labels = json.load(f)

# TODO: Implement auto labeling using heuristics
# - Regex để tìm arXiv ID trong BibTeX
# - Title similarity > 0.9
# - Author overlap > 0.5

# TODO: Split data
# - 5 pubs manual → 1 test, 1 valid, 3 train
# - Remaining pubs → split by ratio
```

### BƯỚC 4: Train ML Model

```python
# train_model.py
from reference_matching import ReferenceMatchingModel, compute_mrr
import json

# Load training data
# ... (load BibTeX entries and references)

# Create feature vectors
model = ReferenceMatchingModel()
X_train, y_train = model.create_training_data(training_examples)

# Train
model.train(X_train, y_train)

# Save model
import pickle
with open('trained_model.pkl', 'wb') as f:
    pickle.dump(model, f)
```

### BƯỚC 5: Generate Predictions

```python
# predict.py
from reference_matching import ReferenceMatchingModel
import pickle
import json

# Load model
with open('trained_model.pkl', 'rb') as f:
    model = pickle.load(f)

# For each test publication
for pub_id in test_pubs:
    # Load refs.bib and references.json
    # ...
    
    predictions = {}
    for bib_key, bib_entry in bib_entries.items():
        # Get top-5 candidates
        top5 = model.rank_candidates(bib_entry, references, top_k=5)
        predictions[bib_key] = [arxiv_id for arxiv_id, score in top5]
    
    # Save pred.json
    pred_data = {
        "partition": "test",  # or "train", "valid"
        "groundtruth": groundtruth_dict,
        "prediction": predictions
    }
    
    with open(f'{pub_id}/pred.json', 'w') as f:
        json.dump(pred_data, f, indent=2)
```

### BƯỚC 6: Evaluate MRR

```python
from reference_matching import compute_mrr

# Load test predictions
mrr_scores = []
for pub_id in test_pubs:
    with open(f'{pub_id}/pred.json') as f:
        data = json.load(f)
    
    mrr = compute_mrr(data['prediction'], data['groundtruth'])
    mrr_scores.append(mrr)

average_mrr = sum(mrr_scores) / len(mrr_scores)
print(f"Test MRR: {average_mrr:.4f}")
```

### BƯỚC 7: Viết Báo cáo

Dùng template `REPORT_TEMPLATE.md` và điền:

1. **Thống kê xử lý dữ liệu**
   - Số publications, versions, elements
   - Tỷ lệ deduplication
   
2. **Feature engineering**
   - Giải thích từng feature
   - Feature importance từ model
   
3. **ML Results**
   - MRR scores (train, valid, test)
   - Error analysis
   - Example predictions

4. **Screenshots**
   - Hierarchy structure
   - Feature distributions
   - Confusion matrix (nếu có)

### BƯỚC 8: Tạo Video Demo (240-300s)

**Nội dung video:**
1. Giới thiệu project (30s)
2. Chạy pipeline (60s)
3. Giải thích hierarchy.json (60s)
4. Giải thích ML pipeline (60s)
5. Kết quả và MRR (30s)

## 🔧 Troubleshooting

### Lỗi: "No main file found"

**Nguyên nhân**: Folder không có file .tex với `\begin{document}`
**Giải pháp**: Kiểm tra lại folder structure

### Lỗi: "Unicode decode error"

**Nguyên nhân**: File có encoding đặc biệt
**Giải pháp**: Đã xử lý tự động với multiple encodings

### Lỗi: "Model not trained"

**Nguyên nhân**: Chưa có training data
**Giải pháp**: Sử dụng heuristic scoring thay vì ML model

## 📊 Kiểm tra kết quả

```python
# Verify output
from pathlib import Path
import json

output_dir = Path('../<MSSV>')

for pub_dir in output_dir.iterdir():
    if not pub_dir.is_dir():
        continue
    
    print(f"\nPublication: {pub_dir.name}")
    
    # Check required files
    for filename in ['metadata.json', 'references.json', 'refs.bib', 'hierarchy.json']:
        filepath = pub_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
            if filename == 'hierarchy.json':
                data = json.load(open(filepath))
                print(f"    Elements: {len(data['elements'])}")
                print(f"    Versions: {len(data['hierarchy'])}")
        else:
            print(f"  ✗ {filename} MISSING")
```

## 📦 Chuẩn bị nộp bài

1. **Cấu trúc folder:**
```
<MSSV>.zip
├── src/
│   ├── *.py (all Python files)
│   └── requirements.txt
├── <MSSV>/
│   ├── 2310-15395/
│   │   ├── metadata.json
│   │   ├── references.json
│   │   ├── refs.bib
│   │   ├── hierarchy.json
│   │   └── pred.json (if in train/valid/test)
│   └── ...
├── README.md
├── Report.pdf
└── [Link to video demo]
```

2. **Checklist trước khi nộp:**
   - [ ] Tất cả publications đã xử lý
   - [ ] Manual labels cho ≥5 pubs, ≥20 pairs
   - [ ] Auto labels cho ≥10% remaining
   - [ ] pred.json cho train/valid/test pubs
   - [ ] MRR scores được tính
   - [ ] Report hoàn chỉnh với figures
   - [ ] Video demo uploaded
   - [ ] README.md có hướng dẫn chạy

## 💡 Tips quan trọng

1. **Backup thường xuyên**: Dữ liệu xử lý mất nhiều thời gian
2. **Version control**: Dùng git để track changes
3. **Test từng bước**: Không chạy toàn bộ pipeline một lúc
4. **Log errors**: Ghi lại các publications failed để debug
5. **Validate output**: Kiểm tra format JSON trước khi nộp

## 🎯 Mục tiêu cuối cùng

- [ ] Process all publications successfully
- [ ] MRR score > 0.5 (good target)
- [ ] Complete report with analysis
- [ ] Clear video demonstration
- [ ] Well-documented code

## 📞 Liên hệ

Nếu có vấn đề với code, check:
1. README.md trong Source/
2. Test output từ test_pipeline.py
3. Error messages trong console

Good luck! 🚀
