document.addEventListener("DOMContentLoaded", () => {
  initStarRating();
  initCharCounter();
  initReviewCards();
  initVoteToggle();
  initLikes();
  initDeleteReviewConfirm();
  initReviewFormValidation();
});

function initStarRating() {
  const inputs = document.querySelectorAll(".star-label input");
  const ratingText = document.querySelector(".rating-text");
  if (!inputs.length) return;

  const setText = (v) => {
    if (ratingText) ratingText.textContent = v ? `${v}/5` : "Select rating";
  };

  const updateStars = (value) => {
    document.querySelectorAll(".star-label").forEach((label, idx) => {
      label.classList.toggle("active", idx < value);
    });
    setText(value);
  };

  const markChecked = (input) => {
    inputs.forEach((i) => (i.dataset.wasChecked = "false"));
    input.dataset.wasChecked = "true";
    updateStars(parseInt(input.value));
  };

  inputs.forEach((input) => {
    input.addEventListener("click", () => {
      if (input.dataset.wasChecked === "true") {
        input.checked = false;
        input.dataset.wasChecked = "false";
        updateStars(0);
        return;
      }
      markChecked(input);
    });

    input.addEventListener("change", () => markChecked(input));
  });

  const checked = document.querySelector(".star-label input:checked");
  if (checked) {
    checked.dataset.wasChecked = "true";
    updateStars(parseInt(checked.value));
  } else {
    updateStars(0);
  }
}

function initCharCounter() {
  const textarea = document.querySelector('textarea[name="review_text"]');
  const counter = document.getElementById("char-count");
  if (!textarea || !counter) return;

  const sync = () => (counter.textContent = textarea.value.length);
  sync();
  textarea.addEventListener("input", sync);
}

function initReviewCards() {
  document.querySelectorAll(".review-card").forEach((card) => {
    const textEl = card.querySelector("[data-review-text]");
    if (!textEl) return;

    const moreBtn = card.querySelector("[data-moreless-btn]");
    const spoilerBtn = card.querySelector("[data-spoiler-btn]");

    if (moreBtn) {
      const setMoreBtnText = () => {
        moreBtn.textContent = textEl.classList.contains("collapsed") ? "More" : "Less";
      };

      setMoreBtnText();
      moreBtn.addEventListener("click", () => {
        textEl.classList.toggle("collapsed");
        setMoreBtnText();
      });
    }

    if (spoilerBtn) {
      spoilerBtn.addEventListener("click", () => {
        const hiddenNow = textEl.classList.toggle("spoiler");
        spoilerBtn.textContent = hiddenNow ? "Show spoiler" : "Hide spoiler";
      });
    }
  });
}

function initVoteToggle() {
  const voteForm = document.querySelector('form[action*="/vote/"]');
  if (!voteForm) return;

  const currentVote = document.querySelector(".detail-page")?.dataset.currentVote || "";

  voteForm.querySelectorAll(".meter-name[data-vote]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const clickedVote = btn.dataset.vote;
      if (!currentVote || clickedVote !== currentVote) return;

      e.preventDefault();
      voteForm.insertAdjacentHTML(
        "beforeend",
        '<input type="hidden" name="vote" value="remove">'
      );
      voteForm.submit();
    });
  });
}

function initLikes() {
  document.querySelectorAll("[data-like-form]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const btn = form.querySelector("[data-like-btn]");
      const countEl = form.querySelector("[data-like-count]");
      const iconEl = form.querySelector("[data-like-icon]");
      if (!btn || !countEl || !iconEl) return;

      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        const data = await res.json();
        if (!data.ok) return;

        btn.classList.toggle("liked", data.liked);
        countEl.textContent = data.like_count;
        iconEl.src = data.liked ? iconEl.dataset.likedSrc : iconEl.dataset.likeSrc;
      } catch (err) {
        console.log(err);
      }
    });
  });
}

function getCSRFToken() {
  return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";
}

function initDeleteReviewConfirm() {
  const modal = document.getElementById("app-confirm-modal");
  if (!modal) return;

  const titleEl = document.getElementById("app-modal-title");
  const textEl = document.getElementById("app-modal-text");

  const confirmBtn = modal.querySelector("[data-modal-confirm]");
  const cancelBtn = modal.querySelector("[data-modal-cancel]");
  const closeEls = modal.querySelectorAll("[data-modal-close]");

  let pendingForm = null;

  const openModal = (form) => {
    pendingForm = form;
    titleEl.textContent = "Delete Review?";
    textEl.textContent = "This review will be permanently deleted.";
    modal.classList.remove("hidden");
  };

  const closeModal = () => {
    modal.classList.add("hidden");
    pendingForm = null;
  };

  document.querySelectorAll("[data-delete-review-form]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      openModal(form);
    });
  });

  confirmBtn.addEventListener("click", () => {
    if (!pendingForm) return;
    pendingForm.submit();
    closeModal();
  });

  cancelBtn.addEventListener("click", closeModal);
  closeEls.forEach((el) => el.addEventListener("click", closeModal));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
}

function initReviewFormValidation() {
  const form = document.querySelector("section.review-form form");
  if (!form) return;

  const textarea = form.querySelector('textarea[name="review_text"]');
  const textErrorEl = document.getElementById("review-text-error");

  const ratingInputs = form.querySelectorAll('input[name="rating"]');
  const ratingErrorEl = document.getElementById("review-rating-error");

  const setError = (el, msg = "") => {
    if (!el) return;
    el.textContent = msg;
    el.hidden = !msg;
  };

  form.addEventListener("submit", (e) => {
    const text = textarea?.value.trim() || "";
    const ratingChecked = form.querySelector('input[name="rating"]:checked');

    let ok = true;

    if (!ratingChecked) {
      setError(ratingErrorEl, "Rating is required.");
      ok = false;
    } else setError(ratingErrorEl);

    if (!text) {
      setError(textErrorEl, "Review text is required.");
      ok = false;
    } else setError(textErrorEl);

    if (!ok) e.preventDefault();
  });

  textarea?.addEventListener("input", () => {
    if (textarea.value.trim()) setError(textErrorEl);
  });

  ratingInputs.forEach((inp) => {
    inp.addEventListener("change", () => setError(ratingErrorEl));
  });
}
