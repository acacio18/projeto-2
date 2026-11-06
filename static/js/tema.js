// Aplica o tema salvo antes de a página aparecer (evita piscar). Sem tema salvo, vale o do sistema.
(function () {
  try {
    var tema = window.localStorage.getItem("suap-tema");
    if (tema === "claro" || tema === "escuro") {
      document.documentElement.setAttribute("data-tema", tema);
    }
  } catch (erro) {
    /* armazenamento indisponível: fica o tema do sistema */
  }
})();
