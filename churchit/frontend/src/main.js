// This source code is freely given for the sake of the gospel (Matthew 10:8)
// and is licensed under MIT No Attribution (MIT-0).

import { createApp } from "vue";
import {
	setConfig,
	frappeRequest,
	resourcesPlugin,
	initSocket,
} from "frappe-ui";
import App from "./App.vue";
import router from "./router";
import "frappe-ui/style.css";

setConfig("resourceFetcher", frappeRequest);

const app = createApp(App);
app.use(router);
app.use(resourcesPlugin);

// One socket.io client, shared through provide/inject. A component that wants
// realtime calls `inject("socket")` and subscribes with `socket.on(...)`.
const socket = initSocket();
app.provide("socket", socket);

app.mount("#app");
