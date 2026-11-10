# This source code is freely given for the sake of the gospel (Matthew 10:8)
# and is licensed under MIT No Attribution (MIT-0).

import frappe
from frappe.model.document import Document

class GivingStatement(Document):
	def before_save(self):
		self.calculate_totals()

	def calculate_totals(self):
		self.total_amount = sum(
			d.amount for d in self.get("gifts")
		)
		self.gift_count = len(self.get("gifts"))


def statement_header(church=None):
	return {
		"name": frappe.db.get_single_value("Churchit Settings", "church_name") or "Church Name",
		"tax_id": "",
		"address": frappe.db.get_single_value("Churchit Settings", "church_address") or "",
		"acknowledgment": ""
	}



@frappe.whitelist()
def generate_statements_for_year(year=None, person_ids=None):
	"""
	Bulk-generate Giving Statements for all donors who gave in the given year.
	Called from a button in the Giving Statement list view or via desk action.
	"""
	year = int(year or frappe.utils.now_datetime().year - 1)

	# Find all donors who have at least one donation in the year
	donor_query = """
		SELECT DISTINCT d.person
		FROM `tabDonation` d
		WHERE YEAR(d.posting_date) = %s
		  AND d.docstatus = 1
		  AND d.person IS NOT NULL
	"""
	# TODO: verify field names (person, posting_date, docstatus)

	if person_ids:
		person_ids = frappe.parse_json(person_ids) if isinstance(person_ids, str) else person_ids
		donors = person_ids
	else:
		donors = [r[0] for r in frappe.db.sql(donor_query, (year,), as_dict=False)]

	created = 0
	skipped = 0

	for donor in donors:
		# Skip if statement already exists for this person+year
		existing = frappe.db.exists("Giving Statement", {
			"person": donor,
			"year": year
		})
		if existing:
			skipped += 1
			continue

		# Gather all donations for this person in the year
		donations = frappe.get_all(
			"Donation",
			filters={
				"person": donor,
				"docstatus": 1,
				"posting_date": ["between",
					frappe.utils.get_first_day(frappe.utils.get_year_start(year)),
					frappe.utils.get_year_end(year)
				]
			},
			fields=["name", "posting_date", "amount", "fund", "mode_of_payment"],
			order_by="posting_date asc"
		)

		if not donations:
			skipped += 1
			continue

		doc = frappe.new_doc("Giving Statement")
		doc.person = donor
		doc.year = year

		for d in donations:
			doc.append("gifts", {
				"donation": d.name,
				"date": d.posting_date,
				"fund": d.fund,
				"amount": d.amount,
				"method": d.mode_of_payment,
			})

		doc.insert(ignore_permissions=True)
		created += 1

	frappe.db.commit()
	frappe.msgprint(
		f"Generated {created} statements. Skipped {skipped} (already existed or no gifts)."
	)
	return {"created": created, "skipped": skipped}
