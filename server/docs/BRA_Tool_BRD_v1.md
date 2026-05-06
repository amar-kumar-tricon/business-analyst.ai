# BRA Tool — Business Requirement Document (BRD v1)

> Extracted from: BRA_Tool_BRD_v1.pdf

## Page 1

BRA TOOL  —  CONFIDENTIAL & INTERNAL 
 
Business Requirement 
Analysis Tool 
 
BRD + Technical Architecture Document 
 
AI-Powered Multi-Agent Platform for Product Teams 
 
Version 
1.0 — Draft 
Date 
April 20, 2026 
Author 
Varun 
Classification 
Internal — Product & Engineering 
Stack 
LangGraph · FastAPI · React/Angular · PostgreSQL · 
pgvector 
 
 
  AI-Powered · Human-Approved · Version-Controlled

---

## Page 2

1.  EXECUTIVE SUMMARY 
The Business Requirement Analysis (BRA) Tool is an internal AI-powered platform designed to automate 
the multi-stage process that product managers and business analysts perform when a new client 
engagement begins. Instead of manually producing discovery notes, architecture diagrams, and sprint 
plans, the product person uploads one or more client requirement documents and the platform 
orchestrates a pipeline of specialised LLM agents to produce structured deliverables at each stage. 
Human-in-the-loop approval gates separate every stage. No agent moves forward without an explicit 
sign-off, ensuring the product person retains full control. All work is versioned so that evolving client 
requirements can be layered as v2, v3 iterations on top of a frozen baseline. 
1.1  Key Highlights 
• 
Multi-agent orchestration: Four specialised agents (Analyser, Discovery/QnA, Architecture, Sprint 
Planner) orchestrated via LangGraph with inter-agent communication. 
• 
Human approval gates: Product person reviews and approves output at every stage before the 
pipeline advances. 
• 
Multi-format document ingestion: Accepts PDF, DOCX, DOC, PPT, PPTX, XLSX, XLS up to 50 MB per 
file; multiple files allowed; structured/unstructured content including images, tables, and links. 
• 
Configurable LLM per agent: Each agent has an independent model selector in the UI settings panel 
— switch between OpenAI, Anthropic Claude, or other providers without code changes. 
• 
Architecture diagrams: Stage 3 generates both Mermaid.js and PlantUML diagrams rendered live in 
the browser. 
• 
Version management: Requirement changes at any stage trigger a re-run delta across all 
downstream stages; finalized versions are snapshotted as v1, v2, v3, etc. 
• 
Export capability: Outputs from every stage are exportable as PDF or DOCX. 
 
2.  PROJECT GOALS & SCOPE 
2.1  Goals 
• 
Reduce the time a product manager spends on initial requirement analysis from days to hours. 
• 
Standardise deliverable quality across all client engagements. 
• 
Capture open questions, risks, and scope boundaries early in the engagement lifecycle. 
• 
Enable requirement traceability from raw document through to sprint tasks. 
• 
Provide full audit history with version snapshots for contractual and governance purposes. 
2.2  In Scope 
• 
Document upload and ingestion pipeline (PDF, DOCX, PPTX, XLSX, images inside documents). 
• 
Document Analyser Agent — scoring, enrichment, and structured output generation.

---

## Page 3

• 
Discovery / QnA Agent — dynamic question generation and interactive Q&A workflow. 
• 
Architecture Agent — HLD diagram generation using Mermaid.js and PlantUML. 
• 
Sprint Planning Agent — sprint breakdown with story points and man-hours. 
• 
Human-in-the-loop approval at every stage with inline editing capability. 
• 
Multi-LLM configuration per agent with runtime switching. 
• 
Versioning system (v1, v2, ...) with delta re-processing on requirement changes. 
• 
Export to PDF and DOCX for all stage outputs. 
• 
PostgreSQL for structured data + pgvector / Qdrant for semantic document retrieval. 
• 
FastAPI backend with REST + WebSocket endpoints. 
• 
React or Angular frontend (framework decision deferred). 
2.3  Out of Scope 
• 
Real-time client collaboration portal (client-facing UI). 
• 
Automated code generation or ticket creation in Jira/Linear. 
• 
Fine-tuning or training custom LLM models. 
• 
Mobile application. 
• 
Multi-tenant SaaS billing or subscription management. 
• 
Integration with specific CRM systems (Salesforce, HubSpot) in v1. 
 
3.  STAKEHOLDERS & USER PERSONAS 
Role 
Responsibility 
Interaction with Tool 
Product Manager / BA 
Primary user; first point of contact 
with client 
Uploads docs, reviews & approves 
each stage output 
Technical Lead / Architect 
Reviews architecture diagrams and 
technical decisions 
Consumes Stage 3 output; may co-
approve 
Project Manager 
Reviews sprint plan and resource 
estimates 
Consumes Stage 4 output; owns 
timeline 
Client 
Provides high-level requirement 
documents 
Indirect — answers fed into 
Discovery stage 
System Admin 
Manages LLM API keys and platform 
config 
Admin panel for model settings and 
user management

---

## Page 4

4.  FUNCTIONAL REQUIREMENTS 
4.1  Document Upload & Input Panel 
Must Have 
 
• Multi-file uploader accepting PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX. 
• Maximum 50 MB per file; multiple files allowed in one session. 
• Structured and unstructured content support: images, tables, embedded links. 
• Free-text textarea alongside uploader for additional context, instructions, or raw requirement text. 
• Upload progress indicator and file validation feedback. 
• Ability to add/remove files before triggering analysis. 
 
 
Should Have 
 
• Drag-and-drop upload interface. 
• Preview panel showing extracted text/tables from uploaded files. 
• Option to paste a public URL for web-hosted documents. 
 
 
4.2  Stage 1 — Document Analyser Agent 
The Analyser Agent is the entry point to the pipeline. It parses all uploaded documents, evaluates their 
completeness, and produces a structured analysis report. 
▸  Scoring Criteria 
Criterion 
Weight 
Description 
Functional Requirements 
20% 
Are user stories or feature 
descriptions present? 
Business Logic / Rules 
15% 
Are business rules, workflows, or 
constraints described? 
Existing Product / System Info 
15% 
Context about current systems or 
legacy integrations 
Target Audience / Users 
10% 
Persona or user segment definition

---

## Page 5

Architecture / Technical Context 
15% 
Any existing tech stack, infra, or 
constraints 
Non-Functional Requirements 
10% 
Performance, security, scalability 
expectations 
Timeline / Budget Signals 
10% 
Delivery expectations or resource 
constraints 
Visual Assets (Diagrams/Flows) 
5% 
Wireframes, mockups, flow 
diagrams included 
 
 
▸  Score-Based Routing Logic 
Score 1–5 out of 10: Document is insufficient. The agent automatically enriches it using LLM inference — 
filling gaps, inferring implied requirements, and flagging assumptions. The enriched version is presented 
for review before moving on. 
Score 6–10 out of 10: Document is sufficient. The agent proceeds directly to structured output 
generation without enrichment. 
▸  Stage 1 Outputs (Must Have) 
• 
Executive Summary — 2–3 paragraph overview of the engagement. 
• 
Project Overview — Objective, Scope, Out-of-Scope. 
• 
Functional Requirements — categorised as Must Have / Should Have / Good to Have (MoSCoW). 
• 
Identified Risks — technical, business, and delivery risks. 
• 
Recommended Team — suggested roles and rough team size. 
• 
Open Questions for Client — unanswered items surfaced for Stage 2. 
• 
Document Completeness Score — numeric score with per-criterion breakdown. 
All outputs are editable inline by the product person before approval. Export to PDF/DOCX available at 
this stage. 
4.3  Stage 2 — Discovery / QnA Agent 
The Discovery Agent conducts a structured Q&A session to surface ambiguities and deepen the 
requirement understanding. It communicates back to the Analyser Agent to update the Stage 1 analysis 
based on answers received. 
▸  Behaviour 
• 
Questions are generated one at a time based on open questions from Stage 1 and gaps in the 
document.

---

## Page 6

• 
Product person can answer directly, defer the question (add to 'Ask Client' backlog), or mark as 'Not 
Applicable'. 
• 
Answered questions trigger a delta update back to the Stage 1 Analyser Agent — the analysis report 
is updated in real time. 
• 
Unanswered / deferred questions are grouped into an 'Open Questions for Client' section preserved 
for future sessions. 
• 
Agent adapts follow-up questions based on prior answers within the session. 
• 
Session can be paused and resumed; partial answers are saved. 
4.4  Stage 3 — Architecture Agent 
Based on the finalised requirement analysis from Stages 1 and 2, the Architecture Agent generates high-
level architecture and user flow diagrams. 
▸  Diagram Types 
Diagram 
Tool 
Purpose 
System Architecture 
PlantUML 
Component-level view: services, 
databases, integrations, external 
APIs 
Data Flow Diagram 
Mermaid.js (flowchart) 
How data moves between 
components 
User Flow 
Mermaid.js (sequence/state) 
End-to-end user journey for key 
scenarios 
Entity Relationship 
PlantUML 
Core data model if applicable 
Deployment Architecture 
PlantUML 
Cloud/infra topology if deployment 
context is known 
 
 
Rendering Approach 
 
• Mermaid.js diagrams are rendered live in the browser using mermaid.js library — editable DSL with 
live preview. 
• PlantUML diagrams are generated server-side (FastAPI) using plantuml JAR and returned as SVG/PNG. 
• Both diagram types are downloadable as SVG/PNG and included in DOCX/PDF exports.

---

## Page 7

4.5  Stage 4 — Sprint Planning Agent 
The Sprint Planning Agent converts the finalised functional requirements into a detailed sprint plan with 
story points, man-hours, MVP scope, and team composition recommendations. 
▸  Output Structure 
Field 
Example / Description 
Total Sprints 
6 (2-week sprints = 12 weeks) 
Total Story Points 
217 points across all sprints 
Total Man Hours 
868 hours (across all roles) 
MVP Cut-off 
End of Sprint 4 — core features delivered 
Sprint Goals 
Per-sprint objective with feature list 
Story Breakdown 
User stories with acceptance criteria, points, and role 
assignment 
Team Composition 
FE Dev x2, BE Dev x2, QA x1, DevOps x1, PM x1 
(example) 
Technology Stack 
Per-component technology recommendations 
Risk Register 
Updated risks post-planning with mitigation notes 
 
 
5.  NON-FUNCTIONAL REQUIREMENTS 
Category 
Requirement 
Performance 
Document processing (up to 50 MB) must complete 
within 60 seconds for Stage 1. 
Scalability 
System must support concurrent sessions for up to 50 
simultaneous users. 
Reliability 
Agent pipeline must handle LLM timeouts with retry 
logic (max 3 retries, exponential backoff). 
Security 
LLM API keys stored encrypted; documents stored in 
encrypted-at-rest storage; role-based access control.

---

## Page 8

Auditability 
All agent inputs/outputs logged with timestamps; 
version history immutable. 
Availability 
99.5% uptime SLA for internal deployment. 
Observability 
Structured logging, agent trace IDs, LangSmith or 
equivalent tracing integration. 
Portability 
Docker Compose for local dev; Kubernetes-ready for 
production deployment.

---

## Page 9

6.  TECHNICAL ARCHITECTURE 
The system is built on a three-tier architecture: a React/Angular SPA frontend, a FastAPI Python 
backend, and a LangGraph-orchestrated agent layer backed by PostgreSQL + pgvector for persistence. 
6.1  High-Level Architecture Overview 
Architecture Layers 
 
┌──────────────────────────────────────────────────────────────┐ 
│  FRONTEND  (React / Angular + TypeScript)                    │ 
│  Upload UI · Stage Dashboards · Diagram Renderer · Export   │ 
└──────────────────┬───────────────────────────────────────────┘ 
                   │  REST + WebSocket (FastAPI)                 
┌──────────────────▼───────────────────────────────────────────┐ 
│  API LAYER  (FastAPI + Python 3.11)                          │ 
│  Auth · File Ingestion · Stage Routing · Export Service      │ 
└──────────────────┬───────────────────────────────────────────┘ 
                   │  LangGraph Graph Execution                  
┌──────────────────▼───────────────────────────────────────────┐ 
│  AGENT LAYER  (LangGraph + LangChain)                        │ 
│  Analyser Agent → Discovery Agent → Arch Agent → Sprint Agent│ 
│  Inter-agent messaging via LangGraph state & channels         │ 
└──────────────────┬───────────────────────────────────────────┘ 
                   │                                              
┌──────────────────▼───────────────────────────────────────────┐ 
│  DATA LAYER                                                   │ 
│  PostgreSQL (structured) · pgvector (embeddings/semantic)    │ 
│  S3-compatible object store (raw documents + exports)        │ 
└──────────────────────────────────────────────────────────────┘ 
 
 
6.2  LangGraph Agent Graph Design 
LangGraph is used to define the agent pipeline as a stateful directed graph. Each stage is a graph node. 
Edges represent either automatic progression or human approval checkpoints (interrupt_before). The 
global state object carries all artifacts between nodes. 
▸  Graph State Schema

---

## Page 10

GraphState (TypedDict) 
 
project_id          : str 
version             : int 
uploaded_documents  : list[DocumentChunk] 
additional_context  : str 
analyser_output     : AnalyserResult | None 
discovery_qa        : list[QAExchange] 
open_questions      : list[str] 
architecture_output : ArchitectureResult | None 
sprint_plan         : SprintPlan | None 
current_stage       : Literal['upload','analyse','discovery','architecture','sprint','finalized'] 
approval_status     : dict[str, bool] 
llm_config          : dict[str, LLMConfig]    # per-agent model config 
change_log          : list[ChangeEvent] 
 
 
▸  Graph Nodes & Edges 
Node 
Type 
Description 
Transition 
document_ingestion 
Tool Node 
Parse files, chunk text, 
extract tables/images, 
embed vectors 
→ analyser_agent 
analyser_agent 
LLM Node 
Score document, enrich if 
needed, generate Stage 1 
outputs 
→ human_review_1 
human_review_1 
Interrupt 
Product person reviews, 
edits, approves Stage 1 
output 
→ discovery_agent 
discovery_agent 
LLM Node 
Generate Q&A, process 
answers, update 
analyser_output state 
→ human_review_2 
human_review_2 
Interrupt 
Product person reviews 
discovery summary and 
open questions 
→ architecture_agent 
architecture_agent 
LLM Node 
Generate Mermaid + 
PlantUML diagrams from 
final analysis 
→ human_review_3

---

## Page 11

human_review_3 
Interrupt 
Product person reviews 
diagrams, optionally 
requests regeneration 
→ sprint_agent 
sprint_agent 
LLM Node 
Generate sprint plan, 
story breakdown, team 
recommendation 
→ human_review_4 
human_review_4 
Interrupt 
Final approval — product 
person finalizes and 
versions 
→ finalized 
change_propagation 
Tool Node 
On new requirement: 
delta re-run from affected 
stage onwards 
→ relevant stage 
 
 
6.3  Agent Designs 
6.3.1  Document Analyser Agent 
Property 
Detail 
Default LLM 
GPT-4o (configurable) 
Tools Used 
FileParserTool  ·  DocumentScorerTool  ·  
EnrichmentTool  ·  MoSCoWClassifierTool  ·  
RiskExtractorTool  ·  TeamRecommenderTool 
Prompt Strategy 
Chain-of-thought scoring → structured JSON output via 
function calling / tool use. 
Output Format 
Structured JSON mapped to AnalyserResult schema; 
rendered as rich UI cards. 
 
 
6.3.2  Discovery / QnA Agent 
Property 
Detail 
Default LLM 
GPT-4o or Claude Sonnet (configurable)

---

## Page 12

Tools Used 
QuestionGeneratorTool  ·  AnswerProcessorTool  ·  
StateUpdaterTool  ·  OpenQuestionTrackerTool 
Prompt Strategy 
Iterative: generate next question based on current 
graph state → await human answer → process → 
update state → repeat until no more questions. 
Output Format 
List of QAExchange objects; updated AnalyserResult 
with delta changes highlighted. 
 
 
6.3.3  Architecture Agent 
Property 
Detail 
Default LLM 
GPT-4o or Claude Opus (configurable) 
Tools Used 
MermaidGeneratorTool  ·  PlantUMLGeneratorTool  ·  
DiagramValidatorTool  ·  UserFlowExtractorTool 
Prompt Strategy 
Decompose requirements into components → identify 
interactions → generate DSL → validate syntax → 
render. 
Output Format 
Mermaid DSL strings + PlantUML DSL strings; rendered 
as SVG in browser. 
 
 
6.3.4  Sprint Planning Agent 
Property 
Detail 
Default LLM 
GPT-4o (configurable) 
Tools Used 
StoryDecomposerTool  ·  StoryPointerTool  ·  
SprintAllocatorTool  ·  TeamSizerTool  ·  
MVPClassifierTool 
Prompt Strategy 
Decompose features into epics → stories → tasks → 
estimate points using reference velocity → allocate to 
sprints → identify MVP boundary.

---

## Page 13

Output Format 
SprintPlan JSON object; rendered as interactive sprint 
board in UI. 
 
 
6.4  Inter-Agent Communication 
Agents communicate via the shared LangGraph StateGraph state object. No direct agent-to-agent RPC is 
needed — state changes by one agent are immediately visible to the next. For the Discovery Agent's 
back-channel update to the Analyser output, a dedicated state key (analyser_output) is mutated and a 
delta_changes list tracks what changed and why. 
Communication Pattern 
 
1. Analyser Agent writes → analyser_output in state. 
2. Discovery Agent reads analyser_output.open_questions, generates Q&A. 
3. After each answer, Discovery Agent calls StateUpdaterTool to patch analyser_output. 
4. Architecture Agent reads the updated analyser_output (post-discovery) as its input. 
5. Sprint Agent reads analyser_output + architecture_output to build the plan. 
6. change_propagation node reads change_log and re-invokes affected agents with updated state. 
 
 
7.  API DESIGN (FASTAPI) 
7.1  REST Endpoints 
Method 
Endpoint 
Description 
POST 
/api/projects 
Create new project session 
GET 
/api/projects/{project_id} 
Get project with all stage outputs 
POST 
/api/projects/{project_id}/documen
ts 
Upload documents (multipart/form-
data) 
POST 
/api/projects/{project_id}/analyse 
Trigger Stage 1 — Analyser Agent 
POST 
/api/projects/{project_id}/approve/
{stage} 
Submit human approval with 
optional edits 
GET 
/api/projects/{project_id}/discovery Get current Q&A state

---

## Page 14

POST 
/api/projects/{project_id}/discovery
/answer 
Submit answer to current question 
GET 
/api/projects/{project_id}/architect
ure 
Get diagram DSL and rendered SVGs 
POST 
/api/projects/{project_id}/architect
ure/regenerate 
Request diagram regeneration 
GET 
/api/projects/{project_id}/sprint 
Get sprint plan 
POST 
/api/projects/{project_id}/finalize 
Finalize and create version snapshot 
GET 
/api/projects/{project_id}/versions 
List all versions 
POST 
/api/projects/{project_id}/export 
Export stage output as PDF/DOCX 
GET 
/api/settings/llm-config 
Get LLM config per agent 
PUT 
/api/settings/llm-config/{agent_id} 
Update LLM model for a specific 
agent 
 
 
7.2  WebSocket Endpoint 
WS /ws/projects/{project_id}/stream 
 
Used for real-time streaming of agent output tokens to the frontend. 
Events: { type: 'token' | 'stage_complete' | 'error' | 'question', payload: ... } 
Enables live display of agent output as it is generated, improving perceived responsiveness. 
 
 
8.  DATABASE DESIGN 
8.1  PostgreSQL Schema (Core Tables) 
Table 
Key Columns 
Purpose 
projects 
id, name, status, current_stage, 
created_at, created_by 
Top-level project entity

---

## Page 15

project_versions 
id, project_id, version_number, 
snapshot_json, created_at 
Immutable version snapshots 
documents 
id, project_id, filename, file_type, 
s3_key, size_bytes, parsed_text, 
score 
Uploaded documents metadata and 
parsed content 
stage_outputs 
id, project_id, version, stage, 
output_json, approved_at, 
approved_by, edits_json 
Outputs for each pipeline stage 
discovery_qa 
id, project_id, question, answer, 
status (answered/deferred/na), 
created_at 
Q&A exchange records 
change_events 
id, project_id, source_stage, 
description, triggered_at, 
reprocessed_stages 
Requirement change tracking 
llm_configs 
id, agent_id, provider, 
model_name, temperature, 
max_tokens, api_key_ref 
Per-agent LLM configuration 
users 
id, email, name, role 
(admin/reviewer), created_at 
Internal user accounts 
 
 
8.2  pgvector — Semantic Search 
Table 
Key Columns 
Purpose 
document_chunks 
id, document_id, chunk_text, 
chunk_index, embedding (vector 
1536) 
Chunked document text with 
OpenAI or local embeddings 
requirement_nodes 
id, project_id, requirement_text, 
category, embedding (vector 1536) 
Individual requirement items as 
searchable nodes 
 
 
Vector embeddings enable semantic search across requirements — useful for duplicate detection, gap 
analysis, and change-impact assessment. 
9.  TECHNOLOGY STACK

---

## Page 16

Layer 
Technology 
Justification 
Agent Orchestration 
LangGraph (LangChain ecosystem) 
Stateful graph with native human-
in-the-loop interrupt support 
LLM Providers 
OpenAI GPT-4o · Anthropic Claude · 
Pluggable via LangChain 
Multi-model support; per-agent 
config 
Backend Framework 
FastAPI (Python 3.11) 
Async-first, auto OpenAPI docs, 
WebSocket support 
Document Parsing 
PyMuPDF · python-docx · python-
pptx · openpyxl · Unstructured.io 
Handles all required file formats 
including image extraction 
Embeddings 
OpenAI text-embedding-3-small or 
local BGE model 
Semantic chunking and retrieval 
Primary Database 
PostgreSQL 15 
ACID compliance, JSONB for flexible 
stage outputs 
Vector Store 
pgvector (PostgreSQL extension) 
Co-located with primary DB; Qdrant 
as alternative 
Object Storage 
MinIO (self-hosted) / AWS S3 
Raw document and export storage 
Diagram Generation 
Mermaid.js (browser) · PlantUML 
(server-side JAR) 
Both rendering approaches required 
Frontend 
React 18 / Angular 17 (TypeScript) 
Framework decision deferred; both 
are viable 
Frontend State 
Zustand (React) / NgRx (Angular) 
Predictable state for multi-stage 
wizard UI 
Export 
WeasyPrint (PDF) · python-docx 
(DOCX) 
Server-side export generation 
Authentication 
FastAPI-Users + JWT 
Lightweight auth for internal SaaS 
Containerisation 
Docker + Docker Compose 
Dev parity; K8s manifests for 
production 
Observability 
LangSmith + Prometheus + Grafana 
LLM tracing + infra monitoring 
Testing 
Pytest · Playwright (E2E) · pytest-
asyncio 
Unit, integration, and E2E coverage

---

## Page 17

10.  VERSIONING & CHANGE MANAGEMENT 
Every finalized project state is snapshot as an immutable version record. When new requirements 
arrive, the product person adds them to the current session. The system identifies which stages are 
affected by the change and triggers a targeted re-run from the earliest impacted stage forward, while 
preserving all previous stage outputs until the re-run completes and is approved. 
▸  Version Lifecycle 
• 
Product person finalizes Stage 4 → system creates v1 snapshot (immutable). 
• 
Client returns with updated requirements → product person adds new documents or text. 
• 
change_propagation node identifies delta impact (e.g., new feature affects Stages 1, 3, 4 but not 2). 
• 
Targeted re-run: affected agents re-execute with merged state (old + new requirements). 
• 
Product person approves each updated stage — creates v2 snapshot on finalization. 
• 
Both v1 and v2 are accessible; diffs between versions are displayed in the UI. 
11.  RISKS & MITIGATIONS 
Risk 
Impact 
Likelihood 
Mitigation 
LLM hallucination in 
requirements output 
High 
Medium 
Structured JSON output 
with validation schema; 
human approval gate 
before any stage output is 
used downstream. 
Large document 
processing timeout (>50 
MB) 
Medium 
Medium 
Async chunked processing 
with progress events; 
background job queue 
(Celery/ARQ). 
LLM API rate limits under 
concurrent users 
Medium 
High 
Per-agent rate limiter; 
request queuing; fallback 
model config. 
Diagram DSL syntax errors 
(Mermaid/PlantUML) 
Low 
Medium 
DiagramValidatorTool 
auto-corrects common 
syntax issues; fallback to 
simplified diagram on 
error.

---

## Page 18

User edits breaking 
downstream agent 
context 
High 
Low 
Edit diffs stored 
separately; 
change_propagation re-
runs affected stages with 
edited content merged 
into state. 
Scope creep in multi-
version projects 
Medium 
High 
Strict version 
snapshotting; change_log 
provides full audit of every 
addition and its impact.
