<!-- This source code is freely given for the sake of the gospel (Matthew 10:8)
     and is licensed under MIT No Attribution (MIT-0). -->
<script setup>
import { computed, inject, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { Button, FormControl, createResource } from "frappe-ui";
import { useRouter } from "vue-router";
import LucideCalendarCheck from "~icons/lucide/calendar-check";
import LucideShield from "~icons/lucide/shield";
import LucideHome from "~icons/lucide/home";
import LucideRadio from "~icons/lucide/radio";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideCheck from "~icons/lucide/check";
import LucideCheckCircle2 from "~icons/lucide/check-circle-2";
import LucideClock from "~icons/lucide/clock";
import LucideCalendar from "~icons/lucide/calendar";
import LucidePackage from "~icons/lucide/package";
import LucideNotebookPen from "~icons/lucide/notebook-pen";
import LucideLogIn from "~icons/lucide/log-in";
import LucideListChecks from "~icons/lucide/list-checks";

const props = defineProps({
	data: { type: Object, default: null },
	loading: { type: Boolean, default: false },
});

const router = useRouter();
const socket = inject("socket");

// Page payload: open functions and whether the reader may sign up at all.
const signUpData = createResource({
	url: "churchit.church_website.kiosk.get_function_sign_up_data",
	method: "GET",
	auto: true,
});

// Per-function item totals come from the existing web form helper so the
// numbers match what the Jinja form shows today, unchanged on the server.
const itemsResource = createResource({
	url: "churchit.church_ministries.web_form.function_sign_up.function_sign_up.get_function_sign_up_items",
	method: "GET",
	auto: false,
});

// Create the Function Sign-Up through Frappe's standard client API so the
// doctype controller runs its full validate — permissions, church scope,
// hold expiry, confirmation emails — exactly as it does for the Jinja form.
const signUp = createResource({
	url: "frappe.client.insert",
	method: "POST",
	onSuccess(doc) {
		submitted.value = { name: doc?.name || "" };
	},
});

const signedIn = computed(() => !!signUpData.data?.signed_in);
const functions = computed(() => signUpData.data?.functions || []);
const person = computed(() => signUpData.data?.person || "");
const intro = computed(() => signUpData.data?.intro || "");
const successMessage = computed(() => signUpData.data?.success_message || "");

// Form state kept in a single ref so reset is trivial.
const form = ref({
	function: "",
	attending: 1,
	notes: "",
});
const items = ref([]); // [{ item, quantity_needed, quantity_signed_up, my_quantity }]
const submitted = ref(null); // { name } once the sign-up saved
const successRef = ref(null);

watch(submitted, async (val) => {
	if (val) {
		await nextTick();
		successRef.value?.focus();
	}
});

const chosenFunction = computed(() =>
	functions.value.find((f) => f.name === form.value.function) || null
);

watch(
	() => form.value.function,
	(name) => {
		items.value = [];
		if (name) {
			itemsResource.submit({ function: name });
		}
	},
);

watch(
	() => itemsResource.data,
	(rows) => {
		items.value = (rows || []).map((row) => ({
			item: row.item,
			quantity_needed: row.quantity_needed || 0,
			quantity_signed_up: row.quantity_signed_up || 0,
			my_quantity: 0,
		}));
	},
);

function formatDate(d) {
	if (!d) return "";
	return new Date(`${d}T00:00:00`).toLocaleDateString(undefined, {
		weekday: "long",
		month: "long",
		day: "numeric",
		year: "numeric",
	});
}

function formatTime(t) {
	if (!t) return "";
	const [h, m] = t.split(":");
	const date = new Date();
	date.setHours(+h, +m);
	return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function remaining(row) {
	const need = row.quantity_needed || 0;
	const taken = row.quantity_signed_up || 0;
	return Math.max(0, need - taken);
}

function fillPercent(row) {
	const need = row.quantity_needed || 0;
	if (!need) return 0;
	return Math.min(100, Math.round(((row.quantity_signed_up || 0) / need) * 100));
}

function submit() {
	if (!form.value.function) return;
	const table_iprj = items.value
		.filter((row) => (row.my_quantity || 0) > 0)
		.map((row) => ({
			item: row.item,
			my_quantity: row.my_quantity,
			quantity_needed: row.quantity_needed,
			quantity_signed_up: row.quantity_signed_up,
		}));
	signUp.submit({
		doc: {
			doctype: "Function Sign-Up",
			function: form.value.function,
			person: person.value,
			attending: form.value.attending ? 1 : 0,
			notes: form.value.notes,
			table_iprj,
		},
	});
}

function goPortal() {
	router.push({ name: "portal" });
}

function goHome() {
	router.push({ name: "home" });
}

// Socket live indicator + realtime refresh.
//   - A Function Sign-Up inserted or updated anywhere reloads the item totals
//     so "Quantity Signed Up" is always current, and re-pulls the open-functions
//     list so a function closing or filling up disappears without a page refresh.
//   - A Function record changing (published, closed, times changed) also refreshes
//     the list of what the member can sign up for.
const socketLive = ref(!!socket?.connected);
function onConnect() { socketLive.value = true; }
function onDisconnect() { socketLive.value = false; }
function onListUpdate(payload) {
	const dt = payload?.doctype;
	if (dt === "Function Sign-Up") {
		if (form.value.function) itemsResource.submit({ function: form.value.function });
		signUpData.reload();
	} else if (dt === "Function") {
		signUpData.reload();
	}
}

// Cursor spotlight on hero, same visual language as Home and Portal.
const heroRef = ref(null);
function onHeroMove(e) {
	const el = heroRef.value;
	if (!el) return;
	const r = el.getBoundingClientRect();
	el.style.setProperty("--sx", `${((e.clientX - r.left) / r.width) * 100}%`);
	el.style.setProperty("--sy", `${((e.clientY - r.top) / r.height) * 100}%`);
}

const scrollProgress = ref(0);
function onScroll() {
	const h = document.documentElement;
	const max = h.scrollHeight - h.clientHeight;
	scrollProgress.value = max > 0 ? Math.min(1, h.scrollTop / max) : 0;
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

			<div class="mx-auto flex max-w-5xl flex-col gap-6 px-6 pb-20 pt-14 lg:pb-24 lg:pt-20">
				<div class="flex flex-wrap items-center gap-3 reveal-up">
					<button type="button" class="crumb" @click="goHome">
						<LucideHome class="h-3.5 w-3.5" aria-hidden="true" />
						Home
					</button>
					<span class="crumb-sep" aria-hidden="true">/</span>
					<button type="button" class="crumb" @click="goPortal">
						<LucideShield class="h-3.5 w-3.5" aria-hidden="true" />
						Portal
					</button>
					<span class="crumb-sep" aria-hidden="true">/</span>
					<span class="crumb crumb-current">
						<LucideCalendarCheck class="h-3.5 w-3.5" aria-hidden="true" />
						Function Sign-Up
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
					Function Sign-Up
				</h1>
				<p class="hero-lead reveal-up" style="animation-delay: 160ms">
					{{ intro || "Sign up to let us know you plan to attend an upcoming function." }}
				</p>
			</div>
		</section>

		<section class="mx-auto -mt-10 max-w-5xl px-6 pb-24">
			<!-- Loading skeleton -->
			<div
				v-if="signUpData.loading && !signUpData.data"
				class="animate-pulse space-y-6"
				aria-hidden="true"
			>
				<div class="h-72 rounded-3xl bg-slate-200/70 dark:bg-slate-800/70" />
				<div class="h-40 rounded-3xl bg-slate-200/70 dark:bg-slate-800/70" />
			</div>

			<!-- Guest state: the web form has login_required=1, so the Vue page sends
				 the member to the same login redirect the Jinja form uses. -->
			<article
				v-else-if="!signedIn"
				class="form-card reveal-up"
				style="animation-delay: 200ms"
			>
				<div class="mt-2 flex flex-wrap gap-3">
					<a href="/login?redirect-to=/kiosk/function-sign-up">
						<Button variant="solid" size="lg" class="btn-glow">
							<template #prefix>
								<LucideLogIn class="h-4 w-4" />
							</template>
							Log In
						</Button>
					</a>
				</div>
			</article>

			<!-- Success state: title and message are the web form's own fields. -->
			<article
				v-else-if="submitted"
				class="form-card reveal-up"
				style="animation-delay: 200ms"
			>
				<div class="form-card-head">
					<span class="success-icon">
						<LucideCheckCircle2 class="h-6 w-6" aria-hidden="true" />
					</span>
					<h2 ref="successRef" tabindex="-1" class="form-card-title focus:outline-none">Signed Up</h2>
				</div>
				<p class="form-card-lead">
					{{ successMessage || "You are signed up. Your sign-ups list shows the status." }}
				</p>
				<div class="mt-6 flex flex-wrap gap-3">
					<a href="/function-sign-up/list">
						<Button variant="solid" class="btn-glow">
							<template #prefix>
								<LucideListChecks class="h-4 w-4" />
							</template>
							Your Function Sign-Ups
						</Button>
					</a>
				</div>
			</article>


			<!-- Form -->
			<form v-else class="space-y-6" @submit.prevent="submit">
				<!-- Step 1: choose a function -->
				<article class="form-card reveal-up" style="animation-delay: 200ms">
					<div class="form-card-head">
						<span class="step-badge">1</span>
						<h2 class="form-card-title">Function</h2>
					</div>
					<div class="function-grid">
						<button
							v-for="fn in functions"
							:key="fn.name"
							type="button"
							class="function-tile"
							:class="{ 'is-active': form.function === fn.name }"
							@click="form.function = fn.name"
						>
							<span class="function-tile-top">
								<span class="function-tile-month">
									{{ fn.start_date ? new Date(fn.start_date + 'T00:00:00').toLocaleDateString(undefined, { month: 'short' }).toUpperCase() : '' }}
								</span>
								<span class="function-tile-day">
									{{ fn.start_date ? new Date(fn.start_date + 'T00:00:00').getDate() : '—' }}
								</span>
							</span>
							<span class="function-tile-body">
								<span class="function-tile-title">{{ fn.function_name }}</span>
								<span class="function-tile-when">
									<LucideClock class="h-3 w-3 shrink-0" aria-hidden="true" />
									{{ formatDate(fn.start_date) }}
									<span v-if="!fn.all_day && fn.start_time"> · {{ formatTime(fn.start_time) }}</span>
									<span v-else-if="fn.all_day"> · all day</span>
								</span>
							</span>
							<span class="function-tile-check" aria-hidden="true">
								<LucideCheck class="h-3.5 w-3.5" />
							</span>
						</button>
					</div>
				</article>

				<template v-if="form.function">
					<!-- Step 2: attending -->
					<article class="form-card reveal-up">
						<div class="form-card-head">
							<span class="step-badge">2</span>
							<h2 class="form-card-title">Attending</h2>
						</div>
						<label class="attending-row">
							<FormControl
								type="checkbox"
								v-model="form.attending"
							/>
							<span class="attending-desc">Check this if you plan to attend this function.</span>
						</label>
					</article>

					<!-- Step 3: items I can bring -->
					<article v-if="items.length" class="form-card reveal-up">
						<div class="form-card-head">
							<span class="step-badge">3</span>
							<LucidePackage class="h-5 w-5 text-emerald-600" aria-hidden="true" />
							<h2 class="form-card-title">Items I Can Bring</h2>
						</div>
						<div class="items-table-wrap">
							<table class="items-table">
								<thead>
									<tr>
										<th>Item</th>
										<th class="num">Quantity Needed</th>
										<th class="num">Quantity Signed Up</th>
										<th class="num">My Quantity</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="row in items" :key="row.item">
										<td>
											<div class="item-cell">
												<span class="item-name">{{ row.item }}</span>
												<span
													class="item-progress"
													:aria-label="`${row.quantity_signed_up} of ${row.quantity_needed} signed up`"
												>
													<span
														class="item-progress-bar"
														:style="{ width: fillPercent(row) + '%' }"
													/>
												</span>
											</div>
										</td>
										<td class="num">{{ row.quantity_needed }}</td>
										<td class="num">{{ row.quantity_signed_up }}</td>
										<td class="num" style="width: 7rem">
											<FormControl
												type="number"
												:min="0"
												:max="remaining(row) || undefined"
												:placeholder="String(remaining(row))"
												:aria-label="`My quantity for ${row.item}, up to ${remaining(row)}`"
												v-model="row.my_quantity"
											/>
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</article>

					<!-- Step 4: notes -->
					<article class="form-card reveal-up">
						<div class="form-card-head">
							<span class="step-badge">{{ items.length ? 4 : 3 }}</span>
							<LucideNotebookPen class="h-5 w-5 text-emerald-600" aria-hidden="true" />
							<h2 class="form-card-title">Notes</h2>
						</div>
						<FormControl
							type="textarea"
							:rows="4"
							v-model="form.notes"
						/>
					</article>

					<!-- Submit: the button label comes straight from the web form's button_label. -->
					<article class="summary-card reveal-up">
						<div class="summary-left">
							<p class="summary-title">{{ chosenFunction?.function_name }}</p>
							<p class="summary-when">
								<LucideCalendar class="h-3.5 w-3.5" aria-hidden="true" />
								{{ formatDate(chosenFunction?.start_date) }}
								<span v-if="chosenFunction && !chosenFunction.all_day && chosenFunction.start_time"> · {{ formatTime(chosenFunction.start_time) }}</span>
							</p>
						</div>
						<div class="summary-right">
							<p v-if="signUp.error" class="error-line">
								{{ signUp.error?.messages?.[0] || signUp.error?.message || signUp.error }}
							</p>
							<Button
								type="submit"
								variant="solid"
								size="lg"
								class="btn-glow"
								:loading="signUp.loading"
							>
								<template #prefix>
									<LucideCalendarCheck class="h-4 w-4" />
								</template>
								Sign Up
								<template #suffix>
									<LucideArrowRight class="h-4 w-4" />
								</template>
							</Button>
						</div>
					</article>
				</template>
			</form>
		</section>
	</main>
</template>

<style scoped>
.scroll-bar {
	position: fixed; top: 0; left: 0; right: 0; height: 2px;
	background: linear-gradient(90deg, #a5f3fc, #34d399, #fcd34d);
	transform-origin: 0 50%; transform: scaleX(0);
	z-index: 50; pointer-events: none;
}

/* ---------- Hero ---------- */
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
	position: absolute; border-radius: 9999px; filter: blur(60px);
	pointer-events: none; opacity: 0.55; z-index: -1;
}
.orb-a { width: 20rem; height: 20rem; top: -4rem; left: -4rem; background: #6366f1; animation: float 14s ease-in-out infinite; }
.orb-b { width: 18rem; height: 18rem; top: 6rem; right: -5rem; background: #10b981; animation: float 16s ease-in-out infinite reverse; }
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
	color: #6ee7b7; border-color: rgba(110, 231, 183, 0.35);
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

.headline {
	font-size: clamp(2.5rem, 5vw, 4rem);
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

/* ---------- Form cards ---------- */
.form-card {
	position: relative;
	border-radius: 1.5rem;
	background: #fff;
	border: 1px solid #e2e8f0;
	box-shadow: 0 20px 50px -30px rgba(15, 23, 42, 0.3);
	padding: 1.75rem;
	overflow: hidden;
}
.form-card-head {
	display: flex; align-items: center; gap: 0.75rem;
	padding-bottom: 1rem;
	border-bottom: 1px dashed #e2e8f0;
	margin-bottom: 1.25rem;
}
.form-card-title {
	font-size: 0.75rem;
	font-weight: 700;
	letter-spacing: 0.22em;
	text-transform: uppercase;
	color: #0f172a;
}
.form-card-lead {
	font-size: 1rem;
	line-height: 1.6;
	color: #475569;
}
.btn-glow { box-shadow: 0 10px 40px -10px rgba(16, 185, 129, 0.6); }

.step-badge {
	display: inline-flex; align-items: center; justify-content: center;
	width: 1.75rem; height: 1.75rem; border-radius: 9999px;
	background: linear-gradient(140deg, #10b981, #6366f1);
	color: #fff; font-size: 0.8rem; font-weight: 700;
	box-shadow: 0 6px 20px -10px rgba(16, 185, 129, 0.8);
}

.success-icon {
	display: inline-flex; align-items: center; justify-content: center;
	width: 2.25rem; height: 2.25rem; border-radius: 9999px;
	background: linear-gradient(140deg, #ecfdf5, #d1fae5);
	border: 1px solid #a7f3d0;
	color: #047857;
}

/* ---------- Function tiles ---------- */
.function-grid {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
	gap: 0.75rem;
}
.function-tile {
	position: relative;
	display: grid;
	grid-template-columns: auto 1fr auto;
	align-items: center;
	gap: 0.9rem;
	padding: 0.8rem 0.9rem;
	border-radius: 1rem;
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	text-align: left;
	cursor: pointer;
	transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.function-tile:hover {
	background: #fff;
	border-color: #a7f3d0;
	transform: translateY(-1px);
	box-shadow: 0 15px 40px -25px rgba(16, 185, 129, 0.4);
}
.function-tile.is-active {
	background: linear-gradient(135deg, #ecfdf5, #eef2ff);
	border-color: #6366f1;
	box-shadow: 0 20px 50px -25px rgba(99, 102, 241, 0.4);
}
.function-tile-top {
	display: flex; flex-direction: column; align-items: center; justify-content: center;
	width: 3rem; height: 3rem; border-radius: 0.75rem;
	background: #fff; border: 1px solid #c7d2fe;
	color: #4338ca;
}
.function-tile.is-active .function-tile-top {
	background: linear-gradient(135deg, #a7f3d0, #c7d2fe);
	border-color: transparent; color: #1e293b;
}
.function-tile-month { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.18em; }
.function-tile-day { font-size: 1.1rem; font-weight: 800; line-height: 1; }
.function-tile-body { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
.function-tile-title {
	font-size: 0.95rem; font-weight: 600; color: #0f172a;
	white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.function-tile-when {
	display: inline-flex; align-items: center; gap: 0.3rem;
	font-size: 0.75rem; color: #64748b;
}
.function-tile-check {
	display: inline-flex; align-items: center; justify-content: center;
	width: 1.5rem; height: 1.5rem; border-radius: 9999px;
	background: #e2e8f0; color: transparent;
	transition: background 0.2s ease, color 0.2s ease;
}
.function-tile.is-active .function-tile-check {
	background: #10b981; color: #fff;
}

/* ---------- Attending row ---------- */
.attending-row {
	display: flex; align-items: flex-start; gap: 0.75rem;
	cursor: pointer;
}
.attending-title {
	display: block;
	font-size: 1rem; font-weight: 600; color: #0f172a;
}
.attending-desc {
	display: block;
	font-size: 0.875rem; color: #64748b; margin-top: 0.15rem;
}

/* ---------- Items table ---------- */
.items-table-wrap {
	overflow-x: auto;
	border-radius: 1rem;
	border: 1px solid #e2e8f0;
}
.items-table {
	width: 100%;
	border-collapse: collapse;
	font-size: 0.9rem;
}
.items-table thead th {
	position: sticky; top: 0;
	background: linear-gradient(180deg, #f8fafc, #f1f5f9);
	color: #475569;
	font-size: 0.68rem;
	font-weight: 700;
	letter-spacing: 0.15em;
	text-transform: uppercase;
	padding: 0.75rem 1rem;
	border-bottom: 1px solid #e2e8f0;
	text-align: left;
}
.items-table thead th.num { text-align: right; }
.items-table tbody td {
	padding: 0.85rem 1rem;
	border-bottom: 1px solid #f1f5f9;
	vertical-align: middle;
	color: #0f172a;
}
.items-table tbody tr:last-child td { border-bottom: none; }
.items-table tbody td.num {
	text-align: right;
	font-variant-numeric: tabular-nums;
	color: #334155;
}
.item-cell { display: flex; flex-direction: column; gap: 0.25rem; }
.item-name { font-weight: 600; color: #0f172a; }
.item-progress {
	display: block;
	width: 100%; max-width: 12rem;
	height: 4px;
	border-radius: 9999px;
	background: #e2e8f0;
	overflow: hidden;
}
.item-progress-bar {
	display: block; height: 100%;
	background: linear-gradient(90deg, #10b981, #6366f1);
	transition: width 0.4s ease;
}
.item-remain {
	font-size: 0.72rem; color: #64748b;
	letter-spacing: 0.02em;
}

/* ---------- Summary / submit ---------- */
.summary-card {
	display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: center;
	border-radius: 1.5rem;
	padding: 1.5rem 1.75rem;
	background: linear-gradient(135deg, #0f172a, #1e293b);
	color: #fff;
	border: 1px solid rgba(255, 255, 255, 0.08);
	box-shadow: 0 25px 60px -25px rgba(2, 6, 23, 0.6);
}
.summary-left { flex: 1 1 18rem; }
.summary-label {
	font-size: 0.7rem;
	font-weight: 700;
	letter-spacing: 0.22em;
	text-transform: uppercase;
	color: rgba(255, 255, 255, 0.55);
}
.summary-title {
	margin-top: 0.3rem;
	font-size: 1.35rem;
	font-weight: 600;
	letter-spacing: -0.01em;
}
.summary-when {
	display: inline-flex; align-items: center; gap: 0.4rem;
	margin-top: 0.4rem;
	font-size: 0.875rem;
	color: rgba(255, 255, 255, 0.65);
}
.summary-right { display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-end; }
.error-line {
	font-size: 0.85rem; color: #fca5a5;
	background: rgba(239, 68, 68, 0.12);
	padding: 0.35rem 0.7rem; border-radius: 0.75rem;
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
	.orb, .live-dot, .reveal-up, .function-tile, .form-card,
	.item-progress-bar { animation: none !important; transition: none !important; }
}

/* ---------- Keyboard focus ---------- */
.crumb:focus-visible,
.function-tile:focus-visible {
	outline: 2px solid #10b981;
	outline-offset: 2px;
}

/* ---------- Dark theme ---------- */
:global([data-theme="dark"]) .form-card {
	background: #0f172a;
	border-color: #1e293b;
	box-shadow: 0 20px 50px -30px rgba(0, 0, 0, 0.7);
}
:global([data-theme="dark"]) .form-card-head { border-bottom-color: #1e293b; }
:global([data-theme="dark"]) .form-card-title { color: #f1f5f9; }
:global([data-theme="dark"]) .form-card-lead { color: #94a3b8; }
:global([data-theme="dark"]) .attending-desc { color: #94a3b8; }

:global([data-theme="dark"]) .function-tile {
	background: #0b1226;
	border-color: #1e293b;
}
:global([data-theme="dark"]) .function-tile:hover {
	background: #111c33;
	border-color: rgba(167, 243, 208, 0.45);
}
:global([data-theme="dark"]) .function-tile.is-active {
	background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(99, 102, 241, 0.18));
	border-color: #818cf8;
}
:global([data-theme="dark"]) .function-tile-top {
	background: #0f172a; border-color: rgba(99, 102, 241, 0.4); color: #c7d2fe;
}
:global([data-theme="dark"]) .function-tile-title { color: #f1f5f9; }
:global([data-theme="dark"]) .function-tile-when { color: #94a3b8; }
:global([data-theme="dark"]) .function-tile-check { background: #1e293b; }

:global([data-theme="dark"]) .items-table-wrap { border-color: #1e293b; }
:global([data-theme="dark"]) .items-table thead th {
	background: linear-gradient(180deg, #0b1226, #0f172a);
	color: #94a3b8;
	border-bottom-color: #1e293b;
}
:global([data-theme="dark"]) .items-table tbody td {
	border-bottom-color: #1e293b;
	color: #e2e8f0;
}
:global([data-theme="dark"]) .items-table tbody td.num { color: #cbd5e1; }
:global([data-theme="dark"]) .item-name { color: #f1f5f9; }
:global([data-theme="dark"]) .item-progress { background: #1e293b; }
</style>
