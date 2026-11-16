# Catalogue & Products

**Module:** LetaFasta · Portal: `/letafasta/catalogue`

## LF Product

| Field | Type | Notes |
|---|---|---|
| `product_name` | Data | Unique |
| `supplier` | Link → LF Organization | |
| `unit_label` | Data | e.g. "bag", "tonne" |
| `unit_price` | Currency | Listed/suggested price; negotiable via RFQ |
| `unit_weight_kg` | Int | Used for freight rate calculation and load share allocation |
| `stock_quantity` | Int | Soft-reserved on direct order creation; restored on cancel/expiry |
| `is_active` | Check | Only active products appear in catalogue |
| `image` | Attach Image | |

**Stock guard:** `validate()` raises if `stock_quantity < 0`. Direct order creation raises before saving if the resulting stock would go negative.

## LF Freight Rate (child of LF Organization)

| Field | Type |
|---|---|
| `hub` | Link → LF Hub |
| `rate_per_tonne` | Currency |

Suppliers add one row per hub they deliver to. The catalogue query sorts by `is_verified DESC, avg_rating DESC` so verified high-rated suppliers appear first.

## Portal Pages

| URL | File | Notes |
|---|---|---|
| `/letafasta/catalogue` | `catalogue.py` | Product grid; qb JOIN on LF Organization for badge + rating |
| `/letafasta/product/<id>` | `product.py` | Product detail; Add to Cart (localStorage) + RFQ link |
| `/letafasta/cart` | `cart.py` | Cart grouped by supplier (localStorage-based) |
| `/letafasta/checkout` | `checkout.py` | Hub picker; direct order or RFQ path |
| `/letafasta/supplier-profile/<id>` | `supplier-profile.py` | Public supplier page: products, avg rating, reviews |

## Supplier Product Management

Suppliers manage their products from the desk (`/app/lf-product`). The portal page `/letafasta/my-products` shows the list with an "Edit in Desk" link. Stock quantities are updated by the platform when orders are placed or cancelled; suppliers should not edit stock directly except to correct physical inventory.
