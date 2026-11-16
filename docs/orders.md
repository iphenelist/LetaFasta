# Orders & Load Logistics

**Module:** LetaFasta · API: `letafasta.letafasta.letafasta.api.order` + `api.load`

## Order Lifecycle

```
confirmed (24h clock starts)
  → supplier calls plan_loads → in_progress
  → supplier adds transport details → load: booked
  → supplier marks departed → load: departed
  → supplier marks arrived → load: arrived
  → buyer confirms collection → load: collected
  → all loads collected → order: completed
  → buyer sees rating prompt
```

## LF Order

| Field | Type | Notes |
|---|---|---|
| `buyer` | Link → User | |
| `supplier` | Link → LF Organization | |
| `hub` | Link → LF Hub | |
| `rfq` | Link → LF RFQ | null for direct/catalogue orders |
| `status` | Select | `confirmed` / `in_progress` / `partly_collected` / `completed` / `cancelled` |
| `agreed_price` | Currency | From RFQ quote or direct catalogue price |
| `total_weight_kg` | Int | Sum of all items' weight |
| `rate_per_tonne` | Currency | Freight rate used for reference |
| `payment_recorded` | Check | Buyer or supplier marks payment received off-platform |
| `expires_at` | Datetime | 24h from creation; stock held until then |
| `items` | Table → LF Order Item | Snapshot of product + price at order time |

**24h expiry (stock hold):** `tasks.expire_orders()` queries orders where `status = confirmed`, `expires_at < now`, and no load is in an active state (booked/departed/arrived/collected). Those orders are set to cancelled and their stock quantities are restored via qb UPDATE.

**Two order paths:**
1. **Direct (catalogue price):** `create_order(cart_json, hub)` groups cart items by supplier, creates one LF Order per supplier, soft-reserves stock (raises if insufficient).
2. **RFQ path:** `accept_quote(quote_name)` calls `_create_order_from_quote()`.

## LF Load

One truck dispatch within an order.

| Field | Type | Notes |
|---|---|---|
| `label` | Data | Auto-labelled "Truck A", "Truck B", … |
| `order` | Link → LF Order | |
| `status` | Select | `planned` / `booked` / `departed` / `arrived` / `collected` / `cancelled` |
| `weight_kg` | Int | |
| `share_amount` | Currency | This truck's portion of `agreed_price`, computed by largest-remainder |
| `plate_number`, `driver_name`, `driver_phone` | Data | Required when status ≥ booked |
| `waybill_no`, `waybill_file` | Data / Attach | |
| `departed_at`, `arrived_at`, `confirmed_at` | Datetime | Set by status transitions |

**Share allocation:** `_allocate_shares(agreed_price, weights, total_weight)` distributes `agreed_price` proportional to `weight_kg` using the largest-remainder algorithm so shares sum exactly to `agreed_price`.

**Valid transitions:** `planned → booked/cancelled`, `booked → departed/cancelled`, `departed → arrived`, `arrived → collected`. `confirm_collection` is the only path to `collected`; it checks for open LF Issue records blocking the load.

## API Methods

| Method | Actor | Action |
|---|---|---|
| `plan_loads(order, loads_json)` | Supplier | Create LF Load records; moves order to in_progress |
| `add_transport_details(load, ...)` | Supplier | Set plate/driver; moves load to booked |
| `update_load_status(load, new_status)` | Supplier | Advance load status |
| `confirm_collection(load)` | Buyer | Mark load collected; triggers order status refresh |
| `cancel_order(order, reason)` | Buyer/Supplier | Cancel if no loads in transit; restores stock |
| `reorder(order)` | Buyer | Clone completed order items to cart JSON |
| `mark_payment_received(order)` | Buyer/Supplier | Set payment_recorded flag |

## Order Status Refresh

`_refresh_order_status(order_name)` is called after every load status change. Logic:
- All active loads collected → `completed`
- Some collected → `partly_collected`
- Any departed/arrived → `in_progress`
