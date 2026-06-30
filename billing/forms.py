from django import forms

from billing.models import Assinatura


class AssinaturaAdminForm(forms.ModelForm):
    class Meta:
        model = Assinatura
        fields = ["plano", "status", "fim_trial_em", "gateway_preferido"]
        widgets = {
            "fim_trial_em": forms.DateInput(attrs={"type": "date"}),
        }
