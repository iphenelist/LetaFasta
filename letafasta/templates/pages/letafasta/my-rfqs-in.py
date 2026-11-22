import frappe


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/letafasta/my-rfqs-in"
        raise frappe.Redirect

    supplier_org = frappe.db.sql("""
        SELECT parent FROM `tabLF Organization Member`
        WHERE user = %s AND parenttype = 'LF Organization' LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    if not supplier_org:
        frappe.local.flags.redirect_location = "/letafasta/onboarding"
        raise frappe.Redirect

    supplier_name = supplier_org[0].parent

    rfqs = frappe.db.sql("""
        SELECT r.name, r.rfq_title, r.quantity, r.unit_label, r.expires_at,
               r.budget_per_unit, r.preferred_date,
               p.product_name,
               r.product_description,
               h.hub_name,
               CASE WHEN q.name IS NOT NULL THEN 1 ELSE 0 END AS already_quoted
        FROM `tabLF RFQ` r
        LEFT JOIN `tabLF Product` p ON p.name = r.product
        LEFT JOIN `tabLF Hub` h ON h.name = r.hub
        LEFT JOIN `tabLF RFQ Quote` q
            ON q.rfq = r.name AND q.supplier = %(supplier)s
            AND q.status NOT IN ('rejected','expired')
        WHERE r.status IN ('open','quoted')
          AND r.expires_at > NOW()
        ORDER BY r.creation DESC
        LIMIT 50
    """, {"supplier": supplier_name}, as_dict=True)

    context.rfqs = rfqs
    context.no_cache = 1
