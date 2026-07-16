/* ============================================================
   RIBEIRO & TIGRE · NEXUM — Supreme Drafter
   Comportamentos compartilhados  ·  app.js
   V18 · Carregado por todas as páginas (idempotente, com guardas)
   ============================================================ */
(function () {
    "use strict";

    /* ------------------------------------------------------------
       Google Analytics 4 — pronto-para-ativar.
       Preencha GA_MEASUREMENT_ID ("G-XXXXXXXXXX") para ligar a
       telemetria em TODAS as páginas (este arquivo é compartilhado).
       Vazio => nenhum byte de analytics é carregado.
       ------------------------------------------------------------ */
    var GA_MEASUREMENT_ID = "";
    if (/^G-[A-Z0-9]{4,}$/.test(GA_MEASUREMENT_ID)) {
        var ga = document.createElement("script");
        ga.async = true;
        ga.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_MEASUREMENT_ID;
        document.head.appendChild(ga);
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag("js", new Date());
        window.gtag("config", GA_MEASUREMENT_ID, { anonymize_ip: true });
    }

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
