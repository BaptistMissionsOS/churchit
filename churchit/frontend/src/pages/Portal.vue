<!-- This source code is freely given for the sake of the gospel (Matthew 10:8)
     and is licensed under MIT No Attribution (MIT-0). -->
<script setup>
import { computed, inject, onMounted, onUnmounted, ref } from "vue";
import { Button, createResource } from "frappe-ui";
import { useRouter } from "vue-router";
import LucideRadio from "~icons/lucide/radio";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideLogIn from "~icons/lucide/log-in";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucidePhone from "~icons/lucide/phone";
import LucideShield from "~icons/lucide/shield";
import LucideHome from "~icons/lucide/home";
// Each portal row's icon slug is resolved to a Lucide component. New slugs fall
// back to the Link icon so an unknown admin-added row still renders.
import LucideIdCard from "~icons/lucide/id-card";
import LucideUsers from "~icons/lucide/users";
import LucideMailCheck from "~icons/lucide/mail-check";
import LucideContact from "~icons/lucide/contact";
import LucideCalendarCheck from "~icons/lucide/calendar-check";
import LucideClipboardCheck from "~icons/lucide/clipboard-check";
import LucideHandshake from "~icons/lucide/handshake";
import LucideDoorOpen from "~icons/lucide/door-open";
import LucideUsersRound from "~icons/lucide/users-round";
import LucideUserRoundCog from "~icons/lucide/user-round-cog";
import LucideFolder from "~icons/lucide/folder";
import LucideHeart from "~icons/lucide/heart";
import LucideHandHeart from "~icons/lucide/hand-heart";
import LucideHandHelping from "~icons/lucide/hand-helping";
import LucideGift from "~icons/lucide/gift";
import LucideReceipt from "~icons/lucide/receipt";
import LucideSprout from "~icons/lucide/sprout";
import LucideBookOpen from "~icons/lucide/book-open";
import LucideBookmark from "~icons/lucide/bookmark";
import LucideNewspaper from "~icons/lucide/newspaper";
import LucideLink from "~icons/lucide/link";

const props = defineProps({
	data: { type: Object, default: null },
	loading: { type: Boolean, default: false },
});

const socket = inject("socket");
const router = useRouter();

// The portal view loads its own payload so the SPA can render the exact same
// sections and welcome copy the server-rendered /portal page shows today.
const portalData = createResource({
	url: "churchit.church_website.door.get_portal_data",
	method: "GET",
	auto: true,
	cache: "door:portal_data",
});

const ICONS = {
	"id-card": LucideIdCard,
	users: LucideUsers,
	"mail-check": LucideMailCheck,
	contact: LucideContact,
	"calendar-check": LucideCalendarCheck,
	"clipboard-check": LucideClipboardCheck,
	handshake: LucideHandshake,
	"door-open": LucideDoorOpen,
	"users-round": LucideUsersRound,
	"user-round-cog": LucideUserRoundCog,
	folder: LucideFolder,
	heart: LucideHeart,
	"hand-heart": LucideHandHeart,
	"hand-helping": LucideHandHelping,
	gift: LucideGift,
	receipt: LucideReceipt,
	sprout: LucideSprout,
	"book-open": LucideBookOpen,
	bookmark: LucideBookmark,
	newspaper: LucideNewspaper,
	link: LucideLink,
};

function iconFor(slug) {
	return ICONS[slug] || LucideLink;
}

// Routes that have a Vue page stay inside the SPA, so clicking a card never
// drops out of history. Everything else is a plain anchor to the Jinja page.
const INTERNAL_ROUTES = {
	"/function-sign-up": { name: "function-sign-up" },
};

function internalRoute(route) {
	return INTERNAL_ROUTES[route] || null;
}

const sections = computed(() => portalData.data?.sections || []);
const signedIn = computed(() => !!portalData.data?.signed_in);
const welcomeName = computed(() => portalData.data?.welcome_name || "");
const contactOn = computed(() => !!portalData.data?.contact_on);
const connectionCardOn = computed(() => !!portalData.data?.connection_card_on);
const churchPhone = computed(() => props.data?.church?.phone || "");

// Socket live indicator + realtime refresh. The portal view depends on
// Portal Settings (menu), Church Features (switched-off pages), Website
// Settings and the Church record itself, so any list_update on those doctypes
// reloads the view without the user having to refresh the tab.
const socketLive = ref(!!socket?.connected);
function onConnect() { socketLive.value = true; }
function onDisconnect() { socketLive.value = false; }

const WATCHED_DOCTYPES = new Set([
	"Portal Settings",
	"Website Settings",
	"Church Features",
	"Church",
]);
function onListUpdate(payload) {
	if (payload?.doctype && WATCHED_DOCTYPES.has(payload.doctype)) {
		portalData.reload();
	}
}

// Cursor spotlight on the hero band, painted on the GPU via CSS variables.
const heroRef = ref(null);
function onHeroMove(e) {
	const el = heroRef.value;
	if (!el) return;
	const r = el.getBoundingClientRect();
	el.style.setProperty("--sx", `${((e.clientX - r.left) / r.width) * 100}%`);
	el.style.setProperty("--sy", `${((e.clientY - r.top) / r.height) * 100}%`);
}

// Cursor-tracked glow on every card. The variable is set on the card itself so
// each tile paints its own spotlight without a global listener.
function onCardMove(e) {
	const el = e.currentTarget;
	const r = el.getBoundingClientRect();
	el.style.setProperty("--cx", `${((e.clientX - r.left) / r.width) * 100}%`);
	el.style.setProperty("--cy", `${((e.clientY - r.top) / r.height) * 100}%`);
}

// Scroll progress hairline, same look as Home. 0–1 of total document scroll.
const scrollProgress = ref(0);
function onScroll() {
	const h = document.documentElement;
	const max = h.scrollHeight - h.clientHeight;
	scrollProgress.value = max > 0 ? Math.min(1, h.scrollTop / max) : 0;
}

function goHome() {
	router.push({ name: "home" });
}

onMounted(() => {
	socket?.on("connect", onConnect);
	socket?.on("disconnect", onDisconnect);
	socket?.on("list_update", onListUpdate);
	window.addEventListener("scroll", onScroll, { passive: true });
});

onUnmounted(() => {
	socket?.off("connect", onConnect);
	socket?.off("disconnect", onDisconnect);
	socket?.off("list_update", onListUpdate);
	window.removeEventListener("scroll", onScroll);
});
</script>

<template>
	<main class="relative">
		<div class="scroll-bar" :style="{ transform: `scaleX(${scrollProgress})` }" aria-hidden="true" />

		<!-- Loading skeleton while the portal payload arrives -->
		<div
			v-if="portalData.loading && !portalData.data"
			class="mx-auto max-w-7xl animate-pulse px-6 py-10 space-y-8"
			aria-hidden="true"
		>
			<div class="h-48 rounded-[2rem] bg-slate-200/70 dark:bg-slate-800/70" />
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				<div v-for="i in 6" :key="i" class="h-56 rounded-2xl bg-slate-200/70 dark:bg-slate-800/70" />
			</div>
		</div>

		<template v-else>
			<!-- HERO: spotlight + mesh + orbs, same visual family as Home -->
			<section
				ref="heroRef"
				class="hero relative isolate overflow-hidden text-white"
				@mousemove="onHeroMove"
			>
				<div class="absolute inset-0 -z-10 bg-slate-950" />
				<div class="hero-mesh absolute inset-0 -z-10" aria-hidden="true" />
				<div class="hero-grid absolute inset-0 -z-10 opacity-[0.07]" aria-hidden="true" />
				<div class="hero-spot absolute inset-0 -z-10" aria-hidden="true" />
				<div class="orb orb-a" aria-hidden="true" />
				<div class="orb orb-b" aria-hidden="true" />

				<div class="mx-auto flex max-w-7xl flex-col gap-6 px-6 pb-20 pt-14 lg:pb-24 lg:pt-20">
					<div class="flex flex-wrap items-center gap-3 reveal-up">
						<button type="button" class="crumb" @click="goHome">
							<LucideHome class="h-3.5 w-3.5" aria-hidden="true" />
							Home
						</button>
						<span class="crumb-sep" aria-hidden="true">/</span>
						<span class="crumb crumb-current">
							<LucideShield class="h-3.5 w-3.5" aria-hidden="true" />
							Member Portal
						</span>
						<span
							class="chip chip-live"
							:class="socketLive ? 'is-on' : 'is-off'"
							style="margin-left:auto"
						>
							<span class="live-dot" />
							<LucideRadio class="h-3.5 w-3.5" aria-hidden="true" />
							{{ socketLive ? "Live" : "Offline" }}
						</span>
					</div>

					<h1 class="headline reveal-up" style="animation-delay: 80ms">
						<span class="block text-white/90">Member Portal</span>
					</h1>

					<p
						v-if="signedIn"
						class="hero-lead reveal-up"
						style="animation-delay: 160ms"
					>
						Welcome, {{ welcomeName }}. Everything for your church family in one place.
					</p>
					<p v-else class="hero-lead reveal-up" style="animation-delay: 160ms">
						Sign in to sign up for events, share prayer requests, and stay connected with your church family.
					</p>

					<div v-if="!signedIn" class="flex flex-wrap items-center gap-3 reveal-up" style="animation-delay: 240ms">
						<a href="/login?redirect-to=/portal">
							<Button variant="solid" size="lg" class="btn-glow">
								<template #prefix>
									<LucideLogIn class="h-4 w-4" />
								</template>
								Log In
							</Button>
						</a>
					</div>

					<!-- Guest helper copy mirrors the Jinja /portal page line by line. -->
					<div v-if="!signedIn" class="mt-4 space-y-2 reveal-up" style="animation-delay: 320ms">
						<p class="helper-line">
							Part of the church but no login yet? Ask
							<a v-if="contactOn" href="/contact" class="link-underline">the church office</a>
							<span v-else>the church office</span>
							to invite you.
							<span v-if="churchPhone" class="helper-phone">
								<LucidePhone class="h-3.5 w-3.5" aria-hidden="true" />
								Phone: {{ churchPhone }}
							</span>
						</p>
						<p v-if="connectionCardOn" class="helper-line">
							New here?
							<a href="/connection-card/new" class="link-underline">
								<LucideUserPlus class="inline h-3.5 w-3.5 align-text-bottom" aria-hidden="true" />
								Fill in a Connection Card
							</a>
						</p>
					</div>
				</div>
			</section>

			<!-- SECTIONS GRID -->
			<section class="mx-auto -mt-10 max-w-7xl px-6 pb-24">
				<div class="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
					<article
						v-for="(section, si) in sections"
						:key="section.title"
						class="section-card reveal-up"
						:style="{ animationDelay: `${si * 90 + 200}ms` }"
					>
						<header class="section-head">
							<span class="section-dot" aria-hidden="true" />
							<h2 class="section-title">{{ section.title }}</h2>
						</header>
						<ul class="section-list">
							<li v-for="link in section.links" :key="link.route">
								<component
									:is="internalRoute(link.route) ? 'router-link' : 'a'"
									v-bind="internalRoute(link.route)
										? { to: internalRoute(link.route) }
										: { href: link.route }"
									class="portal-link"
									@mousemove="onCardMove"
								>
									<span class="portal-link-glow" aria-hidden="true" />
									<span class="portal-link-icon">
										<component :is="iconFor(link.icon)" class="h-5 w-5" aria-hidden="true" />
									</span>
									<span class="portal-link-body">
										<span class="portal-link-title">{{ link.title }}</span>
										<span v-if="link.description" class="portal-link-desc">
											{{ link.description }}
										</span>
									</span>
									<LucideArrowRight class="portal-link-arrow h-4 w-4" aria-hidden="true" />
								</component>
							</li>
						</ul>
					</article>
				</div>

			</section>
		</template>
	</main>
</template>

<style scoped>
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
	opacity: 0.55;
	z-index: -1;
}
.orb-a {
	width: 20rem; height: 20rem; top: -4rem; left: -4rem;
	background: #6366f1; animation: float 14s ease-in-out infinite;
}
.orb-b {
	width: 18rem; height: 18rem; top: 6rem; right: -5rem;
	background: #10b981; animation: float 16s ease-in-out infinite reverse;
}
@keyframes float {
	0%, 100% { transform: translate(0, 0) scale(1); }
	50% { transform: translate(2rem, -1.5rem) scale(1.08); }
}

/* ---------- Breadcrumb chips ---------- */
.crumb {
	display: inline-flex; align-items: center; gap: 0.5rem;
	border-radius: 9999px; padding: 0.3rem 0.75rem;
	font-size: 0.72rem; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
	background: rgba(255, 255, 255, 0.06);
	border: 1px solid rgba(255, 255, 255, 0.14);
	color: rgba(255, 255, 255, 0.75);
	backdrop-filter: blur(8px);
	transition: background 0.2s ease, color 0.2s ease;
}
.crumb:hover { background: rgba(255, 255, 255, 0.12); color: #fff; }
.crumb-current {
	color: #6ee7b7;
	border-color: rgba(110, 231, 183, 0.35);
	background: rgba(16, 185, 129, 0.12);
}
.crumb-sep { color: rgba(255, 255, 255, 0.35); font-size: 0.85rem; }

.chip {
	display: inline-flex; align-items: center; gap: 0.5rem;
	border-radius: 9999px; padding: 0.35rem 0.75rem;
	font-size: 0.72rem; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase;
	background: rgba(255, 255, 255, 0.08);
	color: #fff; border: 1px solid rgba(255, 255, 255, 0.15);
	backdrop-filter: blur(8px);
}
.chip-live.is-on { color: #6ee7b7; border-color: rgba(110, 231, 183, 0.35); }
.chip-live.is-off { color: #fca5a5; border-color: rgba(252, 165, 165, 0.35); }
.live-dot {
	display: inline-block; width: 0.5rem; height: 0.5rem; border-radius: 9999px;
	background: #10b981; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
	animation: pulse 1.6s ease-out infinite;
}
.chip-live.is-off .live-dot { background: #ef4444; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
@keyframes pulse {
	0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
	70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
	100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* ---------- Headline + lead ---------- */
.headline {
	font-size: clamp(2.5rem, 5vw, 4.25rem);
	font-weight: 600;
	letter-spacing: -0.02em;
	line-height: 1.02;
	background-image: linear-gradient(90deg, #a5f3fc 0%, #ffffff 40%, #fcd34d 100%);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
}
.hero-lead {
	max-width: 44rem;
	font-size: 1.125rem;
	line-height: 1.6;
	color: rgba(255, 255, 255, 0.75);
}
.btn-glow { box-shadow: 0 10px 40px -10px rgba(16, 185, 129, 0.6); }

.helper-line {
	font-size: 0.95rem;
	color: rgba(255, 255, 255, 0.65);
	display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 1rem;
}
.helper-phone { display: inline-flex; align-items: center; gap: 0.35rem; color: rgba(255, 255, 255, 0.8); }
.link-underline {
	color: #6ee7b7; text-decoration: underline; text-underline-offset: 3px;
	text-decoration-color: rgba(110, 231, 183, 0.45);
	transition: color 0.2s ease, text-decoration-color 0.2s ease;
}
.link-underline:hover { color: #a7f3d0; text-decoration-color: #a7f3d0; }

/* ---------- Section card ---------- */
.section-card {
	position: relative;
	display: flex; flex-direction: column;
	border-radius: 1.5rem;
	background: #fff;
	border: 1px solid #e2e8f0;
	box-shadow: 0 20px 50px -30px rgba(15, 23, 42, 0.35);
	padding: 1.5rem 1.5rem 1rem;
	overflow: hidden;
	transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.section-card::after {
	content: ""; position: absolute; inset: 0; pointer-events: none;
	background: linear-gradient(135deg, rgba(16, 185, 129, 0.04), rgba(99, 102, 241, 0.03) 60%, transparent);
	opacity: 0; transition: opacity 0.25s ease;
}
.section-card:hover {
	transform: translateY(-3px);
	border-color: #c7d2fe;
	box-shadow: 0 30px 70px -30px rgba(79, 70, 229, 0.35);
}
.section-card:hover::after { opacity: 1; }

.section-head {
	display: flex; align-items: center; gap: 0.6rem;
	padding-bottom: 0.9rem;
	border-bottom: 1px dashed #e2e8f0;
	margin-bottom: 0.75rem;
}
.section-dot {
	width: 0.5rem; height: 0.5rem; border-radius: 9999px;
	background: linear-gradient(135deg, #34d399, #6366f1);
	box-shadow: 0 0 10px rgba(99, 102, 241, 0.6);
}
.section-title {
	font-size: 0.72rem;
	font-weight: 700;
	letter-spacing: 0.22em;
	text-transform: uppercase;
	color: #475569;
}
.section-list {
	display: flex; flex-direction: column; gap: 0.25rem;
}

/* ---------- Portal link row ---------- */
.portal-link {
	--cx: 50%; --cy: 50%;
	position: relative;
	display: grid;
	grid-template-columns: auto 1fr auto;
	align-items: center;
	gap: 0.9rem;
	padding: 0.75rem 0.75rem;
	border-radius: 0.9rem;
	color: #0f172a;
	text-decoration: none;
	transition: background 0.2s ease, transform 0.2s ease;
	overflow: hidden;
}
.portal-link:hover {
	background: linear-gradient(180deg, #f8fafc, #fff);
	transform: translateX(2px);
}
.portal-link-glow {
	position: absolute; inset: 0;
	background: radial-gradient(10rem 10rem at var(--cx) var(--cy), rgba(16, 185, 129, 0.08), transparent 60%);
	opacity: 0; transition: opacity 0.25s ease;
	pointer-events: none;
}
.portal-link:hover .portal-link-glow { opacity: 1; }
.portal-link-icon {
	display: inline-flex; align-items: center; justify-content: center;
	width: 2.5rem; height: 2.5rem; border-radius: 0.75rem;
	background: linear-gradient(140deg, #ecfdf5, #e0e7ff);
	border: 1px solid #a7f3d0;
	color: #047857;
	transition: transform 0.25s ease, border-color 0.25s ease;
}
.portal-link:hover .portal-link-icon {
	transform: scale(1.06) rotate(-2deg);
	border-color: #6366f1;
}
.portal-link-body {
	display: flex; flex-direction: column;
	min-width: 0;
}
.portal-link-title {
	font-size: 0.975rem;
	font-weight: 600;
	color: #0f172a;
	letter-spacing: -0.01em;
}
.portal-link-desc {
	margin-top: 0.1rem;
	font-size: 0.8rem;
	line-height: 1.4;
	color: #64748b;
}
.portal-link-arrow {
	color: #cbd5e1;
	transition: color 0.2s ease, transform 0.2s ease;
}
.portal-link:hover .portal-link-arrow {
	color: #10b981;
	transform: translateX(2px);
}

/* ---------- Reveal ---------- */
.reveal-up {
	animation: reveal-up 0.8s cubic-bezier(0.2, 0.7, 0.2, 1) both;
}
@keyframes reveal-up {
	from { opacity: 0; transform: translateY(16px); }
	to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
	.orb, .live-dot, .reveal-up, .portal-link, .portal-link-icon, .portal-link-arrow,
	.section-card { animation: none !important; transition: none !important; }
}

/* ---------- Dark theme ---------- */
:global([data-theme="dark"]) .section-card {
	background: #0f172a;
	border-color: #1e293b;
	box-shadow: 0 20px 50px -30px rgba(0, 0, 0, 0.7);
}
:global([data-theme="dark"]) .section-card:hover {
	border-color: #4f46e5;
	box-shadow: 0 30px 70px -30px rgba(79, 70, 229, 0.55);
}
:global([data-theme="dark"]) .section-head { border-bottom-color: #1e293b; }
:global([data-theme="dark"]) .section-title { color: #94a3b8; }
:global([data-theme="dark"]) .portal-link { color: #e2e8f0; }
:global([data-theme="dark"]) .portal-link:hover {
	background: linear-gradient(180deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.6));
}
:global([data-theme="dark"]) .portal-link-icon {
	background: linear-gradient(140deg, rgba(16, 185, 129, 0.15), rgba(99, 102, 241, 0.18));
	border-color: rgba(16, 185, 129, 0.35);
	color: #6ee7b7;
}
:global([data-theme="dark"]) .portal-link:hover .portal-link-icon { border-color: #818cf8; }
:global([data-theme="dark"]) .portal-link-title { color: #f1f5f9; }
:global([data-theme="dark"]) .portal-link-desc { color: #94a3b8; }
:global([data-theme="dark"]) .portal-link-arrow { color: #475569; }
:global([data-theme="dark"]) .portal-link:hover .portal-link-arrow { color: #34d399; }

/* ---------- Keyboard focus ---------- */
.crumb:focus-visible,
.portal-link:focus-visible {
	outline: 2px solid #10b981;
	outline-offset: 2px;
}
</style>
