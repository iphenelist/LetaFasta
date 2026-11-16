# RFQ & Price Negotiation

**Module:** LetaFasta · API: `letafasta.letafasta.letafasta.api.rfq`

## Flow

```
Buyer posts RFQ (open)
  → Suppliers see it at /letafasta/my-rfqs-in
  → Each supplier submits one LF RFQ Quote (RFQ moves to quoted)
  → Buyer compares quotes at /letafasta/rfq/<id>
  → Buyer accepts one quote
  → Other quotes → rejected; RFQ → accepted
  → LF Order created from accepted quote
```

A buyer can also post an RFQ from checkout when their cart total is not at a fixed price — the checkout page offers a "Post RFQ" path alongside the direct order path.

## LF RFQ

| Field | Type | Notes |
|---|---|---|
| `rfq_title` | Data | Auto-set to doc name after insert |
| `buyer` | Link → User | Set from session on insert |
| `product` | Link → LF Product | Optional — buyer may describe a free-text product |
| `product_description` | Data | Used when no product link |
| `quantity` | Int | |
| `hub` | Link → LF Hub | Delivery destination |
| `budget_per_unit` | Currency | Optional ceiling price (not enforced) |
| `status` | Select | `open` / `quoted` / `accepted` / `expired` / `cancelled` |
| `expires_at` | Datetime | 24h from creation; set by `before_insert` |
| `accepted_quote` | Link → LF RFQ Quote | Set by `accept_quote` API |

**Expiry:** `tasks.expire_rfqs()` runs every 15 min via `run_scheduled_jobs`. It sets open/quoted RFQs past `expires_at` to `expired` using a single qb UPDATE.

## LF RFQ Quote

| Field | Type | Notes |
|---|---|---|
| `rfq` | Link → LF RFQ | |
| `supplier` | Link → LF Organization | Auto-detected from session user's org membership |
| `price_per_unit` | Currency | |
| `total_price` | Currency | Computed: `price_per_unit × rfq.quantity` in `validate()` |
| `delivery_lead_days` | Int | |
| `valid_until` | Datetime | +48h if not set |
| `status` | Select | `submitted` / `accepted` / `rejected` / `expired` |

**Duplicate prevention:** `submit_quote` checks for an existing non-rejected/expired quote from the same supplier before inserting.

## API Methods

| Method | Actor | Action |
|---|---|---|
| `post_rfq` | Buyer | Create LF RFQ; requires `LF RFQ` create permission |
| `submit_quote` | Supplier | Create LF RFQ Quote; deduplicates per supplier |
| `accept_quote` | Buyer | Reject siblings, accept quote, create LF Order |
| `cancel_rfq` | Buyer | Cancel open/quoted RFQ; rejects submitted quotes |
| `get_rfq_quotes` | Buyer | Return all quotes for an RFQ, sorted by price asc |
| `get_open_rfqs` | Supplier | Return open/quoted RFQs for browsing |
