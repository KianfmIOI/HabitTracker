//toggle actions
document.addEventListener("click", (e) => {
  const toggleBtn = e.target.closest(".actions-toggle-btn");
  if (toggleBtn) {
    const habitItem = toggleBtn.closest(".habit-item");
    const actionsRow = habitItem.querySelector(".habit-actions-row");
    actionsRow.classList.toggle("open");

    console.log("Actions row toggled:", actionsRow.classList.contains("open"));
  }
});
// Toggle Archives Sidebar
document.getElementById("archives-btn").addEventListener("click", function () {
  const archivesSidebar = document.getElementById("archives-sidebar");
  if (archivesSidebar) {
    archivesSidebar.classList.toggle("hidden");
    updateLeftSidebar();
    if (!archivesSidebar.classList.contains("hidden")) {
      setTimeout(() => {
        archivesSidebar.scrollIntoView({
          behavior: "smooth",
          block: "start", // Aligns the top of the profile to the top of the screen
        });
      }, 50);
    }
  }
});

document.getElementById("add-habit-btn").addEventListener("click", function () {
  const addHabitTable = document.getElementById("add_habit_table");
  addHabitTable.classList.toggle("hidden");
});

// Event listeners for Edit buttons to open modal
document.querySelectorAll(".edit-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const habitId = button.getAttribute("data-id");
    const name = button.getAttribute("data-name");
    const interval = button.getAttribute("data-interval");
    const emoji = button.getAttribute("data-emoji");
    const color = button.getAttribute("data-color");

    openModal(habitId, name, interval, emoji, color);
  });
});

document.addEventListener("click", async (e) => {
  //toggle archive button

  if (e.target.classList.contains("habit-archive-btn")) {
    const habitId = e.target.dataset.habitId;

    try {
      const res = await fetch(`/habits/${habitId}/toggle_archive`, {
        method: "POST",
      });
      const data = await res.json();
      console.log(data);
      if (data.ok) {
        showFlash(data.message, "ok");
        setTimeout(() => location.reload(), 800);
      }
    } catch (err) {
      console.error(err);
      showFlash("an error occured", "err");
    }
  }
});

// Open edit modal
function openModal(habitId, name, interval, emoji, color) {
  const modal = document.getElementById("editModal");
  const form = document.getElementById("editForm");

  document.getElementById("editName").value = name;
  document.getElementById("editInterval").value = interval || 1;
  document.getElementById("editEmoji").value = emoji || "🔥";
  document.getElementById("editColor").value = color || "#ffffff";

  form.action = `/habits/${habitId}/edit`;
  modal.classList.add("active");
}

// Close edit modal
function closeModal() {
  const modal = document.getElementById("editModal");
  modal.classList.remove("active");
}

// Close modal when clicking outside the content
window.addEventListener("click", (event) => {
  const modal = document.getElementById("editModal");
  if (event.target === modal) {
    closeModal();
  }
});
// show the note form beneath the habit
function ToggleNoteRow(habitId) {
  const noteRow = document.getElementById(`note-row-${habitId}`);
  const noteForm = document.getElementById(`note-form-${habitId}`);
  const hasDes = noteRow.getAttribute("data-description") === "true";

  if (!noteRow || !noteForm) return;

  if (noteForm.style.display === "none" || noteForm.style.display === "") {
    noteForm.style.display = "flex";
  } else {
    noteForm.style.display = "none";
  }
  if (!hasDes) {
    noteRow.style.display = "table-row";
  }
}
function ToggleCheckInNoteRow(habitId) {
  const noteRow = document.getElementById(`check-in-note-row-${habitId}`);
  noteRow.classList.toggle("hidden");
}
function fadingEffect(element) {
  element.style.opacity = "1";

  setTimeout(() => {
    element.style.transition = "opacity 0.5s ease";
    element.style.opacity = "0";
    setTimeout(() => {
      element.style.display = "none";
      element.remove();
    }, 500);
  }, 3000);
}
// Auto-fade messages after 3 seconds
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".msg").forEach(fadingEffect);
  confirmationDialogs();
  updateLeftSidebar();
  HabitDetailsButton();
  // toggle-main button

  // document.querySelectorAll(".toggle-main-btn").forEach((btn) => {
  //   btn.addEventListener("click", async () => {
  //     const habitId = btn.dataset.habitId;

  //     try {
  //       const res = await fetch(`/habits/${habitId}/toggle-main`, {
  //         method: "POST",
  //         headers: {
  //           "Content-Type": "application/json",
  //         },
  //       });
  //       if (res.ok) {
  //         const data = await res.json();
  //         btn.textContent = data.is_main ? "★" : "☆";
  //         showFlash(data.message, "ok");
  //       }
  //     } catch (err) {
  //       console.error("Error toggling habit as main", err);
  //       showFlash("An error occurred", "err");
  //     }
  //   });
  // });
});
function showFlash(msg, category) {
  const msgBox = document.createElement("div");
  msgBox.className = `msg ${category} alert`;
  msgBox.setAttribute("role", "alert");
  msgBox.textContent = msg;
  document.querySelector(".flash-container").appendChild(msgBox);
  fadingEffect(msgBox);
}

function HabitDetailsButton() {
  const detailsButtons = document.querySelectorAll(".details-btn");
  const detailsSidebar = document.getElementById("details-sidebar");
  const detailsContent = document.getElementById("details-content");

  if (!detailsContent || !detailsSidebar) {
    console.warn("Detail content or sidebar not found");
    return;
  }
  // track the current habit in the details sidebar
  detailsSidebar.dataset.currentHabit = "";

  detailsButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const habitId = btn.dataset.habitId;
      if (!habitId) {
        return console.warn("button missing habit id");
      }

      const currentHabit = detailsSidebar.dataset.currentHabit;
      const isOpen = !detailsSidebar.classList.contains("hidden");

      if (isOpen && currentHabit === habitId) {
        detailsSidebar.classList.add("hidden");
        detailsSidebar.dataset.currentHabit = "";
        updateLeftSidebar();
        return;
      }

      detailsSidebar.dataset.currentHabit = habitId;
      detailsContent.innerHTML = "<P>loading details...</P>";
      detailsSidebar.classList.remove("hidden");
      updateLeftSidebar();

      try {
        const res = await fetch(`/habits/${habitId}/details`);

        if (!res.ok) {
          const text = await res.text();
          throw new Error(
            `Server error: ${res.status} - ${text || res.statusText}`,
          );
        }

        const htmlContent = await res.text();

        detailsContent.innerHTML = htmlContent;
        detailsSidebar.classList.remove("hidden");
        wireUpDetailsCloseButton(detailsSidebar);
      } catch (err) {
        console.error("Error fetching habit's details:", err);
        detailsContent.innerHTML = `<P style="color:red;">Error </P>`;
      }
    });
  });
}

function wireUpDetailsCloseButton(sidebarEl) {
  const closeBtn = sidebarEl.querySelector(".details-close-btn");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      sidebarEl.classList.add("hidden");
      sidebarEl.dataset.currentHabit = "";
      updateLeftSidebar();
    });
  }
}
document.getElementById("user-btn").addEventListener("click", function (e) {
  e.preventDefault();

  // 1. Find the user sidebar element
  const userSidebar = document.querySelector(".user-sidebar");

  if (userSidebar) {
    // 2. Toggle the visibility (remove/add the 'hidden' class)
    userSidebar.classList.toggle("hidden");
    // 3. If it was just opened (no longer hidden), scroll to it
    if (!userSidebar.classList.contains("hidden")) {
      // scroll to the element
      setTimeout(() => {
        userSidebar.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 50);
    }
  }
});

// hide the left side bar when details and archives are not selected
function updateLeftSidebar() {
  const leftSidebar = document.querySelector(".left-sidebar");
  const archives = document.querySelector(".archives-sidebar");
  const details = document.querySelector(".details-sidebar");

  // if any is missing
  if (!leftSidebar || !archives || !details) return;

  const archivesHidden = archives.classList.contains("hidden");
  const detailsHidden = details.classList.contains("hidden");
  if (archivesHidden && detailsHidden) {
    leftSidebar.classList.add("hidden");
  } else {
    leftSidebar.classList.remove("hidden");
  }
}

function confirmationDialogs() {
  const modal = document.getElementById("confirm-modal");
  const titleEl = document.getElementById("confirm-modal-title");
  const messageEl = document.getElementById("confirm-modal-message");
  const cancelBtn = document.getElementById("confirm-modal-cancel");
  const okBtn = document.getElementById("confirm-modal-ok");

  if (!modal || !titleEl || !messageEl || !cancelBtn || !okBtn) return;

  let pendingAction = null;

  function openConfirmModal({ title, message, onConfirm }) {
    titleEl.textContent = title || "Are you sure?";
    messageEl.textContent = message || "";
    pendingAction = typeof onConfirm === "function" ? onConfirm : null;
    modal.classList.remove("hidden");
  }

  function closeConfirmModal() {
    modal.classList.add("hidden");
    pendingAction = null;
  }

  cancelBtn.addEventListener("click", () => {
    closeConfirmModal();
  });

  okBtn.addEventListener("click", () => {
    if (pendingAction) {
      pendingAction();
    }
    closeConfirmModal();
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeConfirmModal();
  });

  document.querySelectorAll("form.confirmation-required").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const title = form.dataset.confirmTitle;
      const message = form.dataset.confirmMessage;
      openConfirmModal({
        title,
        message,
        onConfirm: () => {
          form.submit();
        },
      });
    });
  });
}
