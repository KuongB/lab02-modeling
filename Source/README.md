# Lab 02 - Data Modeling Pipeline

Pipeline xử lý và phân tích dữ liệu LaTeX, thực hiện reference matching với Machine Learning.

## 📁 Cấu Trúc

```
Source/
├── main.py                      # ⭐ Main pipeline (interactive)
├── manual_labeling_helper.py   # 🏷️  Manual labeling tool
│
├── latex_parser.py              # Parse LaTeX
├── latex_cleaner.py             # Clean content
├── hierarchy_builder.py         # Build hierarchy
├── bibtex_processor.py          # Process BibTeX
├── auto_labeling.py             # Auto-labeling
├── reference_matching.py        # ML features
├── ml_pipeline.py               # ML training
│
├── config.py                    # Configuration
└── utils.py                     # Utilities
```

## 🚀 Cách Sử Dụng

### Interactive Menu (Khuyến nghị)

```bash
python main.py
```

Hiển thị menu:
```
1. Process publications
2. Auto-labeling  
3. Manual labeling
4. Train ML model
5. Run full pipeline
6. Show status
0. Exit
```

### Command Line

```bash
python main.py --process        # Xử lý publications
python main.py --auto-label     # Auto-labeling
python main.py --train          # Train model
python main.py --full           # Full pipeline
python main.py --status         # Show status
```

## 📋 Workflow

### 1. Process Publications
```bash
python main.py --process
```
→ Parse LaTeX → Build hierarchy → Extract BibTeX

### 2. Manual Labeling
```bash
python manual_labeling_helper.py
```
→ Label BibTeX → arXiv ID (≥5 pubs, ≥20 pairs)

### 3. Auto-Labeling
```bash
python main.py --auto-label
```
→ Tự động label ~10% data

### 4. Train Model
```bash
python main.py --train
```
→ Train Random Forest → Generate predictions → Compute MRR

## 📊 Output Files

**hierarchy.json** - Cấu trúc phân cấp
**refs.bib** - BibTeX entries
**pred.json** - ML predictions (top-5)

## ✅ Quick Check

```bash
python main.py --status
```

Hiển thị:
- Số publications đã xử lý
- Số labels (manual + auto)
- MRR scores (train/valid/test)
- Next steps

## 🔧 Commands

```bash
# Process specific publication
python main.py --pub-id 2310-15395

# Auto-label 5 publications
python main.py --auto-label --num-auto 5

# Full pipeline
python main.py --full
```

## 📝 Requirements

```bash
pip install -r requirements.txt
```

---

**Lab 02 - NM-KHDL**
