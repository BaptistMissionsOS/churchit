// This source code is freely given for the sake of the gospel (Matthew 10:8)
// and is licensed under MIT No Attribution (MIT-0).

import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{ path: "/", name: "home", component: () => import("@/pages/Home.vue") },
	{ path: "/portal", name: "portal", component: () => import("@/pages/Portal.vue") },
	{
		path: "/function-sign-up",
		name: "function-sign-up",
		component: () => import("@/pages/FunctionSignUp.vue"),
	},
];

export default createRouter({
	history: createWebHistory("/door"),
	routes,
	scrollBehavior() {
		return { top: 0 };
	},
});
