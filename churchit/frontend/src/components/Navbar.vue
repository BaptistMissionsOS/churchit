<!-- This source code is freely given for the sake of the gospel (Matthew 10:8)
     and is licensed under MIT No Attribution (MIT-0). -->
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import LucideUserCircle from "~icons/lucide/user-circle";
import LucideShield from "~icons/lucide/shield";
import LucideClipboardList from "~icons/lucide/clipboard-list";
import LucideUser from "~icons/lucide/user";
import LucideLogIn from "~icons/lucide/log-in";
import LucideLogOut from "~icons/lucide/log-out";
import LucideSun from "~icons/lucide/sun";
import LucideMoon from "~icons/lucide/moon";
import { useTheme } from "@/composables/useTheme";

const props = defineProps({ data: { type: Object, default: null } });

const { theme, toggleTheme } = useTheme();

const open = ref(false);
const memberOpen = ref(false);
const memberWrap = ref(null);
const router = useRouter();

const brand = computed(() => props.data?.church?.church_name || "Churchit");
const menu = computed(() => props.data?.menu || []);
const signedIn = computed(() => props.data?.user && props.data.user !== "Guest");
const userLabel = computed(() => (signedIn.value ? props.data.user : "Members Corner"));
const themeLabel = computed(() => (theme.value === "dark" ? "Switch to light theme" : "Switch to dark theme"));

const INTERNAL = {
	"/home": { name: "home" },
	"/portal": { name: "portal" },
	"/function-sign-up": { name: "function-sign-up" },
};

function internalRoute(url) {
	return INTERNAL[url] || null;
}

function toggleMember() {
	memberOpen.value = !memberOpen.value;
}

function closeMember() {
	memberOpen.value = false;
}

function goPortal() {
	closeMember();
	router.push({ name: "portal" });
}

function goFunctionSignUp() {
	closeMember();
	router.push({ name: "function-sign-up" });
}

function onDocClick(e) {
	if (!memberWrap.value) return;
	if (!memberWrap.value.contains(e.target)) memberOpen.value = false;
}

function onKey(e) {
	if (e.key === "Escape") memberOpen.value = false;
	// "m" opens Members Corner — ignored when typing in a field.
	if (e.key === "m" && !e.metaKey && !e.ctrlKey && !e.altKey) {
		const t = e.target;
		if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
		memberOpen.value = !memberOpen.value;
	}
}

onMounted(() => {
	document.addEventListener("click", onDocClick);
	document.addEventListener("keydown", onKey);
});

onBeforeUnmount(() => {
	document.removeEventListener("click", onDocClick);
	document.removeEventListener("keydown", onKey);
});
</script>

<template>
	<header class="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/85">
		<div class="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
			<RouterLink :to="{ name: 'home' }" class="text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 rounded">
				{{ brand }}
			</RouterLink>

			<nav class="hidden items-center gap-1 md:flex">
				<template v-for="item in menu" :key="item.label">
					<RouterLink
						v-if="internalRoute(item.url)"
						:to="internalRoute(item.url)"
						class="rounded-full px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
						active-class="bg-slate-900 text-white hover:bg-slate-900 hover:text-white dark:bg-white dark:text-slate-900 dark:hover:bg-white dark:hover:text-slate-900"
					>
						{{ item.label }}
					</RouterLink>
					<a
						v-else
						:href="item.url"
						class="rounded-full px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
					>
						{{ item.label }}
					</a>
				</template>

				<!-- Theme toggle -->
				<button
					type="button"
					class="ml-1 flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
					:aria-label="themeLabel"
					:title="themeLabel"
					@click="toggleTheme"
				>
					<LucideSun v-if="theme === 'dark'" class="h-4 w-4" />
					<LucideMoon v-else class="h-4 w-4" />
				</button>

				<!-- Members Corner: icon-triggered popup with member links. Press "m" to open. -->
				<div ref="memberWrap" class="relative">
					<button
						type="button"
						class="flex h-9 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
						:aria-expanded="memberOpen"
						aria-haspopup="menu"
						:aria-label="userLabel"
						:title="`${userLabel} (press m)`"
						@click="toggleMember"
					>
						<LucideUserCircle class="h-5 w-5" />
					</button>

					<transition
						enter-active-class="transition duration-150 ease-out"
						enter-from-class="opacity-0 translate-y-1 scale-95"
						enter-to-class="opacity-100 translate-y-0 scale-100"
						leave-active-class="transition duration-100 ease-in"
						leave-from-class="opacity-100 translate-y-0 scale-100"
						leave-to-class="opacity-0 translate-y-1 scale-95"
					>
						<div
							v-if="memberOpen"
							class="absolute right-0 mt-2 w-64 origin-top-right rounded-xl border border-slate-200 bg-white p-2 shadow-xl ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-900 dark:ring-white/10"
							role="menu"
						>
							<div class="flex items-center justify-between px-3 pb-2 pt-1">
								<span class="text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
									Members Corner
								</span>
								<span v-if="signedIn" class="truncate pl-2 text-[11px] text-slate-500 dark:text-slate-400" :title="props.data.user">
									{{ props.data.user }}
								</span>
							</div>
							<button
								type="button"
								class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus-visible:bg-slate-800"
								role="menuitem"
								@click="goPortal"
							>
								<LucideShield class="h-4 w-4 text-slate-500 dark:text-slate-400" />
								Member Portal
							</button>
							<button
								type="button"
								class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus-visible:bg-slate-800"
								role="menuitem"
								@click="goFunctionSignUp"
							>
								<LucideClipboardList class="h-4 w-4 text-slate-500 dark:text-slate-400" />
								Function Sign-Up
							</button>
							<a
								v-if="signedIn"
								href="/me"
								class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus-visible:bg-slate-800"
								role="menuitem"
								@click="closeMember"
							>
								<LucideUser class="h-4 w-4 text-slate-500 dark:text-slate-400" />
								Account
							</a>
							<a
								v-if="!signedIn"
								href="/login"
								class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus-visible:bg-slate-800"
								role="menuitem"
								@click="closeMember"
							>
								<LucideLogIn class="h-4 w-4 text-slate-500 dark:text-slate-400" />
								Log In
							</a>
							<a
								v-if="signedIn"
								href="/?cmd=web_logout"
								class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 dark:focus-visible:bg-slate-800"
								role="menuitem"
								@click="closeMember"
							>
								<LucideLogOut class="h-4 w-4 text-slate-500 dark:text-slate-400" />
								Log Out
							</a>
						</div>
					</transition>
				</div>
			</nav>

			<div class="flex items-center gap-2 md:hidden">
				<button
					type="button"
					class="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
					:aria-label="themeLabel"
					@click="toggleTheme"
				>
					<LucideSun v-if="theme === 'dark'" class="h-4 w-4" />
					<LucideMoon v-else class="h-4 w-4" />
				</button>
				<button
					type="button"
					class="rounded-md border border-slate-200 p-2 text-slate-600 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
					:aria-expanded="open"
					aria-label="Open menu"
					@click="open = !open"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</button>
			</div>
		</div>

		<nav v-if="open" class="border-t border-slate-200 bg-white md:hidden dark:border-slate-800 dark:bg-slate-900">
			<ul class="mx-auto flex max-w-6xl flex-col gap-1 px-6 py-3">
				<li v-for="item in menu" :key="item.label">
					<RouterLink
						v-if="internalRoute(item.url)"
						:to="internalRoute(item.url)"
						class="block rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
						active-class="bg-slate-900 text-white hover:bg-slate-900 dark:bg-white dark:text-slate-900"
						@click="open = false"
					>
						{{ item.label }}
					</RouterLink>
					<a
						v-else
						:href="item.url"
						class="block rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
					>
						{{ item.label }}
					</a>
				</li>
				<li class="mt-1 border-t border-slate-200 pt-2 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-800 dark:text-slate-500">
					Members Corner
				</li>
				<li>
					<RouterLink
						:to="{ name: 'portal' }"
						class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
						@click="open = false"
					>
						<LucideShield class="h-4 w-4 text-slate-500 dark:text-slate-400" />
						Member Portal
					</RouterLink>
				</li>
				<li>
					<RouterLink
						:to="{ name: 'function-sign-up' }"
						class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
						@click="open = false"
					>
						<LucideClipboardList class="h-4 w-4 text-slate-500 dark:text-slate-400" />
						Function Sign-Up
					</RouterLink>
				</li>
				<li v-if="signedIn">
					<a href="/me" class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800">
						<LucideUser class="h-4 w-4 text-slate-500 dark:text-slate-400" />
						Account
					</a>
				</li>
				<li v-if="!signedIn">
					<a href="/login" class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800">
						<LucideLogIn class="h-4 w-4 text-slate-500 dark:text-slate-400" />
						Log In
					</a>
				</li>
				<li v-if="signedIn">
					<a href="/?cmd=web_logout" class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800">
						<LucideLogOut class="h-4 w-4 text-slate-500 dark:text-slate-400" />
						Log Out
					</a>
				</li>
			</ul>
		</nav>
	</header>
</template>
