from django import forms

from crm.models import Cliente, HistoricoContato, Lead, Oportunidade, ProximaAcao
from empresas.models import EmpresaMembership


class EmpresaScopedFormMixin:
    def __init__(self, *args, empresa, usuario=None, **kwargs):
        self.empresa = empresa
        self.usuario = usuario
        super().__init__(*args, **kwargs)
        self.instance.empresa = empresa

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.empresa = self.empresa
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class ClienteForm(EmpresaScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome", "email", "telefone", "documento", "observacoes", "ativo"]


class LeadForm(EmpresaScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["nome", "email", "telefone", "origem", "status"]


class OportunidadeForm(EmpresaScopedFormMixin, forms.ModelForm):
    class Meta:
        model = Oportunidade
        fields = ["cliente", "vendedor", "titulo", "valor_estimado", "status"]

    def __init__(self, *args, empresa, usuario=None, **kwargs):
        super().__init__(*args, empresa=empresa, usuario=usuario, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.da_empresa(empresa).filter(ativo=True)
        self.fields["vendedor"].queryset = self._vendedores_da_empresa()

    def _vendedores_da_empresa(self):
        user_model = EmpresaMembership._meta.get_field("usuario").remote_field.model
        return user_model.objects.filter(
            empresa_memberships__empresa=self.empresa,
            empresa_memberships__ativo=True,
        ).distinct()


class HistoricoContatoForm(EmpresaScopedFormMixin, forms.ModelForm):
    class Meta:
        model = HistoricoContato
        fields = ["cliente", "lead", "vendedor", "tipo", "resumo", "realizado_em"]
        widgets = {
            "realizado_em": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, empresa, usuario=None, **kwargs):
        super().__init__(*args, empresa=empresa, usuario=usuario, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.da_empresa(empresa)
        self.fields["lead"].queryset = Lead.objects.da_empresa(empresa).exclude(
            status=Lead.Status.CONVERTIDO
        )
        self.fields["vendedor"].queryset = self._usuarios_da_empresa()

    def _usuarios_da_empresa(self):
        user_model = EmpresaMembership._meta.get_field("usuario").remote_field.model
        return user_model.objects.filter(
            empresa_memberships__empresa=self.empresa,
            empresa_memberships__ativo=True,
        ).distinct()


class ProximaAcaoForm(EmpresaScopedFormMixin, forms.ModelForm):
    class Meta:
        model = ProximaAcao
        fields = ["oportunidade", "vendedor", "descricao", "data_prevista", "status"]
        widgets = {
            "data_prevista": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, empresa, usuario=None, **kwargs):
        super().__init__(*args, empresa=empresa, usuario=usuario, **kwargs)
        self.fields["oportunidade"].queryset = Oportunidade.objects.da_empresa(empresa)
        self.fields["vendedor"].queryset = self._usuarios_da_empresa()

    def _usuarios_da_empresa(self):
        user_model = EmpresaMembership._meta.get_field("usuario").remote_field.model
        return user_model.objects.filter(
            empresa_memberships__empresa=self.empresa,
            empresa_memberships__ativo=True,
        ).distinct()
