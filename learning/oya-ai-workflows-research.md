# OYA AI Workflows - Learning & Research

## Business Context

OYA is a soccer/lifestyle brand (DTC today) with a long-term strategy of servicing teams at scale:
- Sunday leagues, amateur leagues, youth clubs, academies, semi-pro teams
- Need scalable growth systems for outreach, customization, and marketing

## Three Workflows Required

### Workflow 1: Team Data Scraping + Sales Automation
- **Problem**: Teams are fragmented across league websites, Facebook, Instagram, Google Maps, club sites, tournament sites. No centralized DB.
- **Solution**: AI-powered scraping -> enrichment -> outreach automation
- **Layers**: Data Collection, Cleaning/Validation, Segmentation AI, Outreach Automation, Compliance

### Workflow 2: AI Jersey Design & Customization
- **Problem**: Custom kits require design labor, long turnarounds, manual revisions, high cost
- **Solution**: AI-assisted design platform using OYA templates
- **Components**: Template Engine, AI Customization Layer, Design Control System, Production Integration

### Workflow 3: AI Video Generation & Mockup Pipeline
- **Problem**: High-quality videos are expensive, slow, hard to scale
- **Solution**: AI-driven video generation pipeline
- **Capabilities**: Design-to-Video Pipeline, Scene Control System, AI Video Assembly

## Tech Stack Analysis for Streamlit Implementation

### Why Streamlit
- Rapid prototyping - get an MVP fast
- Python-native - integrates well with scraping libs, AI APIs, data processing
- Built-in UI components (forms, file uploads, charts, tables)
- Easy deployment (Streamlit Cloud, Docker, or any cloud provider)
- Session state management for multi-step workflows

### Key Python Libraries Needed
- **Scraping**: `requests`, `beautifulsoup4`, `selenium`/`playwright` (JS-rendered pages), `googlemaps` API
- **Data Processing**: `pandas`, `pydantic` for validation
- **Email Validation**: `email-validator`, DNS MX checks
- **AI/LLM**: OpenAI API or Anthropic Claude for text generation (outreach emails, segmentation)
- **Image Generation**: OpenAI DALL-E / Stability AI / Replicate for jersey design
- **Video Generation**: Replicate API (Runway, Stable Video Diffusion) or similar
- **Storage**: SQLite (MVP) -> PostgreSQL (production), S3 for media assets
- **Outreach**: SendGrid/Mailgun for email, Twilio for SMS

### Deployment Options
- **Streamlit Community Cloud** (free, limited resources)
- **Docker + any VPS** (DigitalOcean, AWS EC2, Fly.io)
- **Streamlit on Kubernetes** (for scale)

### Architecture Constraints with Streamlit
- Streamlit reruns entire script on interaction -> need session_state management
- Long-running tasks (scraping, AI generation) need async patterns / background jobs
- Multi-page app support via `st.navigation` (Streamlit 1.36+)
- File storage needs external service (S3, local filesystem, database)

## Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Scraping targets block/rate-limit | Proxies, rate limiting, respectful crawling |
| AI image quality inconsistent | Template-constrained generation, human review step |
| Video generation expensive/slow | Queue system, preview before full render |
| Email deliverability | Warming, domain rotation, compliance checks |
| Streamlit scaling limits | Background workers for heavy tasks, caching |
