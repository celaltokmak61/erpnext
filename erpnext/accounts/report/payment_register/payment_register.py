# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "posting_date", "label": _("Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "voucher_type", "label": _("Type"), "fieldtype": "Data", "width": 130},
		{
			"fieldname": "voucher_no",
			"label": _("Document"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180,
		},
		{"fieldname": "payment_type", "label": _("Payment Type"), "fieldtype": "Data", "width": 110},
		{"fieldname": "party_type", "label": _("Party Type"), "fieldtype": "Data", "width": 100},
		{
			"fieldname": "party",
			"label": _("Party"),
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			"width": 180,
		},
		{"fieldname": "party_name", "label": _("Party Name"), "fieldtype": "Data", "width": 180},
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 180,
		},
		{"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency", "width": 130},
		{
			"fieldname": "mode_of_payment",
			"label": _("Mode of Payment"),
			"fieldtype": "Link",
			"options": "Mode of Payment",
			"width": 140,
		},
		{"fieldname": "reference_no", "label": _("Reference No"), "fieldtype": "Data", "width": 140},
		{"fieldname": "remarks", "label": _("Remarks"), "fieldtype": "Data", "width": 200},
	]


def get_data(filters):
	data = []
	data += get_payment_entries(filters)
	data += get_journal_entries(filters)
	data.sort(key=lambda x: getdate(x.get("posting_date")), reverse=True)
	return data


def get_payment_entries(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND pe.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND pe.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND pe.posting_date <= %(to_date)s"
	if filters.get("party_type"):
		conditions += " AND pe.party_type = %(party_type)s"
	if filters.get("party"):
		conditions += " AND pe.party = %(party)s"
	if filters.get("payment_type") and filters.get("payment_type") != "All":
		if filters.get("payment_type") == "Incoming":
			conditions += " AND pe.payment_type = 'Receive'"
		elif filters.get("payment_type") == "Outgoing":
			conditions += " AND pe.payment_type = 'Pay'"

	return frappe.db.sql(
		"""
		SELECT
			pe.posting_date,
			'Payment Entry' AS voucher_type,
			pe.name AS voucher_no,
			pe.payment_type,
			pe.party_type,
			pe.party,
			pe.party_name,
			CASE
				WHEN pe.payment_type = 'Pay' THEN pe.paid_from
				ELSE pe.paid_to
			END AS account,
			pe.paid_amount AS amount,
			pe.mode_of_payment,
			pe.reference_no,
			pe.remarks
		FROM `tabPayment Entry` pe
		WHERE pe.docstatus = 1
		{conditions}
		ORDER BY pe.posting_date DESC
		""".format(conditions=conditions),
		filters,
		as_dict=True,
	)


def get_journal_entries(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND je.company = %(company)s"
	if filters.get("from_date"):
		conditions += " AND je.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		conditions += " AND je.posting_date <= %(to_date)s"
	if filters.get("party_type"):
		conditions += " AND jea.party_type = %(party_type)s"
	if filters.get("party"):
		conditions += " AND jea.party = %(party)s"

	return frappe.db.sql(
		"""
		SELECT
			je.posting_date,
			'Journal Entry' AS voucher_type,
			je.name AS voucher_no,
			je.voucher_type AS payment_type,
			jea.party_type,
			jea.party,
			'' AS party_name,
			jea.account,
			ABS(jea.credit - jea.debit) AS amount,
			je.mode_of_payment,
			je.cheque_no AS reference_no,
			je.remark AS remarks
		FROM `tabJournal Entry` je
		INNER JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
		WHERE je.docstatus = 1
			AND je.voucher_type IN ('Bank Entry', 'Cash Entry', 'Contra Entry')
			AND jea.party_type IS NOT NULL
			AND jea.party_type != ''
		{conditions}
		ORDER BY je.posting_date DESC
		""".format(conditions=conditions),
		filters,
		as_dict=True,
	)