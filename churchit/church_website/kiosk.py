# This source code is freely given for the sake of the gospel (Matthew 10:8)
# and is licensed under MIT No Attribution (MIT-0).

"""Data for the kiosk SPA. Each endpoint reads only and is open to guests, because the website is."""

import frappe
from frappe import _
from frappe.website.utils import get_portal_sidebar_items

from churchit.church_foundations.doctype.church.church import church_contact_details, get_church
from churchit.church_ministries.doctype.function_sign_up.function_sign_up import (
	WINDOW_FIELDS,
	is_in_sign_up_window,
)
from churchit.church_scope import church_filters, selected_church_filters, session_church, session_person
from churchit.church_website.pages import get_switched_off_pages, is_link_off
from churchit.church_website.portal_home import get_portal_home_sections


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_home_data() -> dict:
	"""Everything the kiosk home page shows: church, menu, hero, stats, upcoming functions and latest sermon. Reads only."""
	church = get_church()
	off_pages = get_switched_off_pages()
	return {
		"church": _church_payload(church),
		"menu": _menu(off_pages),
		"upcoming": _upcoming_functions(),
		"latest_sermon": _latest_sermon(off_pages),
		"stats": _stats(church, off_pages),
		"off_pages": sorted(off_pages),
		"user": frappe.session.user,
	}


def _church_payload(church) -> dict | None:
	"""The fields the hero and the next-gathering card show for *church*."""
	if not church:
		return None
	address_line = ""
	if church.address:
		addr = frappe.get_cached_doc("Address", church.address)
		address_line = ", ".join(part for part in (addr.address_line1, addr.city, addr.state) if part)
	return {
		"name": church.name,
		"church_name": church.church_name,
		"mission_statement": church.mission_statement,
		"about": church.about,
		"address_line": address_line,
		"phone": church_contact_details(church).phone,
	}


def _menu(off_pages: set[str]) -> list[dict]:
	"""Website Settings top bar as a tree of ``{label, url, children}``, with switched-off links dropped."""
	settings = frappe.get_cached_doc("Website Settings")
	rows = list(settings.top_bar_items)
	by_parent: dict[str, list[dict]] = {}
	for row in rows:
		if not row.parent_label:
			continue
		if is_link_off(row.url, off_pages):
			continue
		by_parent.setdefault(row.parent_label, []).append({"label": row.label, "url": row.url})

	items = []
	for row in rows:
		if row.parent_label:
			continue
		children = by_parent.get(row.label, [])
		if is_link_off(row.url, off_pages) and not children:
			continue
		items.append({"label": row.label, "url": row.url, "children": children})
	return items


def _upcoming_functions() -> list[dict]:
	"""The next four published functions in the selected church, soonest first."""
	return frappe.get_all(
		"Function",
		fields=[
			"name",
			"function_name",
			"title",
			"start_date",
			"start_time",
			"all_day",
			"description",
		],
		filters=selected_church_filters(
			publish=1,
			is_link_only=0,
			auto_repeat=0,
			start_date=[">=", frappe.utils.nowdate()],
		),
		order_by="start_date asc, start_time asc",
		limit=4,
	)


def _latest_sermon(off_pages: set[str]) -> dict | None:
	"""The most recent published sermon in the selected church, or None while sermons are off."""
	if "sermons" in off_pages:
		return None
	rows = frappe.get_all(
		"Sermon",
		fields=["name", "title", "notes", "handout", "audio_recording", "prepared_by", "sermon_date"],
		filters=selected_church_filters(publish=1),
		order_by="sermon_date desc, modified desc",
		limit=1,
	)
	if not rows:
		return None
	sermon = rows[0]
	if sermon.get("prepared_by"):
		sermon["prepared_by_name"] = frappe.db.get_value("Person", sermon["prepared_by"], "full_name")
	return sermon


def _stats(church, off_pages: set[str]) -> list[dict]:
	"""Years serving, ministries, missionaries and sermons for the selected church, each with a lucide icon slug. Zeros are dropped."""
	sermons_on = "sermons" not in off_pages
	years = 0
	if church and church.founding_date:
		years = frappe.utils.date_diff(frappe.utils.nowdate(), church.founding_date) // 365
	numbers = [
		(years, _("Years serving"), "heart"),
		(frappe.db.count("Ministry", selected_church_filters(publish=1)), _("Ministries"), "users"),
		(
			frappe.db.count("Missionary", selected_church_filters(publish=1)),
			_("Missionaries supported"),
			"globe",
		),
		(
			frappe.db.count("Sermon", selected_church_filters(publish=1)) if sermons_on else 0,
			_("Sermons online"),
			"book-open",
		),
	]
	return [{"number": number, "label": label, "icon": icon} for number, label, icon in numbers if number]


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_portal_data() -> dict:
	"""The member portal view: church, menu, sections and whether the reader is signed in. Reads only."""
	church = get_church()
	off_pages = get_switched_off_pages()
	is_signed_in = frappe.session.user != "Guest"
	items = [item for item in get_portal_sidebar_items() if not is_link_off(item.get("route"), off_pages)]
	sections = []
	for section in get_portal_home_sections(items):
		links = []
		for link in section.links:
			route = link.route if link.route.startswith("/") else "/" + link.route
			links.append(
				{
					"title": _(link.title) if link.title else "",
					"route": route,
					"icon": link.icon or "link",
					"description": link.description or "",
				}
			)
		if links:
			sections.append({"title": section.title, "links": links})
	return {
		"church": _church_payload(church),
		"menu": _menu(off_pages),
		"off_pages": sorted(off_pages),
		"signed_in": is_signed_in,
		"welcome_name": frappe.utils.get_fullname(frappe.session.user) if is_signed_in else "",
		"sections": sections,
		"connection_card_on": "connection-card" not in off_pages,
		"contact_on": "contact" not in off_pages,
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_function_sign_up_data() -> dict:
	"""The function sign-up view: open functions and whether the reader is signed in. Reads only."""
	church = get_church()
	off_pages = get_switched_off_pages()
	is_signed_in = frappe.session.user != "Guest"
	return {
		"church": _church_payload(church),
		"menu": _menu(off_pages),
		"off_pages": sorted(off_pages),
		"signed_in": is_signed_in,
		"person": session_person() if is_signed_in else None,
		"functions": _open_sign_up_functions() if is_signed_in else [],
		"intro": _("Sign up to let us know you plan to attend an upcoming function."),
		"success_message": _("You are signed up. Your sign-ups list shows the status."),
	}


def _open_sign_up_functions() -> list[dict]:
	"""The functions in the selected church that are open for sign-up right now and have no selection or question set."""
	rows = frappe.get_all(
		"Function",
		filters=church_filters(session_church(), allow_sign_ups=1, is_link_only=0),
		fields=[
			"name",
			"function_name",
			"title",
			"start_date",
			"start_time",
			"end_date",
			"end_time",
			"all_day",
			"description",
			"question_set",
			*WINDOW_FIELDS,
		],
		order_by="start_date asc, start_time asc",
	)
	with_selections = set(
		frappe.get_all(
			"Function Sign-Up Selection",
			filters={"parenttype": "Function", "parent": ("in", [row.name for row in rows])},
			pluck="parent",
		)
	)
	today = frappe.utils.getdate()
	return [
		{
			"name": row.name,
			"function_name": row.function_name or row.title,
			"start_date": row.start_date,
			"start_time": row.start_time,
			"all_day": row.all_day,
			"description": row.description,
		}
		for row in rows
		if is_in_sign_up_window(row)
		and not row.question_set
		and row.name not in with_selections
		and (not row.start_date or row.start_date >= today)
	]
