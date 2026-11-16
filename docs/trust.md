# Trust Layer — Ratings & Verification

**Module:** LetaFasta · API: `letafasta.letafasta.letafasta.api.rating`

## Supplier Verification Badge

`LF Organization.is_verified` is set manually by an admin after reviewing `licence_attachments` and TIN. It shows as a green "✓ Verified" chip on supplier tiles in the catalogue and on the supplier profile page. It is not affected by any automated logic.

## LF Rating

One rating per completed order, submitted by the buyer.

| Field | Type | Notes |
|---|---|---|
| `order` | Link → LF Order | Unique — one rating per order |
| `buyer` | Link → User | Auto-set from session |
| `supplier` | Link → LF Organization | From order |
| `quality_rating` | Rating (1–5) | |
| `punctuality_rating` | Rating (1–5) | |
| `communication_rating` | Rating (1–5) | |
| `overall_rating` | Float | Computed average of above three in `validate()` |
| `comment` | Small Text | |

**When the prompt appears:** `order.py` (portal context) sets `show_rating_prompt = True` when the viewer is the buyer, all non-cancelled loads are `collected`, and no LF Rating exists for the order. The order detail page shows an alert with a "Rate Supplier" link to `/letafasta/rate/<order>`.

**After collect redirect:** `confirm_collection` API returns `show_rating_prompt: True` when all loads are now collected; the order page JS then redirects to `/letafasta/rate/<order>` after a brief delay.

## avg_rating Recomputation

`LF Rating.after_insert()` and `on_update()` both call `_update_supplier_rating()`, which runs a qb query to compute `SUM(overall_rating) / COUNT(*)` over all ratings for the supplier, then writes `avg_rating` and `total_orders_completed` back to `LF Organization` via `frappe.db.set_value`.

## API Methods

| Method | Actor | Notes |
|---|---|---|
| `submit_rating(order, quality, punctuality, communication, comment)` | Buyer | Enforces one-per-order and completed status |
| `get_supplier_ratings(supplier, limit=10)` | Any auth | Returns recent ratings with buyer name |
