// This source code is freely given for the sake of the gospel (Matthew 10:8)
// and is licensed under MIT No Attribution (MIT-0).

import { ref, watchEffect } from "vue";

const STORAGE_KEY = "kiosk:theme";
const prefersDark = typeof window !== "undefined" && window.matchMedia
	? window.matchMedia("(prefers-color-scheme: dark)")
	: null;

function initialTheme() {
	if (typeof window === "undefined") return "light";
	const saved = window.localStorage.getItem(STORAGE_KEY);
	if (saved === "light" || saved === "dark") return saved;
	return prefersDark?.matches ? "dark" : "light";
}

// Shared across the app so every consumer sees the same value.
const theme = ref(initialTheme());

if (typeof window !== "undefined") {
	watchEffect(() => {
		document.documentElement.setAttribute("data-theme", theme.value);
		document.documentElement.style.colorScheme = theme.value;
	});

	// Follow OS changes as long as the user has not chosen manually.
	prefersDark?.addEventListener?.("change", (e) => {
		if (!window.localStorage.getItem(STORAGE_KEY)) {
			theme.value = e.matches ? "dark" : "light";
		}
	});
}

export function useTheme() {
	function setTheme(next) {
		theme.value = next === "dark" ? "dark" : "light";
		if (typeof window !== "undefined") {
			window.localStorage.setItem(STORAGE_KEY, theme.value);
		}
	}

	function toggleTheme() {
		setTheme(theme.value === "dark" ? "light" : "dark");
	}

	return { theme, setTheme, toggleTheme };
}
