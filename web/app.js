const state = { token: localStorage.getItem("taskflow_token"), user: null, clients: [], orders: [] };
const $ = (selector) => document.querySelector(selector);

function showToast(message, isError = false) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.hidden = false;
  toast.classList.toggle("error", isError);
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => { toast.hidden = true; }, 4200);
}

function formatApiError(body, statusCode) {
  const detail = body?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
  return typeof detail === "string" ? detail : `Ошибка HTTP ${statusCode}`;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(formatApiError(body, response.status));
  }
  return response.status === 204 ? null : response.json();
}

function formPayload(form) { return Object.fromEntries(new FormData(form).entries()); }

function showApp() {
  $("#auth-view").hidden = true;
  $("#app-view").hidden = false;
  $("#current-user").textContent = `${state.user.full_name} · ${state.user.role}`;
  $("#user-name").textContent = state.user.full_name.split(" ")[0];
  refresh();
}

function showAuth() { $("#auth-view").hidden = false; $("#app-view").hidden = true; }

function setAuthTab(tab) {
  document.querySelectorAll("[data-auth-tab]").forEach((button) => button.classList.toggle("active", button.dataset.authTab === tab));
  $("#login-form").hidden = tab !== "login";
  $("#register-form").hidden = tab !== "register";
}

function renderStats(dashboard) {
  $("#clients-count").textContent = dashboard.total_clients;
  $("#orders-count").textContent = dashboard.total_orders;
  $("#active-count").textContent = dashboard.active_orders;
  $("#revenue-count").textContent = `${dashboard.total_revenue.toLocaleString("ru-RU")} ₽`;
}

function renderClients() {
  const list = $("#clients-list");
  list.replaceChildren();
  $("#clients-total").textContent = state.clients.length;
  if (!state.clients.length) { list.innerHTML = '<div class="empty">Добавь первого клиента.</div>'; return; }
  const template = $("#client-template");
  state.clients.forEach((client) => {
    const item = template.content.cloneNode(true);
    item.querySelector(".avatar").textContent = client.name.slice(0, 1).toUpperCase();
    item.querySelector(".client-name").textContent = client.name;
    item.querySelector(".client-meta").textContent = client.company || client.email || "Контакты не указаны";
    list.appendChild(item);
  });
  const select = $("#client-select");
  const current = select.value;
  select.replaceChildren();
  if (!state.clients.length) select.add(new Option("Сначала добавь клиента", ""));
  state.clients.forEach((client) => select.add(new Option(`${client.name}${client.company ? ` · ${client.company}` : ""}`, client.id)));
  if (current) select.value = current;
}

const statusLabels = { new: "Новый", in_progress: "В работе", done: "Готов", cancelled: "Отменен" };
const nextStatus = { new: "in_progress", in_progress: "done" };

function renderOrders() {
  const list = $("#orders-list");
  list.replaceChildren();
  $("#orders-total").textContent = state.orders.length;
  if (!state.orders.length) { list.innerHTML = '<div class="empty">Заказов пока нет.</div>'; return; }
  const template = $("#order-template");
  state.orders.forEach((order) => {
    const item = template.content.cloneNode(true);
    const status = item.querySelector(".order-status");
    status.textContent = statusLabels[order.status];
    if (order.status === "in_progress") status.classList.add("progress");
    if (order.status === "done") status.classList.add("done");
    if (order.status === "cancelled") status.classList.add("cancelled");
    item.querySelector(".order-title").textContent = order.title;
    item.querySelector(".order-client").textContent = order.client_name || "Клиент удален";
    item.querySelector(".order-amount").textContent = `${order.amount.toLocaleString("ru-RU")} ₽`;
    const action = item.querySelector(".status-button");
    if (nextStatus[order.status]) {
      action.textContent = `→ ${statusLabels[nextStatus[order.status]]}`;
      action.addEventListener("click", () => updateOrderStatus(order.id, nextStatus[order.status]));
    } else action.hidden = true;
    list.appendChild(item);
  });
}

async function refresh() {
  try {
    const [dashboard, clients, orders] = await Promise.all([request("/api/dashboard"), request("/api/clients"), request("/api/orders")]);
    state.clients = clients; state.orders = orders;
    renderStats(dashboard); renderClients(); renderOrders();
  } catch (error) {
    if (error.message.includes("токен") || error.message.includes("Bearer")) logout(false);
    else showToast(error.message, true);
  }
}

async function updateOrderStatus(id, status) {
  try { await request(`/api/orders/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }); await refresh(); showToast("Статус заказа обновлен"); }
  catch (error) { showToast(error.message, true); }
}

function saveSession(data) { state.token = data.access_token; state.user = data.user; localStorage.setItem("taskflow_token", state.token); showApp(); }
function logout(showMessage = true) { state.token = null; state.user = null; localStorage.removeItem("taskflow_token"); showAuth(); if (showMessage) showToast("Вы вышли из аккаунта"); }

document.querySelectorAll("[data-auth-tab]").forEach((button) => button.addEventListener("click", () => setAuthTab(button.dataset.authTab)));
$("#login-form").addEventListener("submit", async (event) => { event.preventDefault(); try { saveSession(await request("/api/auth/login", { method: "POST", body: JSON.stringify(formPayload(event.currentTarget)) })); } catch (error) { showToast(error.message, true); } });
$("#register-form").addEventListener("submit", async (event) => { event.preventDefault(); try { saveSession(await request("/api/auth/register", { method: "POST", body: JSON.stringify(formPayload(event.currentTarget)) })); } catch (error) { showToast(error.message, true); } });
$("#logout-button").addEventListener("click", () => logout());
$("#refresh-button").addEventListener("click", refresh);
$("#client-form").addEventListener("submit", async (event) => { event.preventDefault(); const formElement = event.currentTarget; try { await request("/api/clients", { method: "POST", body: JSON.stringify(formPayload(formElement)) }); formElement.reset(); await refresh(); showToast("Клиент добавлен"); } catch (error) { showToast(error.message, true); } });
$("#order-form").addEventListener("submit", async (event) => { event.preventDefault(); const formElement = event.currentTarget; const payload = formPayload(formElement); payload.client_id = Number(payload.client_id); payload.amount = Number(payload.amount || 0); try { await request("/api/orders", { method: "POST", body: JSON.stringify(payload) }); formElement.reset(); await refresh(); showToast("Заказ создан"); } catch (error) { showToast(error.message, true); } });

async function restoreSession() {
  if (!state.token) return showAuth();
  try { state.user = await request("/api/auth/me"); showApp(); } catch { logout(false); }
}
restoreSession();
