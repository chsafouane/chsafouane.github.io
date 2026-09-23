// Step-through figures made with tools/figkit ({{< stepper >}} shortcode).
// Without JavaScript every step is shown in order with its caption; this
// script turns the figure into one frame at a time with previous/next
// buttons, arrow keys and an optional autoplay.
(() => {
  const STEP_MS = 2400;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const setup = (figure) => {
    const frames = [...figure.querySelectorAll(".figkit-frame")];
    const controls = figure.querySelector(".figkit-controls");
    const counter = figure.querySelector(".figkit-counter");
    const prev = figure.querySelector(".figkit-prev");
    const next = figure.querySelector(".figkit-next");
    const play = figure.querySelector(".figkit-play");
    let index = 0;
    let timer = null;

    const show = (i) => {
      index = (i + frames.length) % frames.length;
      frames.forEach((frame, n) => {
        const active = n === index;
        frame.classList.toggle("is-active", active);
        frame.setAttribute("aria-hidden", active ? "false" : "true");
      });
      counter.textContent = `${index + 1} / ${frames.length}`;
      prev.disabled = timer === null && index === 0;
      next.disabled = timer === null && index === frames.length - 1;
    };

    const stop = () => {
      if (timer === null) return;
      clearInterval(timer);
      timer = null;
      play.setAttribute("aria-label", "Play all steps");
      play.querySelector("i").className = "bi bi-play-fill";
      show(index);
    };

    const start = () => {
      timer = setInterval(() => show(index + 1), STEP_MS);
      play.setAttribute("aria-label", "Pause");
      play.querySelector("i").className = "bi bi-pause-fill";
      show(index === frames.length - 1 ? 0 : index);
    };

    prev.addEventListener("click", () => { stop(); show(index - 1); });
    next.addEventListener("click", () => { stop(); show(index + 1); });
    play.addEventListener("click", () => (timer === null ? start() : stop()));
    figure.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") { stop(); show(index - 1); event.preventDefault(); }
      if (event.key === "ArrowRight") { stop(); show(index + 1); event.preventDefault(); }
    });
    if (reduceMotion.matches) play.hidden = true;

    figure.classList.add("is-enhanced");
    controls.hidden = false;
    show(0);
  };

  const init = () => document.querySelectorAll(".figkit-stepper").forEach(setup);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
