<!-- This source code is freely given for the sake of the gospel (Matthew 10:8)
     and is licensed under MIT No Attribution (MIT-0). -->
<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import LucideArrowUp from "~icons/lucide/arrow-up";

const show = ref(false);

function onScroll() {
	show.value = window.scrollY > 600;
}

function back() {
	const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
	window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
}

onMounted(() => {
	onScroll();
	window.addEventListener("scroll", onScroll, { passive: true });
});

onBeforeUnmount(() => {
	window.removeEventListener("scroll", onScroll);
});
</script>

<template>
	<transition
		enter-active-class="transition duration-200 ease-out"
		enter-from-class="opacity-0 translate-y-2"
		enter-to-class="opacity-100 translate-y-0"
		leave-active-class="transition duration-150 ease-in"
		leave-from-class="opacity-100 translate-y-0"
		leave-to-class="opacity-0 translate-y-2"
	>
		<button
			v-if="show"
			type="button"
			aria-label="Back to top"
			class="fixed bottom-6 right-6 z-30 flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-lg ring-1 ring-black/5 hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
			@click="back"
		>
			<LucideArrowUp class="h-5 w-5" />
		</button>
	</transition>
</template>
