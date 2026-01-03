# 📋 FINAL CHECKLIST - LAB 02

## ✅ ĐÃ HOÀN THÀNH

### Infrastructure & Code
- [x] Config module với tất cả settings
- [x] Utility functions (normalize, hash, file I/O)
- [x] LaTeX parser với multi-file gathering
- [x] LaTeX cleaner và standardization
- [x] Hierarchy builder với deduplication
- [x] BibTeX processor (.bib và .bbl)
- [x] ML feature extraction (7 features)
- [x] Reference matching model (Random Forest)
- [x] Main pipeline orchestration
- [x] Test suite (4/4 passed ✅)
- [x] Manual labeling helper tool
- [x] README.md documentation
- [x] GUIDE.md với step-by-step instructions
- [x] REPORT_TEMPLATE.md
- [x] PROJECT_SUMMARY.md

### Testing
- [x] LaTeX Parser test
- [x] LaTeX Cleaner test  
- [x] Hierarchy Builder test
- [x] BibTeX Processor test
- [x] Python environment setup
- [x] Dependencies installed

## ⏳ CẦN LÀM (Theo thứ tự)

### Phase 1: Xử lý dữ liệu
- [ ] **Chạy main pipeline**
  ```bash
  cd Source
  python main.py
  ```
  - Xử lý tất cả publications trong sample/
  - Tạo hierarchy.json và refs.bib cho mỗi publication
  - Ước tính: ~15-20 phút cho tất cả publications

### Phase 2: Manual Labeling  
- [ ] **Gán nhãn thủ công (YÊU CẦU BẮT BUỘC)**
  ```bash
  python manual_labeling_helper.py
  ```
  - Chọn 5 publications để label
  - Tổng cộng ≥20 cặp (bib_key, arxiv_id)
  - Tool sẽ suggest matches tự động
  - Lưu vào manual_labels.json
  - Ước tính: ~2-3 giờ

- [ ] **Kiểm tra requirements**
  - Đủ 5 publications? ✓
  - Đủ 20 pairs? ✓

### Phase 3: Auto Labeling
- [ ] **Viết script auto labeling** (tạo file `auto_label.py`)
  ```python
  # Heuristics:
  # 1. Tìm arXiv ID trong BibTeX (eprint field)
  # 2. Title similarity > 0.9
  # 3. Author overlap + year match
  ```
  - Label thêm ≥10% remaining publications
  - Merge với manual labels
  - Ước tính: ~1-2 giờ

### Phase 4: ML Training
- [ ] **Chia data thành train/valid/test**
  - Test: 1 publication manual + 1 auto
  - Valid: 1 publication manual + 1 auto  
  - Train: Phần còn lại
  
- [ ] **Train model** (tạo file `train_model.py`)
  ```python
  from reference_matching import ReferenceMatchingModel
  
  # Load data
  # Create features
  # Train
  # Save model
  ```
  - Ước tính: ~1 giờ

- [ ] **Generate predictions** (tạo file `generate_predictions.py`)
  ```python
  # For each pub in train/valid/test:
  #   - Load model
  #   - Predict top-5
  #   - Save pred.json
  ```
  - Tạo pred.json cho tất cả train/valid/test pubs
  - Ước tính: ~1 giờ

- [ ] **Evaluate MRR**
  ```python
  from reference_matching import compute_mrr
  
  # Compute MRR for test set
  # Compute MRR for validation set
  ```
  - Ghi lại scores
  - Ước tính: ~30 phút

### Phase 5: Report
- [ ] **Viết báo cáo chi tiết** (dùng REPORT_TEMPLATE.md)
  
  **Section 1: Tổng quan hệ thống** (~30 phút)
  - [ ] Kiến trúc tổng thể
  - [ ] Mục tiêu và phương pháp
  
  **Section 2: Hierarchical Parsing** (~1 giờ)
  - [ ] Multi-file gathering explanation
  - [ ] Hierarchy construction details
  - [ ] Standardization & cleaning
  - [ ] Deduplication results
  - [ ] Thống kê (số elements, dedup rate, etc.)
  
  **Section 3: BibTeX Processing** (~30 phút)
  - [ ] .bib vs .bbl handling
  - [ ] Deduplication algorithm
  - [ ] Merge strategy
  - [ ] Thống kê (entries before/after)
  
  **Section 4: ML Pipeline** (~2 giờ)
  - [ ] Feature engineering với rationale
  - [ ] Feature importance analysis
  - [ ] Model training details
  - [ ] MRR results (train/valid/test)
  - [ ] Error analysis với examples
  
  **Section 5: Results** (~30 phút)
  - [ ] Overall statistics
  - [ ] Processing time
  - [ ] Challenges & solutions
  
  **Section 6: Conclusion** (~30 phút)
  - [ ] Achievements
  - [ ] Limitations
  - [ ] Future improvements
  
  **Figures & Tables** (~1 giờ)
  - [ ] Hierarchy example diagram
  - [ ] Feature distribution plots
  - [ ] Feature importance chart
  - [ ] MRR breakdown table
  - [ ] Example predictions
  
  **Total ước tính báo cáo: ~6 giờ**

### Phase 6: Video Demo
- [ ] **Chuẩn bị script** (~30 phút)
  - Giới thiệu (30s)
  - Demo pipeline (60s)
  - Giải thích hierarchy (60s)
  - Giải thích ML (60s)
  - Kết quả (30s)
  
- [ ] **Quay video** (~1 giờ)
  - Screen recording
  - Voice-over
  - 240-300 seconds total
  
- [ ] **Edit & upload** (~30 phút)
  - Cắt ghép
  - Add transitions
  - Upload to YouTube
  - Set public/unlisted
  
  **Total ước tính video: ~2 giờ**

### Phase 7: Submission
- [ ] **Tạo cấu trúc nộp bài**
  ```
  23127332.zip
  ├── src/
  │   ├── *.py
  │   └── requirements.txt
  ├── 23127332/
  │   ├── 2310-15395/
  │   │   ├── metadata.json
  │   │   ├── references.json
  │   │   ├── refs.bib
  │   │   ├── hierarchy.json
  │   │   └── pred.json
  │   └── ...
  ├── README.md
  └── Report.pdf
  ```

- [ ] **Kiểm tra files**
  - [ ] Tất cả .py files có trong src/
  - [ ] requirements.txt đầy đủ
  - [ ] Tất cả publications có metadata.json, references.json
  - [ ] Tất cả publications có refs.bib
  - [ ] Tất cả publications có hierarchy.json
  - [ ] Train/valid/test publications có pred.json
  - [ ] README.md có hướng dẫn chạy rõ ràng
  - [ ] Report.pdf hoàn chỉnh với figures
  
- [ ] **Validate format**
  - [ ] JSON files validate được (không có syntax error)
  - [ ] hierarchy.json đúng format spec
  - [ ] pred.json đúng format spec
  - [ ] refs.bib đúng BibTeX syntax
  
- [ ] **Test lại toàn bộ**
  - [ ] Giải nén ZIP
  - [ ] Đọc README
  - [ ] Cài dependencies: `pip install -r requirements.txt`
  - [ ] Chạy một publication test
  
- [ ] **Upload video**
  - [ ] Upload lên YouTube
  - [ ] Copy link vào Report
  - [ ] Test link hoạt động
  
- [ ] **Final submission**
  - [ ] Nộp ZIP file
  - [ ] Nộp video link
  - [ ] Confirm submission thành công

## 📊 Progress Tracking

### Overall Completion: ~60%
- ✅ Infrastructure: 100%
- ⏳ Data Processing: 0% (chưa chạy full pipeline)
- ⏳ Manual Labeling: 0%
- ⏳ Auto Labeling: 0%
- ⏳ ML Training: 0%
- ⏳ Report: 0%
- ⏳ Video: 0%

### Estimated Time Remaining
| Phase | Time |
|-------|------|
| Data Processing | 30 min |
| Manual Labeling | 3 hours |
| Auto Labeling | 2 hours |
| ML Training & Eval | 3 hours |
| Report Writing | 6 hours |
| Video Creation | 2 hours |
| Submission Prep | 1 hour |
| **TOTAL** | **~17 hours** |

## 🎯 Quality Checklist

### Code Quality
- [x] Follows PEP 8 style
- [x] Well-documented (docstrings)
- [x] Modular design
- [x] Error handling
- [x] All tests pass

### Data Quality
- [ ] All publications processed successfully
- [ ] No missing required files
- [ ] JSON files are valid
- [ ] BibTeX syntax correct
- [ ] Hierarchy makes sense

### ML Quality
- [ ] Features well-justified
- [ ] Model trained successfully
- [ ] MRR > 0.3 (minimum acceptable)
- [ ] MRR > 0.5 (good target)
- [ ] Error analysis done

### Documentation Quality
- [ ] README clear and complete
- [ ] Report well-structured
- [ ] Figures informative
- [ ] Analysis insightful
- [ ] Video clear and engaging

## 🚨 Common Pitfalls to Avoid

- ❌ **Không backup dữ liệu**: Backup thường xuyên!
- ❌ **Gán nhãn sai**: Double-check manual labels
- ❌ **JSON syntax errors**: Validate JSON files
- ❌ **Quên pred.json**: Chỉ train/valid/test cần pred.json
- ❌ **MRR = 0**: Kiểm tra lại feature engineering
- ❌ **Report thiếu analysis**: Cần explain, không chỉ numbers
- ❌ **Video quá dài/ngắn**: 240-300s exactly
- ❌ **Link video private**: Set unlisted hoặc public

## 💪 Motivation

Bạn đã hoàn thành **60% công việc**!

Phần khó nhất (xây dựng infrastructure) đã xong. 
Phần còn lại là execution và documentation.

**Bạn có thể làm được! 🚀**

---

**Last Updated**: [Current Date]
**Status**: Infrastructure Complete, Ready for Data Processing
