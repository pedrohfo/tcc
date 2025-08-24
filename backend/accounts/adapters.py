from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # Se o form (serializer) não tem _has_phone_field, define como False
        if not hasattr(form, '_has_phone_field'):
            form._has_phone_field = False
        return super().save_user(request, user, form, commit)
