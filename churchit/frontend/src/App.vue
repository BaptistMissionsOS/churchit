<!-- This source code is freely given for the sake of the gospel (Matthew 10:8)
     and is licensed under MIT No Attribution (MIT-0). -->
<script setup>
import { createResource } from "frappe-ui";
import { provide } from "vue";
import Navbar from "@/components/Navbar.vue";
import ScrollToTop from "@/components/ScrollToTop.vue";
import { useTheme } from "@/composables/useTheme";

// Initialize theme once at app start so data-theme is applied before paint.
useTheme();

// Chrome and home data load once at app start and are shared with every route
// through provide/inject, so Portal and Function Sign-Up never refetch the menu.
const homeData = createResource({
	url: "churchit.church_website.kiosk.get_home_data",
	method: "GET",
	auto: true,
	cache: "kiosk:home_data",
});

provide("homeData", homeData);
</script>

<template>
	<div class="min-h-screen bg-slate-50 text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
		<Navbar :data="homeData.data" />
		<router-view :data="homeData.data" :loading="homeData.loading" />
		<ScrollToTop />
	</div>
</template>
