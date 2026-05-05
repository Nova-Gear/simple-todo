/**
 * Simple Todo — Frontend Application
 * Handles all UI interactions, API calls, and state management.
 */

(() => {
    "use strict";

    // ─── Constants ───────────────────────────────────────────
    const API_BASE = "/api/todos";
    const TOAST_DURATION_MS = 3000;

    // ─── DOM References ──────────────────────────────────────
    const elements = {
        addForm: document.getElementById("addTodoForm"),
        titleInput: document.getElementById("todoTitle"),
        descInput: document.getElementById("todoDescription"),
        prioritySelector: document.getElementById("prioritySelector"),
        todoList: document.getElementById("todoList"),
        emptyState: document.getElementById("emptyState"),
        loadingState: document.getElementById("loadingState"),
        filterTabs: document.getElementById("filterTabs"),
        statTotal: document.getElementById("statTotal"),
        statActive: document.getElementById("statActive"),
        statCompleted: document.getElementById("statCompleted"),
        editModal: document.getElementById("editModal"),
        editForm: document.getElementById("editTodoForm"),
        editTodoId: document.getElementById("editTodoId"),
        editTitle: document.getElementById("editTitle"),
        editDescription: document.getElementById("editDescription"),
        editPrioritySelector: document.getElementById("editPrioritySelector"),
        modalClose: document.getElementById("modalClose"),
        btnCancelEdit: document.getElementById("btnCancelEdit"),
        toastContainer: document.getElementById("toastContainer"),
    };

    // ─── State ───────────────────────────────────────────────
    let currentFilter = "all";
    let selectedPriority = "medium";
    let editPriority = "medium";

    // ─── API Helper ──────────────────────────────────────────
    async function apiRequest(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: { "Content-Type": "application/json" },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || "Something went wrong");
            }

            return data;
        } catch (error) {
            if (error.message === "Failed to fetch") {
                showToast("Unable to connect to server", "error");
            } else {
                showToast(error.message, "error");
            }
            throw error;
        }
    }

    // ─── Render Functions ────────────────────────────────────

    function renderTodos(todos) {
        elements.loadingState.style.display = "none";

        if (todos.length === 0) {
            elements.todoList.innerHTML = "";
            elements.emptyState.style.display = "block";
            return;
        }

        elements.emptyState.style.display = "none";
        elements.todoList.innerHTML = todos
            .map((todo, index) => createTodoHTML(todo, index))
            .join("");
    }

    function createTodoHTML(todo, index) {
        const completedClass = todo.isCompleted ? "completed" : "";
        const priorityClass = `priority-${todo.priority}`;
        const createdDate = formatRelativeDate(todo.createdAt);

        return `
            <li class="todo-item ${completedClass} ${priorityClass}"
                data-id="${todo.id}"
                style="animation-delay: ${index * 0.04}s">

                <div class="todo-checkbox" onclick="window.todoApp.toggleTodo(${todo.id})" title="Toggle completion">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                </div>

                <div class="todo-content" ondblclick="window.todoApp.openEditModal(${todo.id})">
                    <div class="todo-title">${escapeHTML(todo.title)}</div>
                    ${todo.description ? `<div class="todo-desc">${escapeHTML(todo.description)}</div>` : ""}
                    <div class="todo-meta">
                        <span class="todo-priority-badge ${todo.priority}">${todo.priority}</span>
                        <span class="todo-date">${createdDate}</span>
                    </div>
                </div>

                <div class="todo-actions">
                    <button class="todo-action-btn" onclick="window.todoApp.openEditModal(${todo.id})" title="Edit">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                    <button class="todo-action-btn delete" onclick="window.todoApp.deleteTodo(${todo.id})" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            </li>
        `;
    }

    function updateStats(stats) {
        animateCounter(elements.statTotal, stats.total);
        animateCounter(elements.statActive, stats.active);
        animateCounter(elements.statCompleted, stats.completed);
    }

    function animateCounter(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        if (currentValue === targetValue) return;

        const duration = 300;
        const startTime = performance.now();

        function step(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.round(currentValue + (targetValue - currentValue) * eased);

            element.textContent = value;

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }

        requestAnimationFrame(step);
    }

    // ─── Data Fetching ───────────────────────────────────────

    async function fetchTodos() {
        try {
            const filterParam = currentFilter === "all" ? "" : `?status=${currentFilter}`;
            const result = await apiRequest(filterParam);
            renderTodos(result.data);
        } catch {
            elements.loadingState.style.display = "none";
            elements.emptyState.style.display = "block";
        }
    }

    async function fetchStats() {
        try {
            const result = await apiRequest("/stats");
            updateStats(result.data);
        } catch {
            // Stats fetch failure is non-critical
        }
    }

    async function refreshAll() {
        await Promise.all([fetchTodos(), fetchStats()]);
    }

    // ─── Actions ─────────────────────────────────────────────

    async function addTodo(event) {
        event.preventDefault();

        const title = elements.titleInput.value.trim();
        if (!title) return;

        const description = elements.descInput.value.trim() || undefined;

        try {
            await apiRequest("", {
                method: "POST",
                body: JSON.stringify({ title, description, priority: selectedPriority }),
            });

            elements.titleInput.value = "";
            elements.descInput.value = "";
            elements.titleInput.focus();

            showToast("Task added successfully!", "success");
            await refreshAll();
        } catch {
            // Error already handled by apiRequest
        }
    }

    async function toggleTodo(todoId) {
        try {
            await apiRequest(`/${todoId}/toggle`, { method: "PATCH" });
            await refreshAll();
        } catch {
            // Error already handled
        }
    }

    async function deleteTodo(todoId) {
        const todoElement = document.querySelector(`.todo-item[data-id="${todoId}"]`);

        if (todoElement) {
            todoElement.style.animation = "itemRemove 0.3s ease forwards";
            await new Promise((resolve) => setTimeout(resolve, 280));
        }

        try {
            await apiRequest(`/${todoId}`, { method: "DELETE" });
            showToast("Task deleted", "info");
            await refreshAll();
        } catch {
            await refreshAll();
        }
    }

    async function openEditModal(todoId) {
        try {
            const result = await apiRequest(`/${todoId}`);
            const todo = result.data;

            elements.editTodoId.value = todo.id;
            elements.editTitle.value = todo.title;
            elements.editDescription.value = todo.description || "";

            editPriority = todo.priority;
            updatePriorityButtons(elements.editPrioritySelector, editPriority);

            elements.editModal.classList.add("active");
            elements.editTitle.focus();
        } catch {
            // Error handled
        }
    }

    function closeEditModal() {
        elements.editModal.classList.remove("active");
    }

    async function saveEdit(event) {
        event.preventDefault();

        const todoId = elements.editTodoId.value;
        const title = elements.editTitle.value.trim();
        const description = elements.editDescription.value.trim() || null;

        if (!title) {
            showToast("Title cannot be empty", "error");
            return;
        }

        try {
            await apiRequest(`/${todoId}`, {
                method: "PUT",
                body: JSON.stringify({ title, description, priority: editPriority }),
            });

            closeEditModal();
            showToast("Task updated!", "success");
            await refreshAll();
        } catch {
            // Error handled
        }
    }

    // ─── Filter ──────────────────────────────────────────────

    function setFilter(filter) {
        currentFilter = filter;

        elements.filterTabs.querySelectorAll(".filter-tab").forEach((tab) => {
            tab.classList.toggle("active", tab.dataset.filter === filter);
        });

        fetchTodos();
    }

    // ─── Priority Selection ──────────────────────────────────

    function updatePriorityButtons(container, activePriority) {
        container.querySelectorAll(".priority-btn").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.priority === activePriority);
        });
    }

    // ─── Toast Notifications ─────────────────────────────────

    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;

        const iconMap = {
            success: "✓",
            error: "✕",
            info: "ℹ",
        };

        toast.innerHTML = `<span>${iconMap[type] || ""}</span> ${escapeHTML(message)}`;
        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add("toast-exit");
            toast.addEventListener("animationend", () => toast.remove());
        }, TOAST_DURATION_MS);
    }

    // ─── Utilities ───────────────────────────────────────────

    function escapeHTML(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function formatRelativeDate(isoString) {
        if (!isoString) return "";

        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMinutes < 1) return "just now";
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    // ─── Event Bindings ──────────────────────────────────────

    function bindEvents() {
        // Add todo form
        elements.addForm.addEventListener("submit", addTodo);

        // Priority selector (add form)
        elements.prioritySelector.addEventListener("click", (event) => {
            const btn = event.target.closest(".priority-btn");
            if (!btn) return;

            selectedPriority = btn.dataset.priority;
            updatePriorityButtons(elements.prioritySelector, selectedPriority);
        });

        // Priority selector (edit modal)
        elements.editPrioritySelector.addEventListener("click", (event) => {
            const btn = event.target.closest(".priority-btn");
            if (!btn) return;

            editPriority = btn.dataset.priority;
            updatePriorityButtons(elements.editPrioritySelector, editPriority);
        });

        // Filter tabs
        elements.filterTabs.addEventListener("click", (event) => {
            const tab = event.target.closest(".filter-tab");
            if (!tab) return;

            setFilter(tab.dataset.filter);
        });

        // Edit modal
        elements.editForm.addEventListener("submit", saveEdit);
        elements.modalClose.addEventListener("click", closeEditModal);
        elements.btnCancelEdit.addEventListener("click", closeEditModal);

        // Close modal on overlay click
        elements.editModal.addEventListener("click", (event) => {
            if (event.target === elements.editModal) closeEditModal();
        });

        // Close modal on Escape key
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && elements.editModal.classList.contains("active")) {
                closeEditModal();
            }
        });
    }

    // ─── Public API (for inline event handlers) ──────────────

    window.todoApp = {
        toggleTodo,
        deleteTodo,
        openEditModal,
    };

    // ─── Initialize ──────────────────────────────────────────

    function init() {
        bindEvents();
        refreshAll();
    }

    // Wait for DOM then initialize
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
