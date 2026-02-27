# OYA AI Workflows - Streamlit Implementation Plan

## Problem Statement

OYA needs three interconnected AI workflows to scale their soccer/lifestyle brand:
1. **Sales Automation** - Scrape team data, clean, segment, automate outreach
2. **AI Jersey Design** - Self-serve kit customization using AI + templates
3. **AI Video/Content** - Automated marketing content from designs

**Why it matters**: Without these systems, OYA relies on manual processes for lead generation, design, and content -- none of which scale. Building them as a unified Streamlit app gives a functional internal tool + customer-facing design portal fast.

**Success criteria**: A deployable multi-page Streamlit app where OYA staff can run scraping jobs, manage leads, and generate AI designs and video content.

---

## Solution Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    STREAMLIT MULTI-PAGE APP                   │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐    │
│  │  WF1: Lead  │  │ WF2: Jersey │  │ WF3: Video/      │    │
│  │  Engine     │  │ Designer    │  │ Content           │    │
│  │             │  │             │  │                    │    │
│  │ - Scraper   │  │ - Template  │  │ - Design→Video    │    │
│  │ - Cleaner   │  │ - AI Gen    │  │ - Scene Control   │    │
│  │ - Segmenter │  │ - Controls  │  │ - Assembly        │    │
│  │ - Outreach  │  │ - Export    │  │ - Export           │    │
│  └──────┬──────┘  └──────┬──────┘  └────────┬───────────┘    │
│         │                │                   │               │
│  ┌──────▼────────────────▼───────────────────▼──────────┐    │
│  │              SHARED DATA LAYER                        │    │
│  │  SQLite/PostgreSQL  │  S3/Local Storage  │  Config   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              EXTERNAL SERVICES                        │    │
│  │  OpenAI/Claude API │ SendGrid │ Twilio │ Replicate  │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

```
WORKFLOW 1 (Sales):
  URL/Search Input ──▶ Scraper ──▶ Raw Data ──▶ Cleaner ──▶ Validated Leads
  Validated Leads ──▶ AI Segmenter ──▶ Categorized CRM ──▶ Outreach Engine

WORKFLOW 2 (Design):
  User Input (team info) ──▶ Template Selection ──▶ AI Generation
  AI Generation ──▶ Preview ──▶ User Adjustments ──▶ Export (PNG/PDF)

WORKFLOW 3 (Video):
  Design Assets ──▶ Scene Template ──▶ AI Video Gen ──▶ Assembly
  Assembly ──▶ Branding Overlay ──▶ Format Resize ──▶ Export

CROSS-WORKFLOW:
  WF1 (lead converts) ──▶ WF2 (designs kit) ──▶ WF3 (generates promo video)
```

---

## Project Structure

```
oya/
├── app.py                          # Main Streamlit entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .streamlit/
│   └── config.toml                 # Streamlit theming (OYA brand)
│
├── pages/                          # Streamlit multi-page app
│   ├── 1_Dashboard.py              # Overview / KPIs
│   ├── 2_Lead_Scraper.py           # WF1: Data collection UI
│   ├── 3_Lead_Manager.py           # WF1: CRM view, segmentation, outreach
│   ├── 4_Jersey_Designer.py        # WF2: AI design tool
│   ├── 5_Content_Studio.py         # WF3: Video/content generation
│   └── 6_Settings.py               # API keys, config, domain management
│
├── src/
│   ├── __init__.py
│   ├── config.py                   # App configuration, env vars
│   │
│   ├── scraping/                   # WF1: Data Collection
│   │   ├── __init__.py
│   │   ├── base_scraper.py         # Abstract scraper interface
│   │   ├── google_maps_scraper.py  # Google Maps/Places API
│   │   ├── web_scraper.py          # Generic website scraper
│   │   ├── social_scraper.py       # Social media profile scraper
│   │   └── league_scraper.py       # League directory parser
│   │
│   ├── data/                       # WF1: Data Processing
│   │   ├── __init__.py
│   │   ├── cleaner.py              # Dedup, normalize, validate
│   │   ├── email_validator.py      # MX checks, bounce prediction
│   │   ├── enricher.py             # Contact enrichment
│   │   └── models.py               # Pydantic models (Team, Lead, Contact)
│   │
│   ├── segmentation/               # WF1: AI Segmentation
│   │   ├── __init__.py
│   │   └── classifier.py           # LLM-based lead categorization
│   │
│   ├── outreach/                   # WF1: Outreach Automation
│   │   ├── __init__.py
│   │   ├── email_sender.py         # SendGrid/Mailgun integration
│   │   ├── sms_sender.py           # Twilio integration
│   │   ├── template_engine.py      # AI-generated message templates
│   │   └── campaign_manager.py     # Sequence management, rate limiting
│   │
│   ├── design/                     # WF2: Jersey Design
│   │   ├── __init__.py
│   │   ├── templates.py            # Template definitions (patterns, styles)
│   │   ├── ai_generator.py         # Image generation (DALL-E/Stability)
│   │   ├── color_system.py         # Color palette management
│   │   └── exporter.py             # PNG/PDF/mockup export
│   │
│   ├── video/                      # WF3: Video/Content
│   │   ├── __init__.py
│   │   ├── scene_templates.py      # Scene preset definitions
│   │   ├── video_generator.py      # AI video generation (Replicate)
│   │   ├── assembler.py            # Branding, overlays, captions
│   │   └── formatter.py            # Platform-specific resizing
│   │
│   └── database/                   # Shared Data Layer
│       ├── __init__.py
│       ├── db.py                   # SQLite/PostgreSQL connection
│       ├── repositories.py         # CRUD operations
│       └── migrations.py           # Schema management
│
├── assets/                         # Static assets
│   ├── templates/                  # Jersey SVG templates
│   ├── fonts/                      # Brand fonts
│   └── brand/                      # Logos, colors, brand kit
│
├── tests/
│   ├── test_scraping/
│   ├── test_data/
│   ├── test_design/
│   ├── test_video/
│   └── test_database/
│
├── plan/                           # This plan
├── learning/                       # Research docs
├── implementation_summary/
└── standup/
```

---

## Implementation Phases

### Phase 1: Foundation (MVP Skeleton)
**Goal**: Deployable app shell with shared infrastructure

| File | Action | Description |
|------|--------|-------------|
| `app.py` | Create | Multi-page Streamlit entry point |
| `requirements.txt` | Create | All dependencies |
| `.env.example` | Create | Environment variable template |
| `.streamlit/config.toml` | Create | OYA branding theme |
| `src/config.py` | Create | Centralized config from env vars |
| `src/database/db.py` | Create | SQLite connection + schema init |
| `src/database/migrations.py` | Create | Tables: teams, leads, designs, campaigns |
| `src/database/repositories.py` | Create | CRUD for all entities |
| `src/data/models.py` | Create | Pydantic models: Team, Lead, Contact, Design |
| `pages/1_Dashboard.py` | Create | Placeholder dashboard with nav |
| `pages/6_Settings.py` | Create | API key config page |
| `Dockerfile` | Create | Container for deployment |
| `docker-compose.yml` | Create | Local dev environment |

### Phase 2: Workflow 1 - Lead Engine
**Goal**: Scrape team data, clean, segment, and view in CRM

| File | Action | Description |
|------|--------|-------------|
| `src/scraping/base_scraper.py` | Create | Abstract scraper with rate limiting |
| `src/scraping/google_maps_scraper.py` | Create | Google Places API integration |
| `src/scraping/web_scraper.py` | Create | BeautifulSoup generic scraper |
| `src/scraping/league_scraper.py` | Create | League directory parser |
| `src/data/cleaner.py` | Create | Dedup, normalize fields |
| `src/data/email_validator.py` | Create | Email format + MX record checks |
| `src/data/enricher.py` | Create | Contact enrichment logic |
| `src/segmentation/classifier.py` | Create | LLM-based team categorization |
| `pages/2_Lead_Scraper.py` | Create | Scraping UI with source selection |
| `pages/3_Lead_Manager.py` | Create | CRM table with filters, segments |

**Scraper Page UI Flow**:
```
┌─────────────────────────────────────────┐
│  Lead Scraper                           │
│                                         │
│  Source: [Google Maps ▼]                │
│  Search: [youth soccer teams london  ]  │
│  Radius: [──●────── 25 miles]           │
│                                         │
│  [🔍 Start Scraping]                    │
│                                         │
│  Progress: ████████░░ 80% (40/50)       │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Team Name │ League │ Email │... │    │
│  │ Wolves FC │ Sun L. │ a@b   │   │    │
│  │ Hawks Utd │ Youth  │ c@d   │   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [Save to CRM]  [Export CSV]            │
└─────────────────────────────────────────┘
```

### Phase 3: Workflow 1 - Outreach Automation
**Goal**: Generate and send personalized outreach from CRM

| File | Action | Description |
|------|--------|-------------|
| `src/outreach/template_engine.py` | Create | AI message generation per segment |
| `src/outreach/email_sender.py` | Create | SendGrid integration with warming |
| `src/outreach/sms_sender.py` | Create | Twilio SMS integration |
| `src/outreach/campaign_manager.py` | Create | Campaign sequences, rate limits |
| `pages/3_Lead_Manager.py` | Modify | Add outreach panel to CRM |

### Phase 4: Workflow 2 - Jersey Designer
**Goal**: AI-assisted jersey design tool

| File | Action | Description |
|------|--------|-------------|
| `src/design/templates.py` | Create | Template definitions (JSON/SVG) |
| `src/design/color_system.py` | Create | Color palette + harmony generator |
| `src/design/ai_generator.py` | Create | DALL-E/Stability image gen |
| `src/design/exporter.py` | Create | Export to PNG, PDF, mockup |
| `assets/templates/` | Create | Base SVG jersey templates |
| `pages/4_Jersey_Designer.py` | Create | Full design UI |

**Designer Page UI Flow**:
```
┌──────────────────────────────────────────────────────┐
│  Jersey Designer                                      │
│                                                      │
│  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Team Info         │  │                          │  │
│  │ Name: [Eagles FC] │  │    [JERSEY PREVIEW]      │  │
│  │ Colors: 🔴⚪⚫   │  │                          │  │
│  │ Vibe: [Modern ▼]  │  │    Front    Back         │  │
│  │ Template: [V2  ▼] │  │   ┌─────┐ ┌─────┐      │  │
│  │ Collar: [V-neck▼] │  │   │     │ │  10 │      │  │
│  │                    │  │   │LOGO │ │     │      │  │
│  │ [Generate Design]  │  │   │     │ │NAME │      │  │
│  │                    │  │   └─────┘ └─────┘      │  │
│  │ Adjustments:       │  │                          │  │
│  │ Pattern: [Stripes] │  │  [Variant 1] [2] [3]    │  │
│  │ Font: [Bold Sans]  │  │                          │  │
│  │ Numbers: [Block]   │  │                          │  │
│  └──────────────────┘  └──────────────────────────┘  │
│                                                      │
│  [Download PNG] [Download PDF] [Send to Production]  │
│  [Generate Video ──▶ WF3]                            │
└──────────────────────────────────────────────────────┘
```

### Phase 5: Workflow 3 - Content Studio
**Goal**: Generate marketing videos/content from designs

| File | Action | Description |
|------|--------|-------------|
| `src/video/scene_templates.py` | Create | Scene presets (stadium, street, etc.) |
| `src/video/video_generator.py` | Create | Replicate/Runway API integration |
| `src/video/assembler.py` | Create | Branding overlays, captions |
| `src/video/formatter.py` | Create | Platform resizing (TikTok, IG, YT) |
| `pages/5_Content_Studio.py` | Create | Video generation UI |

**Content Studio UI Flow**:
```
┌──────────────────────────────────────────────────────┐
│  Content Studio                                       │
│                                                      │
│  Input Assets:                                       │
│  [Upload Design] or [Select from Jersey Designer]    │
│                                                      │
│  Scene: [Stadium Walkout ▼]                          │
│  Style: [Cinematic ▼]                                │
│  Duration: [15s ▼]                                   │
│  Platform: [☑ TikTok] [☑ Instagram] [☐ YouTube]     │
│                                                      │
│  [Generate Preview]                                  │
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │              VIDEO PREVIEW                  │      │
│  │         ▶  0:00 / 0:15                     │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  [Download All Formats]  [Save to Library]           │
└──────────────────────────────────────────────────────┘
```

### Phase 6: Dashboard + Cross-Workflow Integration
**Goal**: Unified dashboard, workflow connections

| File | Action | Description |
|------|--------|-------------|
| `pages/1_Dashboard.py` | Modify | KPI cards, activity feed, charts |

---

## Key Technical Decisions

### Database: SQLite (MVP) -> PostgreSQL (scale)
- SQLite for MVP: zero config, file-based, works everywhere
- Migrate to PostgreSQL when needed (same SQL, use SQLAlchemy)

### AI Provider: OpenAI (primary) + Replicate (video)
- **Text/Classification**: OpenAI GPT-4o or Claude for segmentation, email generation
- **Image Generation**: OpenAI DALL-E 3 for jersey designs
- **Video Generation**: Replicate (Stable Video Diffusion, Runway Gen-3)
- All via API -- configurable in Settings page

### Scraping: Respectful + API-first
- Google Places API for business data (paid but reliable)
- BeautifulSoup for static sites, Playwright for JS-rendered
- Rate limiting built into base scraper class
- Proxy support optional

### Outreach: SendGrid + Twilio
- SendGrid for transactional/marketing email
- Twilio for SMS
- Built-in rate limiting, domain rotation config
- Compliance: unsubscribe links, CAN-SPAM headers

---

## Deployment Strategy

### Local Development
```bash
# Clone + setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
streamlit run app.py
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Production Options
1. **Streamlit Community Cloud** - Free, connect GitHub repo, auto-deploy
2. **Docker on VPS** - DigitalOcean droplet ($12/mo), full control
3. **Railway / Render** - PaaS, Docker-based, easy scaling

---

## Test Plan

### Unit Tests (per module)
- `test_scraping/`: Mock HTTP responses, verify parsing
- `test_data/`: Validation logic, dedup, email checks
- `test_design/`: Template rendering, color system
- `test_database/`: CRUD operations on test SQLite

### Integration Tests
- Scraper -> Cleaner -> DB pipeline (mocked HTTP, real DB)
- Design generation -> Export (mocked AI API, real file output)
- Campaign creation -> Message generation (mocked LLM)

### E2E Validation
1. **Setup**: `docker-compose up`, seed test data
2. **WF1**: Run scraper on test URL -> verify leads in DB -> generate outreach
3. **WF2**: Input team details -> generate design -> download PNG
4. **WF3**: Upload design -> select scene -> generate video preview
5. **Cross-WF**: Lead -> Design -> Video pipeline
6. **Cleanup**: `docker-compose down -v`

---

## Out of Scope (Phase 1)

| Item | Reason | Future Home |
|------|--------|-------------|
| Real social media scraping (FB/IG API) | Requires app review, complex auth | Phase 2 - use official APIs |
| WhatsApp integration | Business API requires approval | Phase 2 |
| Real-time collaboration on designs | Complex, needs WebSocket | Phase 3 |
| Production file formats (tech packs) | Needs manufacturing specs | Phase 2 with manufacturer input |
| User authentication | Internal tool first | Phase 2 when customer-facing |
| Payment/checkout | Out of scope for AI tool | Separate e-commerce integration |

---

## Dependencies / API Keys Required

| Service | Purpose | Estimated Cost |
|---------|---------|---------------|
| OpenAI API | Text gen (segmentation, emails) + Image gen (DALL-E) | ~$20-50/mo |
| Google Places API | Team data scraping | ~$200/mo (depends on volume) |
| SendGrid | Email outreach | Free tier (100/day) -> $20/mo |
| Twilio | SMS outreach | ~$0.0079/SMS |
| Replicate | Video generation | ~$0.05-0.50/video |

---

## Implementation Order Summary

```
Phase 1: Foundation        ──▶ Deployable skeleton, DB, config
Phase 2: Lead Scraping     ──▶ Scraper + Cleaner + CRM view
Phase 3: Outreach          ──▶ Email/SMS campaigns from CRM
Phase 4: Jersey Designer   ──▶ AI design tool with templates
Phase 5: Content Studio    ──▶ Video generation pipeline
Phase 6: Integration       ──▶ Dashboard, cross-workflow links
```

Each phase produces a deployable increment. Phase 1-2 deliver immediate business value (lead generation).
