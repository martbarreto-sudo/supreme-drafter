/* ============================================================
   RIBEIRO & TIGRE · NEXUM — Supreme Drafter
   Comportamentos compartilhados  ·  app.js
   V18 · Carregado por todas as páginas (idempotente, com guardas)
   ============================================================ */
(function () {
    "use strict";

    /* Ano corrente no rodapé (onde houver #year) */
    var year = document.getElementById("year");
    if (year) { year.textContent = new Date().getFullYear(); }

    /* Relógio operacional em horário de Brasília (onde houver #clock) */
    var clock = document.getElementById("clock");
    if (clock) {
        var opts = { timeZone: "America/Sao_Paulo", hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" };
        var fmt = new Intl.DateTimeFormat("pt-BR", opts);
        var tick = function () { clock.textContent = fmt.format(new Date()); };
        tick();
        setInterval(tick, 1000);
    }
})();
