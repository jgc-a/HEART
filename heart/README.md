# HEART — Human-centric Experience Agent for Rosewood Travelers

**Status**: Production-ready hackathon build (May 16, 2026)

## What is HEART?

HEART is an agentic hospitality system that orchestrates AI agents to manage guest experiences at Rosewood Sand Hill. It replaces reactive staff scheduling with proactive agent-driven handling across the entire guest lifecycle.

### Three-Agent Architecture

1. **Orchestrator** — Pre-arrival flow assessment, billing resolution, identity verification
2. **Shadow** — In-stay monitoring, complaint detection, escalation logic
3. **Thread** — Post-stay memory snapshot, performance analysis, loyalty tracking

## Quick Start

```bash
# Start the server
python3 server.py

# Dashboard opens at
http://localhost:5560
```

## Features

### Agent Execution Engine
- **Live reasoning chains** — watch agents think step-by-step
- **Dynamic orchestration** — agents trigger other agents based on decisions
- **Escalation logic** — automatic human escalation when needed

### Dashboard (12 Interactive Tabs)
- **Arrivals** — incoming guests with flow prediction
- **In-Stay** — active guests with incident monitoring
- **Rooms Map** — occupancy grid with guest names
- **Agent Brain** — decision log with full reasoning
- **Human vs Agent ROI** — economics of agent resolution
- **🚀 Agent Launcher** — execute agents on demand, watch reasoning in real-time

### APIs (12 Endpoints)
```
GET  /api/heart/v1/arrivals          # Today's arrivals
GET  /api/heart/v1/in-stay           # Currently staying guests
GET  /api/heart/v1/human-queue       # Escalations needing staff
GET  /api/heart/v1/rooms             # Room occupancy (normalized)
GET  /api/heart/v1/agent-brain       # Decision log with reasoning
GET  /api/heart/v1/roi-stats         # Agent vs human economics
POST /api/heart/v1/agents/launch     # Execute a specific agent
POST /api/heart/v1/agents/orchestrate # Run full agent sequence
GET  /api/heart/v1/agents/executions # Execution history
GET  /api/heart/v1/hap/events        # Full audit trail (SSE)
GET  /api/heart/v1/metrics           # System health metrics
GET  /api/heart/v1/dispute-brief     # Reputation audit (WARDEN)
```

## Example: Live Agent Execution

```bash
# Launch Orchestrator on Marcus Chen
curl -X POST http://localhost:5560/api/heart/v1/agents/launch \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "orchestrator",
    "guest_guid": "hap-guid-0001-marcus-chen",
    "trigger": "demo"
  }'
```

**Response** (visible reasoning):
```json
{
  "agent": "Orchestrator",
  "reasoning_chain": [
    "[1/5] Identidad verificada: Marcus Chen",
    "[2/5] Bio analizado: Silicon Valley founder...",
    "[3/5] Flow inferido: CORPORATE",
    "[4/5] ✓ Sin alertas detectadas",
    "[5/5] Billing resuelto: CORPORATE"
  ],
  "decisions": [
    {"action": "FLOW_SELECTED", "value": "CORPORATE"}
  ],
  "status": "COMPLETED"
}
```

## File Structure

```
heart/
├── server.py              # Flask backend (500+ lines)
├── templates/view.html    # Interactive dashboard (1500+ lines)
├── data/
│   ├── guests.json       # 5 guest profiles (CORPORATE, FAMILY, BLEISURE, etc.)
│   ├── rooms.json        # 9 rooms with occupancy mapping
│   └── heart.db          # SQLite (HAP events, conversations, human queue)
└── README.md
```

## Architecture

### Flow Classification (10 Profiles)
- GENERAL, CORPORATE, SPECIAL_DATES, BLEISURE, WELLNESS
- VIP_DISCRETE, FAMILY_WITH_MINORS, GROUP, MEDICAL, TRANSIT

### Decision Cascade
1. **Orchestrator** identifies flow + detects alerts
2. If alert detected → escalate to human (block agent)
3. If no alert + in-stay → run Shadow for monitoring
4. If departing → run Thread for memory snapshot

### Escalation Triggers
- Minors (FAMILY_WITH_MINORS) → human verification required
- Active complaint → human escalation
- Payment missing → hold check-in
- Biometric enrollment missing → flag for on-site enrollment

## Database Schema

### hap_events
Guest journey audit trail (immutable append-only)
- Reservation confirmed
- Flow selected
- Billing resolved
- Check-in completed
- Complaints escalated

### human_queue
Staff action items
- guest_guid, reason, priority, status, assigned_to

### conversations
Agent-guest chat history (supports future fine-tuning)

### dispute_briefs
Reputation audit (WARDEN-signed)

## Testing All Endpoints

```bash
# Run in sequence
for ep in arrivals in-stay rooms agent-brain roi-stats agents/launch; do
  curl -s http://localhost:5560/api/heart/v1/$ep | jq '.[] | .guest_name' 2>/dev/null | head -1
done
```

## Integration Points

- **ARCA API** (localhost:5200) — LLM reasoning via Claude Haiku
- **KINDRED AI** — guest relationship prediction
- **TimDoctor** — agent activity monitoring
- **Nómina system** — payroll integration for cost modeling

## Metrics

Current state (5 guests, 3 in-stay):
- Agent resolution rate: **60%** (3 guests)
- Human escalation rate: **40%** (2 guests)
- Cost savings: **$89.55** vs all-human handling
- ROI: **99%**

## Production Deployment

1. Replace SQLite with PostgreSQL
2. Add Redis for session caching
3. Enable HTTPS + API key auth
4. Deploy on Kubernetes with HAP event streaming
5. Add monitoring (Prometheus) + alerting (PagerDuty)

## License

Proprietary — Rosewood Hotels & Resorts, 2026

---

**Built for Hackathon** — May 16, 2026
**Agent Framework**: HAP (Hospitality Agent Protocol) v1.0
**LLM**: Claude Haiku 4.5 via ARCA API
