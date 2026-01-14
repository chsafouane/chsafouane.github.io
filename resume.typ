#set page(
  paper: "a4",
  margin: (top: 0.4in, bottom: 0.4in, left: 0.5in, right: 0.5in),
)

#set text(font: "Helvetica Neue", size: 9pt)
#set par(justify: true, leading: 0.5em)

#align(center)[
  #text(size: 22pt, weight: "bold")[SAFOUANE CHERGUI]
  #v(-2pt)
  #text(size: 11pt)[Lead Data Scientist]
  #v(-4pt)
  #text(size: 9pt)[Paris, France]
  #v(-4pt)
  #text(size: 9pt)[chsafouane\@gmail.com #h(4pt) | #h(4pt) #link("https://www.linkedin.com/in/safouane-chergui/")[LinkedIn] #h(4pt) | #h(4pt) #link("https://github.com/chsafouane")[GitHub]]
]

#v(4pt)
#line(length: 100%, stroke: 0.5pt + gray)
#v(2pt)

#text(size: 10pt, weight: "bold")[TECHNICAL EXPERTISE]
#v(2pt)

#grid(
  columns: (auto, 1fr),
  gutter: 6pt,
  [*ML/AI Domains:*], [NLP/LLMs, RAG Systems, Search & Recommendation Engines, Computer Vision],
  [*Cloud & Infrastructure:*], [GCP, AWS, Databricks, Docker, Kubernetes, MLflow, Airflow],
  [*Specialized:*], [LLM Evaluation, Production ML Monitoring, Model Drift Detection, Agentic Systems]
)

#v(4pt)
#line(length: 100%, stroke: 0.5pt + gray)
#v(2pt)

#text(size: 10pt, weight: "bold")[PROFESSIONAL EXPERIENCE]
#v(4pt)

#grid(
  columns: (1fr, auto),
  [*Founder & AI Engineer* #h(6pt) | #h(6pt) LumiereAI], [_April 2025 - Current_]
)
#v(1pt)
- Built production *agentic system* for insurance companies: *multi-modal pipeline* combining Vertex AI Gemini API for case analysis with ElevenLabs voice synthesis, built on Google ADK framework and deployed on GCP (Cloud Run, BigQuery, Cloud Storage)

#v(6pt)
#grid(
  columns: (1fr, auto),
  [*Lead Data Scientist* #h(6pt) | #h(6pt) EDF], [_April 2025 - Current_]
)
#v(1pt)
- Architected *document parsing* and *RAG pipeline* using Docling with hybrid semantic/lexical search, deployed on GCP (Vertex AI)
- Built *LLM evaluation framework* to benchmark and monitor model performance on business-critical tasks
- Deployed production inference endpoints using *Vertex AI Prediction* with automated scaling and monitoring

#v(6pt)
#grid(
  columns: (1fr, auto),
  [*Senior Data Scientist* #h(6pt) | #h(6pt) Doctolib], [_Sep 2024 - April 2025_]
)
#v(1pt)
- Architected and deployed a *RAG system* reducing customer support costs by *20%*
- Enhanced phone assistant system using fast *search system* and *agents* for medical appointment booking

#v(6pt)
#grid(
  columns: (1fr, auto),
  [*Senior Data Scientist* #h(6pt) | #h(6pt) Mirakl], [_Oct 2023 - Aug 2024_]
)
#v(1pt)
- Built & deployed *LLM-powered catalog integration system* reducing products onboarding from *20+ days to hours*
- Implemented end-to-end MLOps pipeline for model versioning and automated retraining using MLflow
- Trained & deployed small LLMs for domain-specific tasks, *reducing third-party API costs by 10X*

#v(6pt)
#grid(
  columns: (1fr, auto),
  [*Senior Data Scientist* #h(6pt) | #h(6pt) TheFork (TripAdvisor)], [_May 2022 - Oct 2023_]
)
#v(1pt)
- Designed *recommendation algorithms* driving *35% increase* in page visits across web, mobile, and email channels
- Pioneered *LLM-based review summarization* system processing 500K+ reviews monthly
- Optimized search using semantic embeddings (Elasticsearch, pgvector); built models serving 20M+ users

#v(6pt)
#grid(
  columns: (1fr, auto),
  [*Data Scientist* #h(6pt) | #h(6pt) EDF], [_Dec 2018 - May 2022_]
)
#v(1pt)
- Deployed *production ML models* for customer segmentation and churn prediction
- Designed *real-time drift detection system* monitoring 15+ models in production
- Built A/B testing framework reducing experiment analysis time by 60%
- Developed *predictive maintenance models* using deep learning (CNN/RNN)

#v(4pt)
#line(length: 100%, stroke: 0.5pt + gray)
#v(2pt)

#text(size: 10pt, weight: "bold")[KEY ACHIEVEMENTS & LEADERSHIP]
#v(2pt)
- *Production Impact:* Delivered 20+ production ML systems generating measurable cost savings and revenue impact across multiple business units
- *Technical Leadership:* Led and mentored several data scientists; established code review practices and ML development standards
- *Stakeholder Management:* Translated complex ML capabilities into business strategy, presenting to C-level executives and aligning cross-functional teams

#v(4pt)
#line(length: 100%, stroke: 0.5pt + gray)
#v(2pt)

#grid(
  columns: (1fr, 1fr),
  gutter: 20pt,
  [
    #text(size: 10pt, weight: "bold")[EDUCATION & CERTIFICATIONS]
    #v(2pt)
    - *MSc Engineering* - INSA Lyon (2013-2018)
    - *Deep Learning Specialization* - Coursera
    - *Statistical Learning* - Stanford Online
  ],
  [
    #text(size: 10pt, weight: "bold")[LANGUAGES]
    #v(2pt)
    - French (Fluent)
    - English (Fluent)
    - Spanish (Fluent)
    - Arabic (Native)
    - Mandarin (Learning)
  ]
)
