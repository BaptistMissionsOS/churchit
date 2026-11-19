<!-- This source code is freely given for the sake of the gospel (Matthew 10:8)
     and is licensed under MIT No Attribution (MIT-0). -->
<script setup>
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";
import { Button } from "frappe-ui";
import LucideCalendar from "~icons/lucide/calendar";
import LucideMapPin from "~icons/lucide/map-pin";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideSparkles from "~icons/lucide/sparkles";
import LucideClock from "~icons/lucide/clock";
import LucideUsers from "~icons/lucide/users";
import LucideBookOpen from "~icons/lucide/book-open";
import LucideHeart from "~icons/lucide/heart";
import LucideGlobe from "~icons/lucide/globe";
import LucideMic from "~icons/lucide/mic";
import LucideMessageCircle from "~icons/lucide/message-circle";
import LucidePlay from "~icons/lucide/play";
import LucideRadio from "~icons/lucide/radio";
import LucideChevronRight from "~icons/lucide/chevron-right";
import LucideQuote from "~icons/lucide/quote";

const props = defineProps({
	data: { type: Object, default: null },
	loading: { type: Boolean, default: false },
});

const socket = inject("socket");
const homeData = inject("homeData");

const church = computed(() => props.data?.church);
const menu = computed(() => props.data?.menu || []);
const upcoming = computed(() => props.data?.upcoming || []);
const next = computed(() => upcoming.value[0]);
const later = computed(() => upcoming.value.slice(1));
const sermon = computed(() => props.data?.latest_sermon);
const stats = computed(() => props.data?.stats || []);
const offPages = computed(() => new Set(props.data?.off_pages || []));

const hasCalendar = computed(() => menu.value.some((i) => i.url === "/calendar") && !offPages.value.has("calendar"));
const hasContact = computed(() => menu.value.some((i) => i.url === "/contact") && !offPages.value.has("contact"));

const STAT_ICONS = {
	heart: LucideHeart,
	users: LucideUsers,
	globe: LucideGlobe,
	"book-open": LucideBookOpen,
};

function statIcon(slug) {
	return STAT_ICONS[slug] || LucideSparkles;
}

function formatDate(d, opts = { weekday: "long", month: "long", day: "numeric", year: "numeric" }) {
	if (!d) return "";
	return new Date(`${d}T00:00:00`).toLocaleDateString(undefined, opts);
}

function formatTime(t) {
	if (!t) return "";
	const [h, m] = t.split(":");
	const date = new Date();
	date.setHours(+h, +m);
	return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function dayOfMonth(d) {
	if (!d) return "";
	return new Date(`${d}T00:00:00`).getDate();
}

function monthShort(d) {
	if (!d) return "";
	return new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { month: "short" });
}

function sermonBlurb(notes) {
	if (!notes) return "";
	const match = notes.match(/<p>([\s\S]*?)<\/p>/);
	const text = (match ? match[1] : notes)
		.replace(/<[^>]+>/g, "")
		.replace(/[[\]]/g, "")
		.trim();
	return text.length > 180 ? text.slice(0, 177) + "…" : text;
}

// Live clock ticks every second so the countdown card feels alive.
const now = ref(new Date());
let tickInterval = null;

// Socket.IO connection state surfaced in the "LIVE" badge — proof that
// the frontend is wired up to realtime, not just a static render.
const socketLive = ref(!!socket?.connected);
function onConnect() {
	socketLive.value = true;
}
function onDisconnect() {
	socketLive.value = false;
}

// Count-up animation for the stats row. Each stat's displayed number
// animates from 0 → target on mount and whenever data changes.
const displayedStats = ref([]);
let countRaf = null;

function runCountUp() {
	if (countRaf) cancelAnimationFrame(countRaf);
	const targets = stats.value.map((s) => Number(s.number) || 0);
	displayedStats.value = targets.map(() => 0);
	const start = performance.now();
	const duration = 1200;
	const step = (t) => {
		const p = Math.min(1, (t - start) / duration);
		const eased = 1 - Math.pow(1 - p, 3);
		displayedStats.value = targets.map((n) => Math.round(n * eased));
		if (p < 1) countRaf = requestAnimationFrame(step);
	};
	countRaf = requestAnimationFrame(step);
}

const nextEventDate = computed(() => {
	if (!next.value?.start_date) return null;
	const t = next.value.start_time || "09:00:00";
	return new Date(`${next.value.start_date}T${t}`);
});

const countdown = computed(() => {
	if (!nextEventDate.value) return null;
	const diff = nextEventDate.value.getTime() - now.value.getTime();
	if (diff <= 0) return { d: 0, h: 0, m: 0, s: 0, live: true };
	const d = Math.floor(diff / 86400000);
	const h = Math.floor((diff % 86400000) / 3600000);
	const m = Math.floor((diff % 3600000) / 60000);
	const s = Math.floor((diff % 60000) / 1000);
	return { d, h, m, s, live: false };
});

const greeting = computed(() => {
	const h = now.value.getHours();
	if (h < 12) return "Good morning";
	if (h < 18) return "Good afternoon";
	return "Good evening";
});

// Headline is split so each character can stagger in. We split the
// church name once per data change so Vue only re-renders when needed.
const headlineChars = computed(() => {
	const name = church.value?.church_name || "";
	return Array.from(name);
});

// Cursor-tracked spotlight + 3D tilt use CSS variables so the hero paints
// on the GPU without triggering layout. Values are 0–100 for the spotlight
// and small degrees for the glass card tilt.
const heroRef = ref(null);
const glassRef = ref(null);

function onHeroMove(e) {
	const el = heroRef.value;
	if (!el) return;
	const r = el.getBoundingClientRect();
	const x = ((e.clientX - r.left) / r.width) * 100;
	const y = ((e.clientY - r.top) / r.height) * 100;
	el.style.setProperty("--sx", `${x}%`);
	el.style.setProperty("--sy", `${y}%`);
}

function onGlassMove(e) {
	const el = glassRef.value;
	if (!el) return;
	const r = el.getBoundingClientRect();
	const cx = (e.clientX - r.left) / r.width - 0.5;
	const cy = (e.clientY - r.top) / r.height - 0.5;
	el.style.setProperty("--rx", `${(-cy * 8).toFixed(2)}deg`);
	el.style.setProperty("--ry", `${(cx * 10).toFixed(2)}deg`);
}

function resetGlass() {
	const el = glassRef.value;
	if (!el) return;
	el.style.setProperty("--rx", "0deg");
	el.style.setProperty("--ry", "0deg");
}

// Magnetic buttons: the handler is attached once via directive-style ref
// callback so any <a> inside .magnetic gets the pull effect for free.
function onMagneticMove(e) {
	const el = e.currentTarget;
	const r = el.getBoundingClientRect();
	const x = e.clientX - (r.left + r.width / 2);
	const y = e.clientY - (r.top + r.height / 2);
	el.style.setProperty("--mx", `${x * 0.2}px`);
	el.style.setProperty("--my", `${y * 0.2}px`);
}

function onMagneticLeave(e) {
	const el = e.currentTarget;
	el.style.setProperty("--mx", "0px");
	el.style.setProperty("--my", "0px");
}

// Scroll progress for the hairline bar at the top. 0–1 of total scroll.
const scrollProgress = ref(0);
function onScroll() {
	const h = document.documentElement;
	const max = h.scrollHeight - h.clientHeight;
	scrollProgress.value = max > 0 ? Math.min(1, h.scrollTop / max) : 0;
}

// Signature touch: a rotating scripture marquee under the hero. Kept in
// the component because it is pure design copy, not church data.
const verses = [
	{ text: "Be still, and know that I am God.", ref: "Psalm 46:10" },
	{ text: "The Lord is my shepherd; I shall not want.", ref: "Psalm 23:1" },
	{ text: "Let all that you do be done in love.", ref: "1 Corinthians 16:14" },
	{ text: "For where two or three are gathered in my name, there am I among them.", ref: "Matthew 18:20" },
	{ text: "This is the day that the Lord has made; let us rejoice and be glad in it.", ref: "Psalm 118:24" },
	{ text: "Love one another as I have loved you.", ref: "John 15:12" },
];
const verseIndex = ref(0);
let verseInterval = null;

// Hour-of-day ring progresses the outer SVG arc on the countdown card — an
// always-moving timepiece that makes the door feel alive even on a quiet lobby wall.
const hourRingProgress = computed(() => {
	const d = now.value;
	const totalSeconds = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds();
	return totalSeconds / 86400;
});
const RING_CIRC = 2 * Math.PI * 46;

function onListUpdate(payload) {
	if (payload?.doctype === "Function" || payload?.doctype === "Sermon") {
		homeData.reload();
	}
}

onMounted(() => {
	tickInterval = setInterval(() => (now.value = new Date()), 1000);
	verseInterval = setInterval(() => {
		verseIndex.value = (verseIndex.value + 1) % verses.length;
	}, 6000);
	socket?.on("list_update", onListUpdate);
	socket?.on("connect", onConnect);
	socket?.on("disconnect", onDisconnect);
	window.addEventListener("scroll", onScroll, { passive: true });
	runCountUp();
});

onUnmounted(() => {
	clearInterval(tickInterval);
	clearInterval(verseInterval);
	if (countRaf) cancelAnimationFrame(countRaf);
	socket?.off("list_update", onListUpdate);
	socket?.off("connect", onConnect);
	socket?.off("disconnect", onDisconnect);
	window.removeEventListener("scroll", onScroll);
});

watch(stats, runCountUp);
</script>

<template>
	<main class="relative">
		<!-- Hairline scroll-progress bar: Vercel/Linear style, one line of state -->
		<div class="scroll-bar" :style="{ transform: `scaleX(${scrollProgress})` }" aria-hidden="true" />

		<!-- Grain overlay used by the hero. Inline SVG so no asset round-trip. -->
		<svg class="hidden" aria-hidden="true">
			<filter id="grain">
				<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
				<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.35 0" />
			</filter>
		</svg>

		<!-- Skeleton while the door fetches home data -->
		<div v-if="loading && !data" class="mx-auto max-w-7xl animate-pulse px-6 py-10 space-y-10" aria-hidden="true">
			<div class="h-[32rem] rounded-[2rem] bg-slate-200/70 dark:bg-slate-800/70" />
			<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
				<div v-for="i in 4" :key="i" class="h-32 rounded-2xl bg-slate-200/70 dark:bg-slate-800/70" />
			</div>
			<div class="grid gap-6 lg:grid-cols-2">
				<div class="h-64 rounded-2xl bg-slate-200/70 dark:bg-slate-800/70" />
				<div class="h-64 rounded-2xl bg-slate-200/70 dark:bg-slate-800/70" />
			</div>
		</div>

		<template v-else-if="church">
			<!-- HERO: cursor-spotlight, mesh gradient, orbs, grain overlay -->
			<section
				ref="heroRef"
				class="hero relative isolate overflow-hidden text-white"
				@mousemove="onHeroMove"
			>
				<div class="absolute inset-0 -z-10 bg-slate-950" />
				<div class="hero-mesh absolute inset-0 -z-10" aria-hidden="true" />
				<div class="hero-grid absolute inset-0 -z-10 opacity-[0.07]" aria-hidden="true" />
				<div class="hero-spot absolute inset-0 -z-10" aria-hidden="true" />
				<div class="hero-grain absolute inset-0 -z-10" aria-hidden="true" />
				<div class="orb orb-a" aria-hidden="true" />
				<div class="orb orb-b" aria-hidden="true" />
				<div class="orb orb-c" aria-hidden="true" />

				<div class="mx-auto grid max-w-7xl gap-10 px-6 pb-24 pt-14 lg:grid-cols-[1.4fr_1fr] lg:gap-14 lg:pb-32 lg:pt-20">
					<!-- Left: brand + mission + CTAs -->
					<div class="relative flex flex-col justify-center reveal-up">
						<div class="flex flex-wrap items-center gap-3">
							<span class="chip">
								<LucideSparkles class="h-3.5 w-3.5" aria-hidden="true" />
								{{ greeting }}
							</span>
							<span class="chip chip-live" :class="socketLive ? 'is-on' : 'is-off'">
								<span class="live-dot" />
								<LucideRadio class="h-3.5 w-3.5" aria-hidden="true" />
								{{ socketLive ? "Live" : "Offline" }}
							</span>
						</div>

						<h1 class="mt-6 text-5xl font-semibold leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl">
							<span class="block text-white/90">Welcome to</span>
							<span class="headline-gradient block">
								<!-- Letter-by-letter kinetic entrance: each glyph rises with
									 its own delay so the name feels authored, not stamped on. -->
								<span
									v-for="(ch, i) in headlineChars"
									:key="i"
									class="headline-char"
									:style="{ animationDelay: `${i * 35 + 120}ms` }"
								>{{ ch === " " ? "\u00a0" : ch }}</span>
							</span>
						</h1>

						<p
							v-if="church.mission_statement"
							class="mt-6 max-w-xl text-lg leading-relaxed text-white/75 sm:text-xl reveal-up"
							style="animation-delay: 260ms"
						>
							{{ church.mission_statement }}
						</p>

						<div class="mt-9 flex flex-wrap items-center gap-3 reveal-up" style="animation-delay: 360ms">
							<a
								v-if="hasCalendar"
								href="/calendar"
								class="magnetic"
								@mousemove="onMagneticMove"
								@mouseleave="onMagneticLeave"
							>
								<Button variant="solid" size="lg" class="btn-glow">
									<template #prefix>
										<LucideCalendar class="h-4 w-4" />
									</template>
									See the calendar
								</Button>
							</a>
							<a
								v-if="hasContact"
								href="/contact"
								class="magnetic"
								@mousemove="onMagneticMove"
								@mouseleave="onMagneticLeave"
							>
								<Button
									variant="outline"
									size="lg"
									class="!border-white/25 !bg-white/5 !text-white backdrop-blur hover:!bg-white/10"
								>
									<template #prefix>
										<LucideMessageCircle class="h-4 w-4" />
									</template>
									Get in touch
								</Button>
							</a>
						</div>

					</div>

					<!-- Right: next gathering with LIVE COUNTDOWN and 3D tilt -->
					<aside v-if="next" class="reveal-up tilt-wrap" style="animation-delay: 140ms">
						<div
							ref="glassRef"
							class="glass-card tilt relative flex h-full flex-col p-7 lg:p-8"
							@mousemove="onGlassMove"
							@mouseleave="resetGlass"
						>
							<!-- Sheen that tracks the tilt so the card feels like real glass -->
							<div class="glass-sheen" aria-hidden="true" />

							<div class="flex items-center justify-between">
								<p class="chip chip-emerald">
									<span class="pulse-dot" />
									Next gathering
								</p>
								<!-- SVG hour-of-day ring: the outer arc fills from midnight to
									 midnight, giving the card a constantly-moving timepiece. -->
								<svg class="hour-ring" viewBox="0 0 100 100" aria-hidden="true">
									<circle class="hour-ring-track" cx="50" cy="50" r="46" />
									<circle
										class="hour-ring-fill"
										cx="50" cy="50" r="46"
										:stroke-dasharray="RING_CIRC"
										:stroke-dashoffset="RING_CIRC * (1 - hourRingProgress)"
									/>
								</svg>
							</div>

							<h2 class="mt-5 text-2xl font-semibold leading-tight text-white">
								{{ next.function_name || next.title }}
							</h2>
							<p class="mt-2 flex items-center gap-1.5 text-sm text-white/70">
								<LucideClock class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
								<span>
									{{ formatDate(next.start_date, { weekday: "long", month: "long", day: "numeric" }) }}
									<span v-if="!next.all_day && next.start_time"> · {{ formatTime(next.start_time) }}</span>
									<span v-else-if="next.all_day"> · all day</span>
								</span>
							</p>

							<!-- Live countdown: every second, powered by Vue reactivity -->
							<div v-if="countdown" class="mt-6 grid grid-cols-4 gap-2">
								<div v-for="unit in [
									{ v: countdown.d, l: 'days' },
									{ v: countdown.h, l: 'hrs' },
									{ v: countdown.m, l: 'min' },
									{ v: countdown.s, l: 'sec' },
								]" :key="unit.l" class="countdown-cell">
									<div class="countdown-num">{{ String(unit.v).padStart(2, "0") }}</div>
									<div class="countdown-label">{{ unit.l }}</div>
								</div>
							</div>

							<p v-if="church.address_line" class="mt-6 flex items-center gap-1.5 text-sm text-white/60">
								<LucideMapPin class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
								<span>{{ church.address_line }}</span>
							</p>

							<a
								v-if="hasCalendar"
								href="/calendar"
								class="mt-auto inline-flex items-center gap-1 pt-6 text-sm font-medium text-emerald-300 transition hover:text-emerald-200"
							>
								Full calendar
								<LucideArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
							</a>
						</div>
					</aside>
				</div>

				<!-- Scripture ticker: the signature detail under the hero. Verses are
					 presentation-only, so they live client-side and rotate every 6s. -->
				<div class="verse-strip" aria-live="polite">
					<div class="mx-auto flex max-w-7xl items-center gap-4 px-6 py-5">
						<LucideQuote class="h-4 w-4 shrink-0 text-emerald-300/70" aria-hidden="true" />
						<Transition name="verse" mode="out-in">
							<div :key="verseIndex" class="verse-line">
								<span class="verse-text">{{ verses[verseIndex].text }}</span>
								<span class="verse-ref">— {{ verses[verseIndex].ref }}</span>
							</div>
						</Transition>
					</div>
				</div>
			</section>

			<!-- STATS: animated count-up on gradient tiles -->
			<section v-if="stats.length" class="mx-auto -mt-14 max-w-7xl px-6">
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
					<div
						v-for="(stat, i) in stats"
						:key="stat.label"
						class="stat-tile reveal-up"
						:style="{ animationDelay: `${i * 80 + 200}ms` }"
					>
						<div class="stat-icon">
							<component :is="statIcon(stat.icon)" class="h-5 w-5" aria-hidden="true" />
						</div>
						<div class="stat-number">
							{{ displayedStats[i] ?? 0 }}
						</div>
						<div class="stat-label">{{ stat.label }}</div>
						<!-- Thin shimmer underline — a design-only flourish that reads
							 as "fresh" without looking like a loading spinner. -->
						<div class="stat-shimmer" aria-hidden="true" />
					</div>
				</div>
			</section>

			<!-- ABOUT: understated with gradient divider -->
			<section v-if="church.about" class="mx-auto mt-20 max-w-4xl px-6">
				<div class="flex items-center gap-3">
					<span class="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent dark:via-slate-600" aria-hidden="true" />
					<p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 dark:text-slate-400">About us</p>
					<span class="h-px flex-1 bg-gradient-to-r from-transparent via-slate-300 to-transparent dark:via-slate-600" aria-hidden="true" />
				</div>
				<div class="prose prose-slate dark:prose-invert mx-auto mt-6 max-w-none text-center text-[17px] leading-relaxed text-slate-700 dark:text-slate-300" v-html="church.about" />
			</section>

			<!-- SERMON + COMING UP -->
			<section v-if="sermon || later.length" class="mx-auto mt-20 max-w-7xl px-6 pb-20">
				<div class="grid gap-6 lg:grid-cols-2">
					<article
						v-if="sermon"
						class="sermon-card group relative flex flex-col overflow-hidden rounded-3xl p-8 text-white"
					>
						<div class="sermon-mesh absolute inset-0 -z-10" aria-hidden="true" />
						<div class="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-amber-300/20 blur-3xl" aria-hidden="true" />

						<p class="chip chip-amber">
							<LucideMic class="h-3.5 w-3.5" aria-hidden="true" />
							Latest message
						</p>
						<h2 class="mt-4 text-3xl font-semibold leading-tight">{{ sermon.title }}</h2>
						<p v-if="sermon.prepared_by_name" class="mt-1 text-sm text-white/70">
							by {{ sermon.prepared_by_name }}
						</p>
						<p v-if="sermon.notes && !sermon.handout" class="mt-5 text-[15px] leading-relaxed text-white/80">
							{{ sermonBlurb(sermon.notes) }}
						</p>

						<!-- Faux audio bars: the bars animate with staggered keyframes so
							 the sermon card reads as "sound" even before playback starts. -->
						<div class="waveform mt-6" aria-hidden="true">
							<span v-for="n in 32" :key="n" :style="{ animationDelay: `${n * 60}ms` }" />
						</div>

						<audio
							v-if="sermon.audio_recording"
							controls
							preload="none"
							class="mt-4 w-full rounded-lg"
							:aria-label="`Sermon audio: ${sermon.title}`"
						>
							<source :src="sermon.audio_recording" />
						</audio>
						<a
							href="/sermons"
							class="mt-auto inline-flex items-center gap-1 pt-6 text-sm font-medium text-amber-200 transition hover:text-amber-100"
						>
							<LucidePlay class="h-3.5 w-3.5" aria-hidden="true" />
							Browse all sermons
							<LucideArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
						</a>
					</article>

					<article
						v-if="later.length"
						class="flex flex-col rounded-3xl border border-slate-200 bg-white p-8 shadow-sm transition hover:shadow-xl dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40"
					>
						<p class="chip chip-slate">
							<LucideCalendar class="h-3.5 w-3.5" aria-hidden="true" />
							Coming up
						</p>
						<ul class="mt-5 divide-y divide-slate-100 dark:divide-slate-800">
							<li
								v-for="event in later"
								:key="event.name"
								class="group flex items-center gap-4 py-4 transition hover:translate-x-0.5"
							>
								<div class="date-chip">
									<span class="date-chip-month">{{ monthShort(event.start_date) }}</span>
									<span class="date-chip-day">{{ dayOfMonth(event.start_date) }}</span>
								</div>
								<div class="min-w-0 flex-1">
									<p class="truncate text-base font-semibold text-slate-900 dark:text-slate-100">
										{{ event.function_name || event.title }}
									</p>
									<p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
										{{ formatDate(event.start_date, { weekday: "short" }) }}
										<span v-if="!event.all_day && event.start_time"> · {{ formatTime(event.start_time) }}</span>
									</p>
								</div>
								<LucideChevronRight
									class="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-emerald-500 dark:text-slate-600"
									aria-hidden="true"
								/>
							</li>
						</ul>
						<a
							v-if="hasCalendar"
							href="/calendar"
							class="mt-auto inline-flex items-center gap-1 pt-6 text-sm font-medium text-emerald-700 transition hover:text-emerald-800"
						>
							See the full calendar
							<LucideArrowRight class="h-3.5 w-3.5" aria-hidden="true" />
						</a>
					</article>
				</div>
			</section>
		</template>

		<section v-else class="mx-auto max-w-xl py-24 text-center">
			<h2 class="text-2xl font-semibold text-slate-900 dark:text-slate-100">This website is being set up</h2>
			<p class="mt-2 text-slate-600 dark:text-slate-400">Please check back soon.</p>
			<a href="/login">
				<Button class="mt-6" variant="outline">Log in</Button>
			</a>
		</section>
	</main>
</template>

<style scoped>
/* ---------- Scroll progress hairline ---------- */
.scroll-bar {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	height: 2px;
	background: linear-gradient(90deg, #a5f3fc, #34d399, #fcd34d);
	transform-origin: 0 50%;
	transform: scaleX(0);
	z-index: 50;
	pointer-events: none;
}

/* ---------- Hero backdrop ---------- */
.hero { --sx: 50%; --sy: 30%; }
.hero-mesh {
	background:
		radial-gradient(60rem 40rem at 10% 0%, rgba(99, 102, 241, 0.45), transparent 60%),
		radial-gradient(50rem 35rem at 95% 15%, rgba(16, 185, 129, 0.35), transparent 60%),
		radial-gradient(70rem 50rem at 60% 100%, rgba(236, 72, 153, 0.25), transparent 60%),
		linear-gradient(180deg, #0b1020 0%, #0a0f1f 100%);
}
.hero-spot {
	background: radial-gradient(28rem 28rem at var(--sx) var(--sy), rgba(255, 255, 255, 0.10), transparent 60%);
	transition: background 0.25s ease;
	mix-blend-mode: screen;
}
.hero-grain {
	filter: url(#grain);
	opacity: 0.35;
	mix-blend-mode: overlay;
}
.hero-grid {
	background-image:
		linear-gradient(to right, rgba(255, 255, 255, 0.5) 1px, transparent 1px),
		linear-gradient(to bottom, rgba(255, 255, 255, 0.5) 1px, transparent 1px);
	background-size: 44px 44px;
	mask-image: radial-gradient(ellipse at top, black 40%, transparent 75%);
}
.orb {
	position: absolute;
	border-radius: 9999px;
	filter: blur(60px);
	pointer-events: none;
	opacity: 0.6;
	z-index: -1;
}
.orb-a {
	width: 22rem;
	height: 22rem;
	top: -4rem;
	left: -4rem;
	background: #6366f1;
	animation: float 14s ease-in-out infinite;
}
.orb-b {
	width: 20rem;
	height: 20rem;
	top: 8rem;
	right: -5rem;
	background: #10b981;
	animation: float 16s ease-in-out infinite reverse;
}
.orb-c {
	width: 18rem;
	height: 18rem;
	bottom: 2rem;
	left: 30%;
	background: #ec4899;
	animation: float 18s ease-in-out infinite;
}
@keyframes float {
	0%, 100% { transform: translate(0, 0) scale(1); }
	50% { transform: translate(2rem, -1.5rem) scale(1.08); }
}

/* ---------- Chips ---------- */
.chip {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	border-radius: 9999px;
	padding: 0.35rem 0.75rem;
	font-size: 0.72rem;
	font-weight: 600;
	letter-spacing: 0.18em;
	text-transform: uppercase;
	background: rgba(255, 255, 255, 0.08);
	color: #fff;
	border: 1px solid rgba(255, 255, 255, 0.15);
	backdrop-filter: blur(8px);
}
.chip-live.is-on { color: #6ee7b7; border-color: rgba(110, 231, 183, 0.35); }
.chip-live.is-off { color: #fca5a5; border-color: rgba(252, 165, 165, 0.35); }
.chip-emerald { color: #6ee7b7; border-color: rgba(110, 231, 183, 0.35); background: rgba(16, 185, 129, 0.12); }
.chip-amber { color: #fcd34d; border-color: rgba(252, 211, 77, 0.35); background: rgba(252, 211, 77, 0.12); }
.chip-slate {
	color: #475569;
	background: #f1f5f9;
	border-color: #e2e8f0;
	backdrop-filter: none;
}

.live-dot, .pulse-dot {
	display: inline-block;
	width: 0.5rem;
	height: 0.5rem;
	border-radius: 9999px;
	background: #10b981;
	box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
	animation: pulse 1.6s ease-out infinite;
}
.chip-live.is-off .live-dot { background: #ef4444; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
@keyframes pulse {
	0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
	70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
	100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* ---------- Headline ---------- */
.headline-gradient {
	background-image: linear-gradient(90deg, #a5f3fc 0%, #ffffff 40%, #fcd34d 100%);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
}
.headline-char {
	display: inline-block;
	opacity: 0;
	transform: translateY(0.4em);
	animation: letter-in 0.7s cubic-bezier(0.2, 0.7, 0.2, 1) both;
}
@keyframes letter-in {
	to { opacity: 1; transform: translateY(0); }
}

.btn-glow {
	box-shadow: 0 10px 40px -10px rgba(16, 185, 129, 0.6);
}

/* ---------- Magnetic buttons ---------- */
.magnetic {
	--mx: 0px;
	--my: 0px;
	display: inline-flex;
	transform: translate(var(--mx), var(--my));
	transition: transform 0.25s cubic-bezier(0.2, 0.7, 0.2, 1);
	will-change: transform;
}

/* ---------- Glass card with 3D tilt ---------- */
.tilt-wrap { perspective: 1200px; }
.tilt {
	--rx: 0deg;
	--ry: 0deg;
	transform: rotateX(var(--rx)) rotateY(var(--ry));
	transition: transform 0.25s cubic-bezier(0.2, 0.7, 0.2, 1);
	transform-style: preserve-3d;
	will-change: transform;
}
.glass-card {
	background: linear-gradient(140deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
	border: 1px solid rgba(255, 255, 255, 0.14);
	border-radius: 1.5rem;
	backdrop-filter: blur(14px);
	box-shadow: 0 30px 80px -30px rgba(0, 0, 0, 0.6);
	position: relative;
	overflow: hidden;
}
.glass-sheen {
	position: absolute;
	inset: 0;
	pointer-events: none;
	background: linear-gradient(120deg, rgba(255, 255, 255, 0.12), transparent 40%);
	opacity: 0.6;
	mix-blend-mode: screen;
}

.hour-ring {
	width: 2.75rem;
	height: 2.75rem;
}
.hour-ring-track {
	fill: none;
	stroke: rgba(255, 255, 255, 0.12);
	stroke-width: 4;
}
.hour-ring-fill {
	fill: none;
	stroke: #6ee7b7;
	stroke-width: 4;
	stroke-linecap: round;
	transform: rotate(-90deg);
	transform-origin: 50% 50%;
	transition: stroke-dashoffset 1s linear;
	filter: drop-shadow(0 0 6px rgba(110, 231, 183, 0.6));
}

.countdown-cell {
	border-radius: 0.9rem;
	padding: 0.75rem 0.5rem;
	background: linear-gradient(160deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.04));
	border: 1px solid rgba(255, 255, 255, 0.12);
	text-align: center;
}
.countdown-num {
	font-size: 1.75rem;
	font-weight: 700;
	line-height: 1;
	color: #fff;
	font-variant-numeric: tabular-nums;
	letter-spacing: -0.02em;
}
.countdown-label {
	margin-top: 0.4rem;
	font-size: 0.65rem;
	font-weight: 600;
	letter-spacing: 0.2em;
	text-transform: uppercase;
	color: rgba(255, 255, 255, 0.55);
}

/* ---------- Verse strip (signature design element) ---------- */
.verse-strip {
	position: relative;
	border-top: 1px solid rgba(255, 255, 255, 0.08);
	border-bottom: 1px solid rgba(255, 255, 255, 0.08);
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.00));
	backdrop-filter: blur(6px);
}
.verse-line {
	display: flex;
	flex-wrap: wrap;
	align-items: baseline;
	gap: 0.75rem;
	min-height: 1.5rem;
}
.verse-text {
	font-family: ui-serif, Georgia, "Times New Roman", serif;
	font-style: italic;
	font-size: 1.05rem;
	color: rgba(255, 255, 255, 0.85);
	letter-spacing: 0.01em;
}
.verse-ref {
	font-size: 0.72rem;
	font-weight: 600;
	letter-spacing: 0.22em;
	text-transform: uppercase;
	color: rgba(110, 231, 183, 0.75);
}
.verse-enter-active, .verse-leave-active {
	transition: opacity 0.6s ease, transform 0.6s cubic-bezier(0.2, 0.7, 0.2, 1);
}
.verse-enter-from { opacity: 0; transform: translateY(0.5rem); }
.verse-leave-to { opacity: 0; transform: translateY(-0.5rem); }

/* ---------- Stats ---------- */
.stat-tile {
	position: relative;
	border-radius: 1.25rem;
	padding: 1.25rem;
	background: #fff;
	border: 1px solid #e2e8f0;
	box-shadow: 0 10px 30px -18px rgba(15, 23, 42, 0.25);
	transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
	overflow: hidden;
}
.stat-tile::before {
	content: "";
	position: absolute;
	inset: 0;
	background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(99, 102, 241, 0.06) 60%, transparent);
	opacity: 0;
	transition: opacity 0.25s ease;
}
.stat-tile:hover {
	transform: translateY(-3px);
	border-color: #a7f3d0;
	box-shadow: 0 20px 40px -20px rgba(16, 185, 129, 0.35);
}
.stat-tile:hover::before { opacity: 1; }
.stat-icon {
	position: relative;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 2.5rem;
	height: 2.5rem;
	border-radius: 0.85rem;
	background: linear-gradient(140deg, #ecfdf5, #e0e7ff);
	color: #047857;
	border: 1px solid #a7f3d0;
}
.stat-number {
	position: relative;
	margin-top: 1rem;
	font-size: 2.25rem;
	font-weight: 700;
	line-height: 1;
	letter-spacing: -0.02em;
	color: #0f172a;
	font-variant-numeric: tabular-nums;
	background: linear-gradient(180deg, #0f172a, #334155);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
}
.stat-label {
	position: relative;
	margin-top: 0.35rem;
	font-size: 0.72rem;
	font-weight: 600;
	letter-spacing: 0.15em;
	text-transform: uppercase;
	color: #64748b;
}
.stat-shimmer {
	position: absolute;
	left: 1.25rem;
	right: 1.25rem;
	bottom: 0.65rem;
	height: 2px;
	border-radius: 9999px;
	background: linear-gradient(90deg, transparent, #a7f3d0 50%, transparent);
	background-size: 200% 100%;
	animation: shimmer 2.8s linear infinite;
	opacity: 0.6;
}
@keyframes shimmer {
	0% { background-position: 200% 0; }
	100% { background-position: -200% 0; }
}

/* ---------- Sermon card ---------- */
.sermon-card {
	background: #111827;
	border: 1px solid rgba(255, 255, 255, 0.08);
	box-shadow: 0 30px 70px -30px rgba(2, 6, 23, 0.8);
}
.sermon-mesh {
	background:
		radial-gradient(40rem 25rem at 0% 0%, rgba(99, 102, 241, 0.35), transparent 60%),
		radial-gradient(35rem 20rem at 100% 100%, rgba(236, 72, 153, 0.25), transparent 60%),
		linear-gradient(180deg, #0f172a 0%, #111827 100%);
}

/* ---------- Faux waveform on the sermon card ---------- */
.waveform {
	display: flex;
	align-items: flex-end;
	gap: 3px;
	height: 2.5rem;
}
.waveform span {
	flex: 1;
	min-width: 2px;
	border-radius: 2px;
	background: linear-gradient(180deg, #fcd34d, #f59e0b);
	animation: wave 1.4s ease-in-out infinite;
	transform-origin: bottom;
	opacity: 0.85;
}
@keyframes wave {
	0%, 100% { transform: scaleY(0.25); }
	50% { transform: scaleY(1); }
}

/* ---------- Date chip (coming-up list) ---------- */
.date-chip {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: 3.25rem;
	height: 3.25rem;
	border-radius: 0.85rem;
	background: linear-gradient(160deg, #ecfdf5, #f0fdf4);
	border: 1px solid #a7f3d0;
	color: #065f46;
	flex-shrink: 0;
}
.date-chip-month {
	font-size: 0.6rem;
	font-weight: 700;
	letter-spacing: 0.18em;
	text-transform: uppercase;
}
.date-chip-day {
	font-size: 1.1rem;
	font-weight: 800;
	line-height: 1;
}

/* ---------- Entrance animation ---------- */
.reveal-up {
	animation: reveal-up 0.8s cubic-bezier(0.2, 0.7, 0.2, 1) both;
}
@keyframes reveal-up {
	from { opacity: 0; transform: translateY(16px); }
	to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
	.orb, .live-dot, .pulse-dot, .reveal-up, .headline-char,
	.stat-shimmer, .waveform span, .verse-enter-active, .verse-leave-active,
	.tilt, .magnetic { animation: none !important; transition: none !important; }
}

/* ---------- Dark theme (hero stays dark; non-hero sections invert) ---------- */
:global([data-theme="dark"]) .stat-tile {
	background: #0f172a;
	border-color: #1e293b;
	box-shadow: 0 10px 30px -18px rgba(0, 0, 0, 0.7);
}
:global([data-theme="dark"]) .stat-tile:hover {
	border-color: rgba(167, 243, 208, 0.5);
	box-shadow: 0 20px 40px -20px rgba(16, 185, 129, 0.35);
}
:global([data-theme="dark"]) .stat-icon {
	background: linear-gradient(140deg, rgba(16, 185, 129, 0.18), rgba(99, 102, 241, 0.18));
	border-color: rgba(16, 185, 129, 0.35);
	color: #6ee7b7;
}
:global([data-theme="dark"]) .stat-number {
	background: linear-gradient(180deg, #f8fafc, #cbd5e1);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
}
:global([data-theme="dark"]) .stat-label { color: #94a3b8; }

:global([data-theme="dark"]) .date-chip {
	background: linear-gradient(160deg, rgba(16, 185, 129, 0.18), rgba(5, 150, 105, 0.12));
	border-color: rgba(16, 185, 129, 0.4);
	color: #6ee7b7;
}
</style>
