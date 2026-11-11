// Acompanha a leitura de boletins enviados: consulta a situação a cada 2 s e atualiza a página.
(function () {
  "use strict";

  document.querySelectorAll("[data-acompanhar]").forEach(function (painel) {
    var url = painel.getAttribute("data-acompanhar");
    var tentativas = 0;

    function atualizar(itens) {
      itens.forEach(function (item) {
        var rotulo = document.querySelector('[data-situacao="' + item.id + '"]');
        if (rotulo) rotulo.textContent = item.rotulo;
      });
    }

    function consultar() {
      tentativas += 1;
      fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" })
        .then(function (resposta) {
          if (!resposta.ok) throw new Error("HTTP " + resposta.status);
          return resposta.json();
        })
        .then(function (dados) {
          var itens = dados.itens || [dados];
          atualizar(itens);
          if (dados.terminal) {
            if (!dados.itens && dados.destino) {
              window.location.assign(dados.destino);
            } else {
              window.location.reload();
            }
            return;
          }
          // Depois de ~10 min, para de consultar (a fila pode estar parada); o aviso fica na tela.
          if (tentativas < 300) window.setTimeout(consultar, 2000);
        })
        .catch(function () {
          if (tentativas < 300) window.setTimeout(consultar, 5000);
        });
    }

    window.setTimeout(consultar, 1500);
  });
})();
