// This source code is freely given for the sake of the gospel (Matthew 10:8)
// and is licensed under MIT No Attribution (MIT-0).

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import frappeui from "frappe-ui/vite";
import path from "path";

// The door SPA. frappe-ui's preset handles lucide icons, the proxy to the
// local bench, and copying the built index.html to churchit/www/door.html so
// Frappe serves it in production.
export default defineConfig({
	plugins: [
		frappeui({
			frontendRoute: "/door",
			// churchit nests the Vue app inside the python package, so the preset's
			// auto-detection cannot find the Frappe app directory. Point it at the
			// right folders by hand.
			buildConfig: {
				outDir: path.resolve(__dirname, "../public/frontend"),
				indexHtmlPath: path.resolve(__dirname, "../www/door.html"),
			},
		}),
		vue(),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
		},
	},
	// frappe-ui ships source, not a bundle, and uses `~icons/*` imports that
	// its own vite plugin resolves. Skip esbuild's pre-bundle so the plugin
	// pipeline sees those modules first.
	optimizeDeps: {
		exclude: ["frappe-ui"],
		// Transitive CommonJS deps that need Vite's interop to expose a default
		// export to frappe-ui's source files.
		include: [
			"feather-icons",
			"showdown",
			"engine.io-client",
			"socket.io-client",
			"prosemirror-state",
			"prosemirror-view",
			"lowlight",
			"interactjs",
		],
	},
});
