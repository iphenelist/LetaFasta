# LetaFasta

B2B bulk-materials procurement and last-mile freight marketplace for Tanzania. Buyers discover cement, grain and building-material suppliers, negotiate via RFQ or buy at catalogue price, and track truck-by-truck delivery to named collection hubs. Payment is off-platform.

**Frappe v16 · standalone (no ERPNext)**

## Docs

| Area | File |
|---|---|
| Organisations & onboarding | [docs/organisations.md](docs/organisations.md) |
| Catalogue & products | [docs/catalogue.md](docs/catalogue.md) |
| RFQ & price negotiation | [docs/rfq.md](docs/rfq.md) |
| Orders & load logistics | [docs/orders.md](docs/orders.md) |
| Trust layer (ratings) | [docs/trust.md](docs/trust.md) |
| Admin desk & platform settings | [docs/admin.md](docs/admin.md) |

## Roles

| Role | Who |
|---|---|
| `LF Admin` | Letapro staff — full desk + portal |
| `LF Buyer` | Buyers — portal only |
| `LF Supplier Owner` | Supplier org owner — portal supplier view |
| `LF Supplier Staff` | Supplier staff — portal read |

## Development

```bash
# New site
bench new-site letafasta.localhost --install-app letafasta

# Migrate
bench --site letafasta.localhost migrate

# Create Admin workspace (must run after migrate — cannot be a fixture)
bench --site letafasta.localhost console
# >>> from letafasta.setup import create_workspace; create_workspace()
```

## Scheduler

| Job | Interval | Function |
|---|---|---|
| Expire orders | every 15 min | `tasks.expire_orders` |
| Expire RFQs | every 15 min | `tasks.expire_rfqs` |
| Flush SMS queue | every 1 min | `tasks.flush_sms_queue` (Phase 6) |
