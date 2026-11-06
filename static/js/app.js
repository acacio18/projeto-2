// Comportamentos da interface do SUAP V2. Tudo funciona sem JavaScript; aqui só há melhorias.
(function () {
  "use strict";

  var raiz = document.documentElement;

  function temaAtual() {
    var escolhido = raiz.getAttribute("data-tema");
    if (escolhido) return escolhido;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
  }

  // Troca de tema claro/escuro, guardada no navegador.
  function prepararTema() {
    var botao = document.querySelector("[data-alternar-tema]");
    if (!botao) return;
    function atualizar() {
      var escuro = temaAtual() === "escuro";
      botao.setAttribute("aria-pressed", escuro ? "true" : "false");
      botao.setAttribute("aria-label", escuro ? "Usar tema claro" : "Usar tema escuro");
      botao.setAttribute("title", escuro ? "Usar tema claro" : "Usar tema escuro");
    }
    botao.addEventListener("click", function () {
      var novo = temaAtual() === "escuro" ? "claro" : "escuro";
      raiz.setAttribute("data-tema", novo);
      try {
        window.localStorage.setItem("suap-tema", novo);
      } catch (erro) {
        /* sem armazenamento: o tema vale só nesta página */
      }
      atualizar();
    });
    atualizar();
  }

  // Menu de navegação no celular.
  function prepararMenu() {
    var botao = document.querySelector("[data-alternar-menu]");
    if (!botao) return;
    var menu = document.getElementById(botao.getAttribute("aria-controls"));
    botao.addEventListener("click", function () {
      var aberto = botao.getAttribute("aria-expanded") === "true";
      botao.setAttribute("aria-expanded", aberto ? "false" : "true");
      menu.setAttribute("data-aberta", aberto ? "false" : "true");
    });
  }

  // Mostrar/ocultar senha.
  function prepararSenhas() {
    document.querySelectorAll("[data-alternar-senha]").forEach(function (botao) {
      var campo = document.getElementById(botao.getAttribute("data-alternar-senha"));
      if (!campo) return;
      botao.hidden = false;
      botao.addEventListener("click", function () {
        var visivel = campo.type === "text";
        campo.type = visivel ? "password" : "text";
        botao.setAttribute("aria-pressed", visivel ? "false" : "true");
        botao.setAttribute("aria-label", visivel ? "Mostrar senha" : "Ocultar senha");
      });
    });
  }

  // Evita envio duplicado: desabilita o botão e mostra "carregando" até a resposta.
  function prepararEnvios() {
    document.querySelectorAll("form[data-envio-unico]").forEach(function (formulario) {
      formulario.addEventListener("submit", function (evento) {
        if (formulario.getAttribute("data-enviando") === "true") {
          evento.preventDefault();
          return;
        }
        formulario.setAttribute("data-enviando", "true");
        var botao = evento.submitter || formulario.querySelector("button[type=submit]");
        if (!botao) return;
        botao.setAttribute("aria-busy", "true");
        var texto = botao.getAttribute("data-texto-enviando");
        var rotulo = botao.querySelector("[data-rotulo]");
        if (texto && rotulo) rotulo.textContent = texto;
      });
    });
  }

  prepararTema();
  prepararMenu();
  prepararSenhas();
  prepararEnvios();
})();
