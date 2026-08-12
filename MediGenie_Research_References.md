# MediGenie — Research Paper Reference Guide

This maps every dataset, algorithm, evaluation metric, and architectural choice in the MediGenie project to the actual academic source that supports it — verified via live web search, not recalled from memory. Use this to write your Related Work / Methodology / References sections. Every entry below is a real, checkable publication.

---

## 1. Datasets (Section: Related Work / Dataset Description)

Each of your 9 disease models is built on a named, citable public dataset. Cite the *creators*, not just "UCI" or "Kaggle."

### 1.1 Heart Disease (Cleveland)
- **Citation:** Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989). *Heart Disease* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X
- **Companion clinical paper:** Detrano, R., Janosi, A., Steinbrunn, W., Pfisterer, M., Schmid, J., Sandhu, S., Guppy, K., Lee, S., & Froelicher, V. (1989). International application of a new probability algorithm for the diagnosis of coronary artery disease. *American Journal of Cardiology*, 64(5), 304–310.
- **Use in paper:** Cite when describing the source and clinical provenance of your 13-feature, 303-sample heart disease dataset (age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal).

### 1.2 Diabetes 130-US Hospitals
- **Citation:** Strack, B., DeShazo, J. P., Gennings, C., Olmo Ortiz, J. L., Ventura, S., Cios, K. J., & Clore, J. N. (2014). Impact of HbA1c measurement on hospital readmission rates: analysis of 70,000 clinical database patient records. *BioMed Research International*, 2014, Article 781670.
- **Dataset record:** Strack, B., et al. (2014). *Diabetes 130-US Hospitals for Years 1999–2008* [Dataset]. UCI Machine Learning Repository.
- **Use in paper:** Cite for the 101,766-record, 9-feature readmission-risk dataset. Note in your limitations/discussion that this is an *administrative encounter-level* dataset (not lab-value-driven), which is the actual reason your Diabetes model tops out around ROC-AUC 0.65 — this is a defensible, citable point, not a modeling weakness.

### 1.3 Chronic Kidney Disease
- **Citation:** Rubini, L., Soundarapandian, P., & Eswaran, P. (2015). *Chronic Kidney Disease* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5G020
- **Use in paper:** 400-sample, 24-feature dataset collected over ~2 months at a hospital in Tamil Nadu, India. Good citation if you discuss missing-value imputation, since this dataset is well known for heavy missingness.

### 1.4 Indian Liver Patient Dataset (ILPD)
- **Citation:** Ramana, B. V., & Venkateswarlu, N. B. (2012). *ILPD (Indian Liver Patient Dataset)* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5D02C
- **Companion paper:** Ramana, B. V., Prasad Babu, M. S., & Venkateswarlu, N. B. (2012). A critical comparative study of liver patients from USA and India: an exploratory analysis. *International Journal of Computer Science Issues*, 9(3).
- **Use in paper:** 583-sample, 10-feature dataset from Andhra Pradesh, India. If you discuss fairness/bias, there is directly relevant literature (Straw & Wu, 2022, on sex-stratified bias in this exact dataset) you can cite as related work.

### 1.5 Breast Cancer Wisconsin (Diagnostic)
- **Citation:** Wolberg, W. H., Mangasarian, O. L., Street, N., & Street, W. N. (1995). *Breast Cancer Wisconsin (Diagnostic)* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5DW2B
- **Companion papers:**
  - Street, W. N., Wolberg, W. H., & Mangasarian, O. L. (1993). Nuclear feature extraction for breast tumor diagnosis. *IS&T/SPIE International Symposium on Electronic Imaging*, 1905, 861–870.
  - Wolberg, W. H., Street, W. N., & Mangasarian, O. L. (1994). Machine learning techniques to diagnose breast cancer from image-processed nuclear features of fine-needle aspirates. *Cancer Letters*, 77(2–3), 163–171.
- **Use in paper:** 569-sample, 30-feature dataset (10 measurements × mean/SE/worst). This is the single best-performing model in your report (Acc 0.977, ROC-AUC 0.999) — strong candidate for a "why this dataset generalizes so well" discussion citing the feature-engineering rigor in the original Street et al. paper.

### 1.6 Parkinson's Disease (voice measurements)
- **Citation:** Little, M. A., McSharry, P. E., Roberts, S. J., Costello, D. A. E., & Moroz, I. M. (2007). Exploiting nonlinear recurrence and fractal scaling properties for voice disorder detection. *BioMedical Engineering OnLine*, 6, 23.
- **Dataset record:** Little, M. (2007). *Parkinsons* [Dataset]. UCI Machine Learning Repository.
- **Use in paper:** 195-sample, 22-feature voice-measurement dataset from 31 subjects. Cite this paper specifically (not the later 2009 telemonitoring dataset, which is a different, larger, regression-oriented dataset — don't conflate the two).

### 1.7 Hepatitis
- **Citation:** Gong, G. (1988). *Hepatitis Domain* [Dataset]. UCI Machine Learning Repository. Donated by Gail Gong, Carnegie Mellon University.
- **Use in paper:** 155-sample, 19-feature dataset, "die"/"live" outcome. Note for your paper: this is one of your smallest and most class-imbalanced test sets (24 test samples, only 5 positive) — cite this dataset's known small-N status if you discuss confidence-interval width.

### 1.8 Heart Failure Clinical Records
- **Citation:** Chicco, D., & Jurman, G. (2020). Machine learning can predict survival of patients with heart failure from serum creatinine and ejection fraction alone. *BMC Medical Informatics and Decision Making*, 20, 16. https://doi.org/10.1186/s12911-020-1023-5
- **Use in paper:** 299-sample, 12-feature dataset from the Faisalabad Institute of Cardiology (2015). This is a strong, highly-citable companion paper — it's not just a dataset dump, it's a full study with its own ML findings you can directly compare your results against.

### 1.9 Stroke Prediction Dataset
- **Citation:** fedesoriano. (2021). *Stroke Prediction Dataset* [Dataset]. Kaggle. https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset
- **Use in paper:** 5,110-sample, 10-feature dataset. Note: this is a Kaggle-only release (no peer-reviewed companion paper), so cite it as a dataset source, not a research finding. Multiple published papers using this exact dataset exist if you want secondary support (e.g., stroke prediction survey/hybrid-system papers found in this session — see §4 below for the SMOTE angle, which is directly relevant to this dataset's 4.9% positive rate).

---

## 2. Algorithms used (Section: Methodology)

Your pipeline selects the best of up to four algorithms per disease by validation-set PR-AUC. Cite the original method paper for each one you actually used (check Section 10 of your report for which algorithm won each disease).

| Algorithm | Citation |
|---|---|
| **Random Forest** | Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324 |
| **Logistic Regression** | Standard statistical method — if you want a citable ML-context reference: Hosmer, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). *Applied Logistic Regression* (3rd ed.). John Wiley & Sons. |
| **Support Vector Machine (SVM)** | Cortes, C., & Vapnik, V. (1995). Support-vector networks. *Machine Learning*, 20(3), 273–297. https://doi.org/10.1007/BF00994018 |
| **XGBoost** | Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD '16)*, 785–794. https://doi.org/10.1145/2939672.2939785 |

**Which algorithm won which disease** (from your verified Section 10 results — cite the matching method paper when you discuss that disease):
- Heart Disease → SVM · Diabetes → Logistic Regression · Kidney Disease → Random Forest
- Liver Disease → XGBoost · Breast Cancer → SVM · Parkinson's → XGBoost
- Hepatitis → Logistic Regression · Heart Failure → SVM · Stroke → Logistic Regression

---

## 3. Explainability (Section: Methodology — Interpretability)

Your `requirements.txt` includes SHAP. If your paper discusses model interpretability at all:

- **Citation:** Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems (NeurIPS)*, 30, 4765–4774.
- **Use in paper:** This is the SHAP (SHapley Additive exPlanations) paper — cite it wherever you mention per-feature contribution/explainability output for any of the 9 models.

---

## 4. Class imbalance handling (Section: Methodology — Stroke model)

Your Stroke dataset has severe imbalance (37 positive / 5,110 total, ≈4.9%), which directly explains its low precision (0.0997) in your results.

- **Citation:** Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: Synthetic minority over-sampling technique. *Journal of Artificial Intelligence Research*, 16, 321–357. https://doi.org/10.1613/jair.953
- **Use in paper:** Cite this when explaining your imbalance-handling strategy and, honestly, when explaining *why* stroke precision is low despite high recall — this is a known, published, expected trade-off of oversampling-based approaches on severely imbalanced clinical data, not a flaw unique to your pipeline.

---

## 5. Evaluation metrics (Section: Methodology — Evaluation Protocol)

Your `master_metrics.json` reports Accuracy, Precision, Recall, Specificity, F1, ROC-AUC, PR-AUC, MCC, Cohen's κ, and Brier score. Each of the non-obvious ones has a specific citable origin:

| Metric | Citation |
|---|---|
| **Matthews Correlation Coefficient (MCC)** | Matthews, B. W. (1975). Comparison of the predicted and observed secondary structure of T4 phage lysozyme. *Biochimica et Biophysica Acta (BBA) — Protein Structure*, 405(2), 442–451. |
| **Why MCC over accuracy/F1 (justify using it)** | Chicco, D., & Jurman, G. (2020). The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation. *BMC Genomics*, 21, 6. https://doi.org/10.1186/s12864-019-6413-7 |
| **Cohen's Kappa** | Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37–46. |

**Use in paper:** This pair (Matthews 1975 + Chicco & Jurman 2020) is a strong, standard citation combo for justifying why your evaluation reports MCC alongside accuracy — reviewers specifically like seeing this because accuracy alone is known to be misleading on your imbalanced datasets (Stroke, Hepatitis).

---

## 6. Multi-agent LLM architecture (Section: Related Work — System Architecture)

Your 8-agent LangGraph workflow (Supervisor, Intake, Report Analysis, Disease Risk, Medical Knowledge, Drug Safety, Recommendation, Report Generation) sits in an active, fast-moving research area. Use these for your Related Work section framing:

- Wang, W., Ma, Z., Wang, Z., et al. (2025). A survey of LLM-based agents in medicine: How far are we from Baymax? *arXiv:2502.11211*.
- OpenReview (2025). A survey of LLM-based multi-agent systems in medicine — proposes a taxonomy along team composition, medical knowledge augmentation, and agent interaction (directly maps onto how you'd describe your own 8-agent design).
- Ge, Z., Li, H., Wang, Y., Hu, N., Zhang, C. J., & Li, Q. (2026). ClinicalAgents: Multi-agent orchestration for clinical decision making with dual-memory. *Proceedings of the 32nd ACM SIGKDD Conference (KDD '26)*.
- Kim, Y., Park, C., Jeong, H., et al. (2024). MDAgents: An adaptive collaboration of LLMs for medical decision-making. *arXiv:2404.15155*.

**Use in paper:** These let you position MediGenie's Supervisor + specialist-agent design within the current "LLM-based multi-agent clinical decision support" literature rather than presenting it as an ad hoc engineering choice — this is exactly the kind of positioning a paper reviewer expects to see.

---

## 7. Retrieval-Augmented Generation / Guideline grounding (Section: Methodology — Medical Knowledge Agent)

Your Medical Knowledge agent queries a ChromaDB vector store for guideline evidence — this is RAG.

- **Citation:** Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems (NeurIPS)*, 33, 9459–9474.
- **Use in paper:** This is the foundational RAG paper — cite it wherever you describe the ChromaDB-backed guideline retrieval step, and frame it as grounding LLM output in retrieved evidence rather than relying purely on parametric memory (which directly supports your reduced-hallucination argument, if you make one).

---

## 8. Interoperability (Section: System Design — FHIR export)

Your `/fhir` endpoint exports HL7 FHIR-formatted reports.

- **Citation:** Bender, D., & Sartipi, K. (2013). HL7 FHIR: An agile and RESTful approach to healthcare information exchange. *Proceedings of the 26th IEEE International Symposium on Computer-Based Medical Systems (CBMS)*, 326–331. https://doi.org/10.1109/CBMS.2013.6627810
- **Use in paper:** Standard citation for any HL7 FHIR interoperability claim.

---

## 9. Quick citation list (BibTeX-ready skeleton)

Copy and fill into your reference manager:

```
@article{breiman2001random, author={Breiman, Leo}, title={Random Forests}, journal={Machine Learning}, volume={45}, number={1}, pages={5--32}, year={2001}, doi={10.1023/A:1010933404324}}

@inproceedings{chen2016xgboost, author={Chen, Tianqi and Guestrin, Carlos}, title={XGBoost: A Scalable Tree Boosting System}, booktitle={Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining}, pages={785--794}, year={2016}, doi={10.1145/2939672.2939785}}

@article{cortes1995support, author={Cortes, Corinna and Vapnik, Vladimir}, title={Support-Vector Networks}, journal={Machine Learning}, volume={20}, pages={273--297}, year={1995}, doi={10.1007/BF00994018}}

@article{chawla2002smote, author={Chawla, Nitesh V. and Bowyer, Kevin W. and Hall, Lawrence O. and Kegelmeyer, W. Philip}, title={SMOTE: Synthetic Minority Over-sampling Technique}, journal={Journal of Artificial Intelligence Research}, volume={16}, pages={321--357}, year={2002}, doi={10.1613/jair.953}}

@inproceedings{lundberg2017unified, author={Lundberg, Scott M. and Lee, Su-In}, title={A Unified Approach to Interpreting Model Predictions}, booktitle={Advances in Neural Information Processing Systems}, volume={30}, pages={4765--4774}, year={2017}}

@article{matthews1975comparison, author={Matthews, Brian W.}, title={Comparison of the Predicted and Observed Secondary Structure of T4 Phage Lysozyme}, journal={Biochimica et Biophysica Acta (BBA) - Protein Structure}, volume={405}, number={2}, pages={442--451}, year={1975}}

@article{chicco2020advantages, author={Chicco, Davide and Jurman, Giuseppe}, title={The Advantages of the Matthews Correlation Coefficient (MCC) over F1 Score and Accuracy in Binary Classification Evaluation}, journal={BMC Genomics}, volume={21}, pages={6}, year={2020}, doi={10.1186/s12864-019-6413-7}}

@article{cohen1960coefficient, author={Cohen, Jacob}, title={A Coefficient of Agreement for Nominal Scales}, journal={Educational and Psychological Measurement}, volume={20}, number={1}, pages={37--46}, year={1960}}

@inproceedings{lewis2020retrieval, author={Lewis, Patrick and Perez, Ethan and Piktus, Aleksandra and Petroni, Fabio and Karpukhin, Vladimir and Goyal, Naman and K{\"u}ttler, Heinrich and Lewis, Mike and Yih, Wen-tau and Rockt{\"a}schel, Tim and Riedel, Sebastian and Kiela, Douwe}, title={Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks}, booktitle={Advances in Neural Information Processing Systems}, volume={33}, pages={9459--9474}, year={2020}}

@inproceedings{bender2013fhir, author={Bender, Duane and Sartipi, Kamran}, title={HL7 FHIR: An Agile and RESTful Approach to Healthcare Information Exchange}, booktitle={Proceedings of the 26th IEEE International Symposium on Computer-Based Medical Systems}, pages={326--331}, year={2013}, doi={10.1109/CBMS.2013.6627810}}

@article{janosi1989heart, author={Janosi, Andras and Steinbrunn, William and Pfisterer, Matthias and Detrano, Robert}, title={Heart Disease}, journal={UCI Machine Learning Repository}, year={1989}, doi={10.24432/C52P4X}}

@article{strack2014impact, author={Strack, Beata and DeShazo, Jonathan P. and Gennings, Chris and Olmo Ortiz, Juan L. and Ventura, Sebastian and Cios, Krzysztof J. and Clore, John N.}, title={Impact of HbA1c Measurement on Hospital Readmission Rates: Analysis of 70,000 Clinical Database Patient Records}, journal={BioMed Research International}, volume={2014}, pages={781670}, year={2014}}

@article{rubini2015chronic, author={Rubini, L. and Soundarapandian, P. and Eswaran, P.}, title={Chronic Kidney Disease}, journal={UCI Machine Learning Repository}, year={2015}, doi={10.24432/C5G020}}

@article{ramana2012ilpd, author={Ramana, Bendi Venkata and Venkateswarlu, N. B.}, title={ILPD (Indian Liver Patient Dataset)}, journal={UCI Machine Learning Repository}, year={2012}, doi={10.24432/C5D02C}}

@article{wolberg1995breast, author={Wolberg, William H. and Mangasarian, Olvi L. and Street, Nick and Street, W.}, title={Breast Cancer Wisconsin (Diagnostic)}, journal={UCI Machine Learning Repository}, year={1995}, doi={10.24432/C5DW2B}}

@article{little2007exploiting, author={Little, Max A. and McSharry, Patrick E. and Roberts, Stephen J. and Costello, Declan A. E. and Moroz, Irene M.}, title={Exploiting Nonlinear Recurrence and Fractal Scaling Properties for Voice Disorder Detection}, journal={BioMedical Engineering OnLine}, volume={6}, pages={23}, year={2007}}

@misc{gong1988hepatitis, author={Gong, Gail}, title={Hepatitis Domain}, howpublished={UCI Machine Learning Repository}, year={1988}}

@article{chicco2020machine, author={Chicco, Davide and Jurman, Giuseppe}, title={Machine Learning can Predict Survival of Patients with Heart Failure from Serum Creatinine and Ejection Fraction Alone}, journal={BMC Medical Informatics and Decision Making}, volume={20}, pages={16}, year={2020}, doi={10.1186/s12911-020-1023-5}}

@misc{fedesoriano2021stroke, author={{fedesoriano}}, title={Stroke Prediction Dataset}, howpublished={Kaggle}, year={2021}, url={https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset}}
```

---

## 10. Honesty note (important)

A few things to flag as you write, so your paper doesn't repeat the report's earlier mistake of overstating things:

- **You cannot claim novelty in the datasets** — all 9 are established public benchmarks used in dozens of prior papers. Your paper's contribution is the *system* (multi-agent orchestration + automated per-disease algorithm selection + full-feature-set methodology + FHIR/RAG integration), not the datasets themselves. Frame it that way.
- **Don't cite the algorithm papers as if you invented the algorithms** — cite them as "we use Random Forest (Breiman, 2001)..." not "we developed a Random Forest approach."
- **The Stroke and Hepatitis models have real, citable limitations** (severe imbalance, small test sets) — citing Chawla et al. (2002) and general small-sample-size literature to *explain* these numbers honestly will read as more credible to reviewers than omitting the discussion.
- I was not able to verify a peer-reviewed academic paper specifically describing LangGraph itself (it's a software framework, not a research publication) — cite it as software (LangChain/LangGraph documentation or GitHub) rather than inventing an academic reference for it.
