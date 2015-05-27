from edc_base.modeladmin.admin import BaseModelAdmin


class BaseProfileItemAdmin(BaseModelAdmin):

    list_display = (
        'profile', 'aliquot_type', 'created', 'modified', 'user_created', 'user_modified')

    search_fields = (
        'profile__profile_name', 'aliquot_type__name', 'aliquot_type__alpha_code', 'aliquot_type__numeric_code')

    list_filter = (
        'aliquot_type__name',
        'aliquot_type__alpha_code',
        'aliquot_type__numeric_code',
        'created',
        'modified',
        'user_created',
        'user_modified')
