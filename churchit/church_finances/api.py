# This source code is freely given for the sake of the gospel (Matthew 10:8)
# and is licensed under MIT No Attribution (MIT-0).

import io
import frappe
from frappe import _
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def download_year_end_statements_pdf(year=None, person_ids=None):
	"""
	Merge all Giving Statement print PDFs for a year into one combined PDF.
	Each statement is rendered via the 'Contribution Statement' print format.

	Args:
		year: Int, default = current year - 1
		person_ids: JSON list of person DocType names (optional; if omitted, all)

	Returns:
		Triggers a browser download of the merged PDF.
	"""
	try:
		from pypdf import PdfWriter
	except ImportError:
		frappe.throw(_("pypdf is not installed. Run: pip install pypdf"))

	year = int(year or (frappe.utils.now_datetime().year - 1))

	filters = {
		"year": year,
		"docstatus": ["<", 2],  # draft + submitted
	}

	if person_ids:
		person_ids = frappe.parse_json(person_ids) if isinstance(person_ids, str) else person_ids
		filters["person"] = ["in", person_ids]

	statements = frappe.get_all(
		"Giving Statement",
		filters=filters,
		pluck="name",
		order_by="name asc",
	)

	if not statements:
		frappe.throw(_("No giving statements found for year {0}").format(year))

	writer = PdfWriter()
	print_format = "Contribution Statement"

	for name in statements:
		try:
			html = frappe.get_print(
				"Giving Statement",
				name,
				print_format=print_format,
				as_pdf=False,
			)
			pdf_bytes = get_pdf(html)
			writer.append(io.BytesIO(pdf_bytes))
		except Exception as e:
			frappe.log_error(
				title="Giving Statement PDF render failed",
				message=f"Doc: {name}, Error: {str(e)}"
			)

	if not writer.pages:
		frappe.throw(_("No PDF pages could be generated."))

	out = io.BytesIO()
	writer.write(out)
	pdf_data = out.getvalue()

	frappe.local.response.filename = f"EOY-Giving-Statements-{year}.pdf"
	frappe.local.response.filecontent = pdf_data
	frappe.local.response.type = "application/pdf"
	frappe.local.response.disposition = "attachment"

	return frappe.local.response
