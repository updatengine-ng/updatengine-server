import urllib.request, urllib.error, urllib.parse
import json
from django import forms


def get_latest_release_version(url):
    try:
        headers = {'User-Agent': "Magic Browser", 'Accept': "application/vnd.github.v3+json"}
        req = urllib.request.Request(url, headers= headers)
        html = urllib.request.urlopen(req).read().decode("utf-8")
        releases = json.loads(html)
        retval = releases[0]['tag_name']
    except Exception as e:
        retval = 'undefined'
    return retval


class FieldsetsInlineMixin(object):
    change_form_template = 'fieldsets_with_inlines/change_form.html'

    def make_placeholder(self, index, fieldset):
        if isinstance(fieldset, forms.MediaDefiningClass):
            fieldset.fieldset_index = index

            # Placeholder must conform to the rules in
            # the ModelAdmin.fieldsets.
            # https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.fieldsets
            return (None, {'fields': ()})
        return fieldset

    def get_fieldsets(self, request, obj=None):
        if self.fieldsets_with_inlines:
            return [
                self.make_placeholder(index, fieldset)
                for index, fieldset in enumerate(self.fieldsets_with_inlines)]
        return super().get_fieldsets(request, obj)

    def get_inline_instances(self, request, obj=None):
        """
        Get inline instances from fieldsets_with_inlines if defined.
        This way inlines property is not needed anymore.
        """
        if self.fieldsets_with_inlines:
            inlines = [
                inline for inline in self.fieldsets_with_inlines
                if isinstance(inline, forms.MediaDefiningClass)]
            print(inlines)
            inline_instances = []
            for inline_class in inlines:
                inline = inline_class(self.model, self.admin_site)
                if request:
                    if not (inline.has_add_permission(request, obj) or
                            inline.has_change_permission(request, obj) or
                            inline.has_view_permission(request, obj) or
                            inline.has_delete_permission(request, obj)):
                        continue
                    if not inline.has_add_permission(request, obj):
                        inline.max_num = 0
                inline_instances.append(inline)

            return inline_instances

        return super().get_inline_instances(request, obj)
