# Admin Desk & Platform Settings

**Module:** LetaFasta · Workspace: `LetaFasta Admin`

## LF Platform Settings (singleton)

Holds SMS/notification credentials only. No financial or escrow configuration.

| Field | Type |
|---|---|
| `sms_enabled` | Check |
| `rodsms_api_key` | Password |
| `rodsms_sender_id` | Data |
| `rodsms_base_url` | Data |
| `default_sms_language` | Select: en / sw |

Access via desk: `LetaFasta Admin → Trust & Settings → LF Platform Settings`.

## LetaFasta Admin Workspace

**Cannot be a fixture.** Frappe v16's `sync_fixtures()` calls full mandatory validation which raises `TypeError: strip_html(None)` when the workspace title is not set during import. The workspace must be created after migrate via bench console:

```python
ws = frappe.new_doc("Workspace")
ws.title = "LetaFasta Admin"
ws.module = "LetaFasta"
ws.is_standard = 1
ws.shortcuts = [...]  # see letafasta/letafasta/workspace/letafasta_admin.json.bak
ws.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
frappe.db.commit()
```

The workspace JSON is kept in `letafasta/letafasta/workspace/letafasta_admin.json.bak` as reference but is NOT loaded by fixtures or sync_all.

## Sidebar & Navigation (v16)

The app's sidebar is at `letafasta/letafasta/sidebar/LetaFasta/LetaFasta.json` and the dock entry is at `letafasta/dock/letafasta/letafasta.json`. These are synced automatically on `bench migrate`.

The `add_to_apps_screen` entry in `hooks.py` has **no `route`** field. Setting `route` to a bare module path causes "Page not found" on v16. The client falls through to the Dock's first Sidebar entry instead.

## role_home_page

| Role | Redirect |
|---|---|
| `LF Admin` | `app/letafasta-admin` (desk workspace) |
| `LF Buyer` | `letafasta/orders` |
| `LF Supplier Owner` | `letafasta/supplier` |
| `LF Supplier Staff` | `letafasta/my-orders` |

## Scheduler Jobs

Both jobs run via `run_scheduled_jobs()` on Frappe's "all" interval (≈15 min):

- **`expire_orders()`**: finds confirmed orders past `expires_at` with no active loads → cancelled + stock restored. Uses qb with `.notin()` subquery to find orders that have no booked/active loads.
- **`expire_rfqs()`**: bulk-sets open/quoted RFQs past `expires_at` to expired in one qb UPDATE.
- **`flush_sms_queue()`**: runs every minute; Phase 6 stub that checks `sms_enabled`.
