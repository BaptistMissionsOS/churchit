# This source code is freely given for the sake of the gospel (Matthew 10:8)
# and is licensed under MIT No Attribution (MIT-0).

import frappe
from frappe.tests.utils import FrappeTestCase

class TestGivingStatement(FrappeTestCase):
	def test_generate_and_merge(self):
		"""Smoke test: create a statement, render PDF, merge."""
		# Create a test person (Donor)
		person = frappe.get_doc({
			"doctype": "Person",
			"first_name": "Test",
			"last_name": "Donor",
		}).insert(ignore_permissions=True)

		# Create a test fund
		fund_name = "General Test Fund"
		if not frappe.db.exists("Fund", fund_name):
			frappe.get_doc({
				"doctype": "Fund",
				"fund": fund_name,
				"is_tax_deductible": 1
			}).insert(ignore_permissions=True)

		# Create a test collection and donation
		collection = frappe.get_doc({
			"doctype": "Collection",
			"date": "2025-06-15 00:00:00",
			"expected_total": 500.00,
			"donations": [
				{
					"fund": fund_name,
					"amount": 500.00,
					"person": person.name,
					"currency": "USD"
				}
			]
		}).insert(ignore_permissions=True)
		collection.submit()

		# Generate statement
		from churchit.church_finances.doctype.giving_statement.giving_statement import generate_statements_for_year
		result = generate_statements_for_year(year=2025, person_ids=[person.name])
		self.assertGreaterEqual(result["created"], 1)

		# Verify statement exists
		stmt = frappe.get_doc("Giving Statement", {
			"person": person.name,
			"year": 2025
		})
		self.assertEqual(stmt.total_amount, 500.00)
		self.assertEqual(stmt.gift_count, 1)

		# Test merging API
		from churchit.church_finances.api import download_year_end_statements_pdf
		response = download_year_end_statements_pdf(year=2025, person_ids=[person.name])
		self.assertIsNotNone(response.filecontent)

		# Clean up
		stmt.delete()
		collection.cancel()
		collection.delete()
		person.delete()
