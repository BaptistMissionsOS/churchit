frappe.ui.form.on("Giving Statement", {
	refresh(frm) {
		// "Generate for Year" button on the form
		if (frm.doc.__islocal) {
			frm.add_custom_button(__("Generate for Year"), () => {
				frappe.prompt(
					[
						{
							label: __("Year"),
							fieldname: "year",
							fieldtype: "Int",
							default: new Date().getFullYear() - 1,
							reqd: 1
						}
					],
					(values) => {
						frappe.call({
							method: "churchit.church_finances.doctype.giving_statement.giving_statement.generate_statements_for_year",
							args: { year: values.year },
							freeze: true,
							callback: (r) => {
								frappe.show_alert({
									message: __("Generated {0} statements", [r.message?.created || 0]),
									indicator: "green"
								});
								frappe.reload_doc("Giving Statement");
							}
						});
					}
				);
			});
		}
	}
});

frappe.listview_settings["Giving Statement"] = {
	add_fields: ["year"],
	get_indicator(doc) {
		return [__("Year {0}", [doc.year]), "green", "year,>=," + doc.year];
	},
	refresh(frappe_list) {
		frappe_list.page.add_menu_item(__("Download Merged PDF"), () => {
			frappe.prompt(
				[
					{
						label: __("Year"),
						fieldname: "year",
						fieldtype: "Int",
						default: new Date().getFullYear() - 1,
						reqd: 1
					}
				],
				(values) => {
					frappe.call({
						method: "churchit.church_finances.api.download_year_end_statements_pdf",
						args: { year: values.year },
						freeze: true,
						freeze_message: __("Generating PDF..."),
						callback: (r) => {
							// Frappe will auto-download via response headers
						}
					});
				}
			);
		});
	}
};
