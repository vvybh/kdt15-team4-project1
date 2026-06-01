function formatRemaining(milliseconds) {
  if (milliseconds <= 0) {
    return "종료";
  }

  const totalMinutes = Math.floor(milliseconds / 60000);
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;

  if (days > 0) {
    return `${days}일 ${hours}시간 남음`;
  }
  if (hours > 0) {
    return `${hours}시간 ${minutes}분 남음`;
  }
  return `${minutes}분 남음`;
}

function updateCountdowns() {
  document.querySelectorAll("[data-countdown]").forEach((node) => {
    const end = new Date(node.dataset.end);
    if (Number.isNaN(end.getTime())) {
      return;
    }
    node.textContent = formatRemaining(end.getTime() - Date.now());
  });
}

updateCountdowns();
window.setInterval(updateCountdowns, 60000);

function setupRankSliders() {
  document.querySelectorAll("[data-rank-slider]").forEach((slider) => {
    const slides = Array.from(slider.querySelectorAll("[data-slide]"));
    const dots = Array.from(slider.querySelectorAll("[data-slide-dot]"));
    let activeIndex = 0;

    if (slides.length <= 1) {
      return;
    }

    function showSlide(index) {
      activeIndex = (index + slides.length) % slides.length;
      slides.forEach((slide, slideIndex) => {
        slide.classList.toggle("active", slideIndex === activeIndex);
      });
      dots.forEach((dot, dotIndex) => {
        dot.classList.toggle("active", dotIndex === activeIndex);
      });
    }

    dots.forEach((dot, dotIndex) => {
      dot.addEventListener("click", () => showSlide(dotIndex));
    });

    window.setInterval(() => showSlide(activeIndex + 1), 4500);
  });
}

setupRankSliders();
