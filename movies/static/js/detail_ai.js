document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("section.review-form form");
  const textarea = form?.querySelector('textarea[name="review_text"]');
  if (!form || !textarea) return;

  const modeSelect = document.getElementById("ai-mode");
  const generateBtn = document.getElementById("ai-generate-btn");
  const prosConsBtn = document.getElementById("ai-proscons-btn");
  const undoBtn = document.getElementById("ai-undo-btn");
  const statusEl = document.getElementById("ai-status");

  const modal = document.getElementById("ai-modal");
  const modalTitle = document.getElementById("ai-modal-title");
  const modalBody = document.getElementById("ai-modal-body");

  const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";

  let lastTextBeforeAI = "";

  function showStatus(msg, isError = false) {
    if (!statusEl) return;
    statusEl.hidden = false;
    statusEl.textContent = msg;
    statusEl.classList.toggle("error", isError);
  }

  function hideStatus() {
    if (!statusEl) return;
    statusEl.hidden = true;
    statusEl.textContent = "";
    statusEl.classList.remove("error");
  }

function openModal(title, html, isError = false) {
  if (!modal || !modalTitle || !modalBody) return;

  const card = modal.querySelector(".ai-modal-card");
  if (card) {
    card.classList.toggle("error", isError);
  }

  modalTitle.textContent = title;
  modalBody.innerHTML = html;
  modal.hidden = false;
}


  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
  }

  document.querySelectorAll("[data-ai-close]").forEach((el) => {
    el.addEventListener("click", () => closeModal());
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  async function post(url, payload) {
    const formData = new FormData();
    Object.keys(payload).forEach((k) => formData.append(k, payload[k]));

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrf,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    });

    const data = await res.json();
    return { res, data };
  }

  function renderProsConsHTML(pros, cons) {
    const safePros = Array.isArray(pros) ? pros : [];
    const safeCons = Array.isArray(cons) ? cons : [];

    const prosHtml =
      safePros.length > 0
        ? `<ul class="ai-pc-list">${safePros.map((p) => `<li>${p}</li>`).join("")}</ul>`
        : `<div>No pros found</div>`;

    const consHtml =
      safeCons.length > 0
        ? `<ul class="ai-pc-list">${safeCons.map((c) => `<li>${c}</li>`).join("")}</ul>`
        : `<div>No cons found</div>`;

    return `
      <div class="ai-pc-block">
        <div>
          <div class="ai-pc-title">Pros</div>
          ${prosHtml}
        </div>

        <div>
          <div class="ai-pc-title">Cons</div>
          ${consHtml}
        </div>
      </div>
    `;
  }

  if (generateBtn) {
    generateBtn.addEventListener("click", async () => {
      const url = generateBtn.dataset.url;
      const text = textarea.value.trim();
      const mode = modeSelect ? modeSelect.value : "rewrite";

      lastTextBeforeAI = textarea.value;
      if (undoBtn) undoBtn.disabled = false;

      showStatus("Generating...");

      try {
        const { data } = await post(url, { text: text, mode: mode });

        if (!data.ok) {
          showStatus(data.error || "AI failed", true);
          return;
        }

        textarea.value = data.result;
        showStatus("Done");
      } catch (err) {
        console.log(err);
        showStatus("Something went wrong", true);
      }
    });
  }

  if (undoBtn) {
    undoBtn.addEventListener("click", () => {
      textarea.value = lastTextBeforeAI;
      undoBtn.disabled = true;
      hideStatus();
    });
  }

  if (prosConsBtn) {
    prosConsBtn.addEventListener("click", async () => {
      const url = prosConsBtn.dataset.url;
      const text = textarea.value.trim();

      if (!text) {
        openModal("Pros & Cons", "Write a review first", true);

        return;
      }

      openModal("Pros & Cons (Your Review)", "Extracting...");

      try {
        const { data } = await post(url, { text: text });

        if (!data.ok) {
          openModal("Pros & Cons", data.error || "Pros/Cons failed", true);

          return;
        }

        openModal("Pros & Cons (Your Review)", renderProsConsHTML(data.pros, data.cons));
      } catch (err) {
        console.log(err);
        openModal("Pros & Cons", "Something went wrong");
      }
    });
  }

  document.querySelectorAll("[data-proscons-btn]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const url = btn.dataset.url;
      if (!url) return;

      const card = btn.closest(".review-card");

      openModal("Pros & Cons ", "Extracting...");

      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrf,
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        const data = await res.json();

        if (!data.ok) {
          openModal("Pros & Cons", data.error || "Failed");
          return;
        }

        openModal(
          "Pros & Cons",
          renderProsConsHTML(data.pros, data.cons)
        );
      } catch (err) {
        console.log(err);
        openModal("Pros & Cons", "Something went wrong");
      }
    });
  });
});
