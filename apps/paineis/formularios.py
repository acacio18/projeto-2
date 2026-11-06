"""Apoio de acessibilidade para todos os formulários da interface."""


class FormularioAcessivel:
    """Liga cada campo ao texto de ajuda e à mensagem de erro (aria-describedby e aria-invalid).

    Os ids seguem o padrão usado em templates/parciais/campo.html: <id>_ajuda e <id>_erro.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if campo.help_text:
                id_campo = campo.widget.attrs.get("id") or self.auto_id % self.add_prefix(nome)
                campo.widget.attrs["aria-describedby"] = f"{id_campo}_ajuda"

    def full_clean(self):
        super().full_clean()
        for nome in self.errors:
            if nome not in self.fields:
                continue
            campo = self.fields[nome]
            id_campo = campo.widget.attrs.get("id") or self.auto_id % self.add_prefix(nome)
            descricoes = [d for d in campo.widget.attrs.get("aria-describedby", "").split() if d]
            campo.widget.attrs["aria-describedby"] = " ".join([*descricoes, f"{id_campo}_erro"])
            campo.widget.attrs["aria-invalid"] = "true"
