# Organisations & Onboarding

**Module:** LetaFasta · Sidebar section: Organisations

## LF Organization

The central identity record for every actor on the platform. One user may belong to multiple organisations.

| Field | Type | Notes |
|---|---|---|
| `org_name` | Data | Display name |
| `type` | Select | `supplier` / `transporter` / `hub_operator` / `letapro` |
| `status` | Select | `pending` → `approved` → `suspended` |
| `is_verified` | Check | Set by admin after KYC review; shows green "✓ Verified" badge in catalogue |
| `avg_rating` | Float | Recomputed by `LF Rating` controller after every rating |
| `total_orders_completed` | Int | Counts of ratings (proxy for completed orders) |
| `commission_rate` | Float | Supplier margin %, informational |
| `freight_rates` | Table → LF Freight Rate | Per-hub transport rate used by order pricing |
| `members` | Table → LF Organization Member | user + role (owner/staff/driver/hub_manager) |
| `licence_attachments` | Table → LF Organization Licence | KYC documents |

**Workflow:** `pending → approved → suspended` — LF Admin only. Defined in `fixtures/workflow.json`; upserted on every migrate.

**Important:** The workspace (`LetaFasta Admin`) is not a fixture. It must be created via `bench console` after migrate because Frappe's `sync_fixtures()` calls full mandatory validation which rejects Workspace records with no title. See README for the console command.

## LF Hub

A named collection hub where buyers receive goods.

| Field | Type |
|---|---|
| `hub_name` | Data |
| `region` | Data |
| `is_active` | Check |
| `latitude`, `longitude` | Float |

## Onboarding Flow

Portal page `/letafasta/onboarding`. A logged-in user with no LF role lands here automatically (enforced by `index.py` redirect logic).

- **Join as Buyer** → calls `api/onboarding.set_buyer_role()` → grants `LF Buyer`, redirects to `/letafasta/catalogue`.
- **Register as Supplier** → links to `/letafasta/onboarding/supplier` (Phase 2 form or desk). Calls `api/onboarding.register_supplier()` → creates LF Organization (status=pending), grants `LF Supplier Owner`. Supplier can use the portal but not list products until admin approves.

## Admin Actions

After a supplier registers, the admin approves via the LF Organization approval workflow from the desk (`LetaFasta Admin` workspace → LF Organization list). After approval the admin may set `is_verified = 1` to show the badge once KYC docs are reviewed.
