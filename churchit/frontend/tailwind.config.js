// This source code is freely given for the sake of the gospel (Matthew 10:8)
// and is licensed under MIT No Attribution (MIT-0).

import frappeuiPreset from "frappe-ui/tailwind";

export default {
	presets: [frappeuiPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts}",
		"../node_modules/frappe-ui/src/**/*.{vue,js,ts}",
		"./node_modules/frappe-ui/src/**/*.{vue,js,ts}",
	],
};
