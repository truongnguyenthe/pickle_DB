// Cấu hình Nodes
const NODES = {
  primary: "http://127.0.0.1:4000",
  followers: [
    "http://127.0.0.1:4001",
    "http://127.0.0.1:4002",
    "http://127.0.0.1:4003",
  ],
};

let currentNode = NODES.primary;
let tasks = [];
let currentFilter = "all";
let isFailover = false;
let healthCheckInterval;

document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
});

async function initializeApp() {
  await checkNodeHealth();
  await loadTasks();
  startHealthCheck();
}

// Kiểm tra sức khỏe của nodes
async function checkNodeHealth() {
  const primaryStatus = await checkNode(NODES.primary);

  // Nếu primary sống → failback nếu đang ở follower
  if (primaryStatus && currentNode !== NODES.primary) {
    await performFailback();
    return;
  }

  // Nếu primary chết → thử lần lượt followers
  if (!primaryStatus && currentNode === NODES.primary) {
    for (const follower of NODES.followers) {
      const status = await checkNode(follower);
      if (status) {
        await performFailover(follower);
        return;
      }
    }

    // Nếu không node nào sống
    console.warn("🚨 Không có node nào khả dụng!");
    showFailoverAlert("⚠️ Tất cả node đều không khả dụng!");
  }

  updateCurrentNodeUI();
}

async function checkNode(url) {
  try {
    const response = await fetch(`${url}/status`, {
      method: "GET",
      signal: AbortSignal.timeout(2000),
    });
    const data = await response.json();
    return data.status !== undefined || data.is_leader !== undefined;
  } catch (error) {
    return false;
  }
}

function updateCurrentNodeUI() {
  const nodeUrlEl = document.getElementById("nodeUrl");
  const statusEl = document.getElementById("nodeStatus");
  const displayEl = document.getElementById("currentNodeDisplay");

  nodeUrlEl.textContent = currentNode;

  if (currentNode === NODES.primary) {
    displayEl.classList.remove("standby", "active");
    displayEl.style.backgroundColor = "var(--primary-red)";
  } else {
    displayEl.classList.add("active");
    displayEl.style.backgroundColor = "var(--primary-green)";
  }
}

async function performFailover(targetNode) {
  console.log(`🔄 Performing failover to ${targetNode}...`);
  isFailover = true;
  currentNode = targetNode;

  const alertEl = document.getElementById("failoverAlert");
  const messageEl = document.getElementById("failoverMessage");
  messageEl.textContent = ` Node chính không khả dụng! Đã chuyển sang ${targetNode}`;
  alertEl.classList.add("show");

  updateCurrentNodeUI();
  await loadTasks();

  setTimeout(() => {
    alertEl.classList.remove("show");
  }, 5000);
}

async function performFailback() {
  console.log("✅ Performing failback to primary node...");
  isFailover = false;
  currentNode = NODES.primary;

  showFailoverAlert("✅ Node chính (4000) đã hoạt động trở lại!");
  updateCurrentNodeUI();
  await loadTasks();
}

function startHealthCheck() {
  // Kiểm tra sức khỏe mỗi 5 giây
  healthCheckInterval = setInterval(async () => {
    await checkNodeHealth();
  }, 5000);
}

function handleKeyPress(event) {
  if (event.key === "Enter") {
    addTask();
  }
}

function showMessage(message, type = "success") {
  const element = document.getElementById(type + "Message");
  element.textContent = message;
  element.classList.add("show");
  setTimeout(() => {
    element.classList.remove("show");
  }, 3000);
}

async function apiRequest(endpoint, options = {}) {
  try {
    const response = await fetch(`${currentNode}${endpoint}`, {
      ...options,
      signal: AbortSignal.timeout(5000),
    });

    // Nếu node follower trả về lỗi 403 (not leader)
    if (response.status === 403) {
      let data = {};
      try {
        data = await response.json();
      } catch (_) {}

      // Nếu backend có gửi địa chỉ leader → dùng nó
      if (data.leader) {
        currentNode = data.leader.startsWith("http")
          ? data.leader
          : `http://${data.leader}`;
      } else {
        // Nếu backend không gửi leader, fallback về node chính
        console.warn("⚠️ Follower không báo leader, fallback về node 4000");
        currentNode = NODES.primary;
      }

      updateCurrentNodeUI();
      console.warn(`🔁 Chuyển sang ${currentNode} và gửi lại request...`);

      const retry = await fetch(`${currentNode}${endpoint}`, options);
      if (!retry.ok)
        throw new Error(`HTTP error ${retry.status} khi retry sang leader`);
      return await retry.json();
    }

    // Nếu không lỗi → trả kết quả bình thường
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);

    return await response.json();
  } catch (error) {
    console.error(`❌ Request thất bại tại ${currentNode}:`, error);
    showMessage("Không thể kết nối đến node!", "error");
    throw error;
  }
}

async function loadTasks() {
  try {
    const data = await apiRequest("/tasks");
    tasks = data.tasks || [];
    renderTasks();
  } catch (error) {
    console.error("Lỗi tải tasks:", error);
    document.getElementById("tasksList").innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">Không thể kết nối đến bất kỳ node nào</div></div>';
  }
}

function renderTasks() {
  const container = document.getElementById("tasksList");
  let filteredTasks = tasks;

  if (currentFilter === "active") {
    filteredTasks = tasks.filter((t) => !t.completed);
  } else if (currentFilter === "completed") {
    filteredTasks = tasks.filter((t) => t.completed);
  }

  document.getElementById("taskCount").textContent = tasks.length;

  if (filteredTasks.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📂</div>
        <div class="empty-state-text">Chưa có công việc nào. Hãy thêm công việc mới!</div>
      </div>
    `;
    return;
  }

  container.innerHTML = filteredTasks
    .map(
      (task) => `
    <div class="task-item ${task.completed ? "completed" : ""}" data-id="${
        task.id
      }">
      <input 
        type="checkbox" 
        class="task-checkbox" 
        ${task.completed ? "checked" : ""} 
        onchange="toggleTask('${task.id}')"
      />
      <div class="task-content">
        <div class="task-title">${escapeHtml(task.title)}</div>
        <div class="task-meta">ID: ${task.id} | ${new Date(
        task.created_at
      ).toLocaleString("vi-VN")}</div>
      </div>
      <button 
        class="btn btn-edit" 
        onclick="editTask('${task.id}')" 
        data-title="Sửa"
        ${task.completed ? "disabled" : ""}
      >
        Sửa
      </button>
      <button class="btn btn-danger" onclick="deleteTask('${task.id}')">
        Xóa
      </button>
    </div>
  `
    )
    .join("");
}

async function addTask() {
  const input = document.getElementById("taskInput");
  const title = input.value.trim();

  if (!title) {
    showMessage("Vui lòng nhập tên công việc!", "error");
    return;
  }

  try {
    await apiRequest("/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });

    input.value = "";
    showMessage("Đã thêm công việc thành công!");
    await loadTasks();
  } catch (error) {
    showMessage("Lỗi khi thêm công việc!", "error");
  }
}

async function addBulkTasks() {
  const input = document.getElementById("bulkTaskInput");
  const lines = input.value.split("\n").filter((line) => line.trim());

  if (lines.length === 0) {
    showMessage("Vui lòng nhập ít nhất một công việc!", "error");
    return;
  }

  try {
    const promises = lines.map((title) =>
      apiRequest("/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() }),
      })
    );

    await Promise.all(promises);
    input.value = "";
    showMessage(`Đã thêm ${lines.length} công việc thành công!`);
    await loadTasks();
  } catch (error) {
    showMessage("Lỗi khi thêm nhiều công việc!", "error");
  }
}

async function toggleTask(id) {
  const task = tasks.find((t) => t.id === id);
  if (!task) return;

  try {
    await apiRequest(`/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed: !task.completed }),
    });

    await loadTasks();
  } catch (error) {
    showMessage("Lỗi khi cập nhật công việc!", "error");
    await loadTasks();
  }
}

async function deleteTask(id) {
  if (!confirm("Bạn có chắc muốn xóa công việc này?")) return;

  try {
    await apiRequest(`/tasks/${id}`, {
      method: "DELETE",
    });

    showMessage("Đã xóa công việc!");
    await loadTasks();
  } catch (error) {
    showMessage("Lỗi khi xóa công việc!", "error");
  }
}

async function editTask(id) {
  const task = tasks.find((t) => t.id === id);
  if (!task) return;

  // Logic to prevent editing completed tasks
  if (task.completed) {
    showMessage("Không thể sửa công việc đã hoàn thành!", "error");
    return;
  }

  const newTitle = prompt("Nhập tên công việc mới:", task.title);
  if (newTitle === null || newTitle.trim() === "") {
    showMessage("Tên công việc không hợp lệ!", "error");
    return;
  }

  try {
    await apiRequest(`/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle.trim() }),
    });

    showMessage("Đã cập nhật công việc thành công!");
    await loadTasks();
  } catch (error) {
    showMessage("Lỗi khi sửa công việc!", "error");
  }
}

async function clearAllTasks() {
  if (tasks.length === 0) {
    showMessage("Không có công việc nào để xóa!", "error");
    return;
  }

  if (
    !confirm(
      `Bạn có chắc chắn muốn xóa TẤT CẢ ${tasks.length} công việc? Thao tác này không thể hoàn tác!`
    )
  )
    return;

  try {
    // Logic to delete ALL tasks
    const promises = tasks.map((task) =>
      apiRequest(`/tasks/${task.id}`, { method: "DELETE" })
    );

    await Promise.all(promises);
    showMessage(`Đã xóa tất cả ${tasks.length} công việc!`);
    await loadTasks();
  } catch (error) {
    showMessage("Lỗi khi xóa tất cả công việc!", "error");
  }
}

function filterTasks(filter, event) {
  currentFilter = filter;

  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.classList.remove("active");
  });

  if (event && event.target) {
    event.target.classList.add("active");
  }

  renderTasks();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
  }
});
