###############################################################################
# UpdatEngine - Software Packages Deployment and Administration tool          #
#                                                                             #
# Copyright (C) Yves Guimard - yves.guimard@gmail.com                         #
#                                                                             #
# This program is free software; you can redistribute it and/or               #
# modify it under the terms of the GNU General Public License                 #
# as published by the Free Software Foundation; either version 2              #
# of the License, or (at your option) any later version.                      #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program; if not, write to the Free Software Foundation,     #
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.         #
###############################################################################

from deploy.models import package, packagehistory, packageprofile, packagecondition, timeprofile, packagewakeonlan, impex
from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from deploy.filters import entityFilter, machineFilter, statusFilter,\
        packageEntityFilter, packageHistoryFilter, conditionEntityFilter, conditionFilter,\
        myPackagesFilter, myConditionsFilter
from inventory.models import entity, machine
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from django.contrib import messages
from django.utils.safestring import mark_safe


class ueAdmin(admin.ModelAdmin):
    list_max_show_all = 600
    list_per_page = 200
    actions_selection_counter = True
    list_select_related = True

    def get_export_as_csv_filename(self, request, queryset):
        return 'deploy'


class packageForm(ModelForm):
    class Meta:
        model = package
        fields = '__all__'

    # Custom form to be able to use request in clean method
    # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
    # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
    def __init__(self, *args, **kwargs):
        self.my_user = kwargs.pop('my_user')
        super(packageForm, self).__init__(*args, **kwargs)
        self.fields['editor'].choices =([(self.my_user.id,self.my_user.username)])
        self.fields['editor'].widget.can_add_related = False
        if not self.my_user.is_superuser and 'entity' in self.fields and 'conditions' in self.fields:
            #restrict entity choice
            self.fields['entity'].queryset = entity.objects.filter(pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
            self.fields['entity'].required = True
            # Restrict condition choice
            self.fields['conditions'].queryset = packagecondition.objects.filter(entity__pk__in = self.my_user.subuser.id_entities_allowed()).\
                    order_by('name').distinct()
        if 'entity' in self.fields:
            self.fields['entity'].widget.can_add_related = False

    def clean_editor(self):
        return self.my_user


class packageAdmin(ueAdmin):
    list_display = ('name','description','get_command','filename','get_conditions','ignoreperiod','public','editor','exclusive_editor')
    list_display_link = ('name')
    search_fields = ('name','description','command','filename','public')
    list_filter = ('ignoreperiod',packageEntityFilter,conditionFilter, myPackagesFilter)
    filter_horizontal = ('conditions','entity')
    form = packageForm
    fieldsets = (
                (_('package|general information'), {'fields': ('name', 'description')}),
                (_('package|package edition'), {'fields': ('conditions', 'command', 'filename','public','ignoreperiod')}),
                (_('package|permissions'), {
                    'classes': ('grp-collapse grp-closed',),
                    'fields': ('entity','editor', 'exclusive_editor')}),
                )
    def get_command(self, obj):
        return mark_safe(obj.command.replace('\r', '').replace('\n', '<br>'))
    get_command.short_description = _('package|command')
    get_command.admin_order_field = 'command'
    
    def changelist_view(self, request, extra_context=None):
        # Show a warning if user is not superuser
        if not request.user.is_superuser:
            messages.info(request,_('Warning: you will not be able to update a package that you didn\'t create if exclusive editor is set to yes for this package'))
        return super(packageAdmin, self).changelist_view(request, extra_context)

    # Prevent deletion of objects when user hasn't enough permission
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        return True

    # Prevent to change objects when user hasn't enough permission
    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        else:
            return request.user.is_superuser or request.user.has_perm('deploy.change_package')

    def get_form(self, request, obj=None, **kwargs):
        form = super(packageAdmin, self).get_form(request, obj, **kwargs)
        # Custom form to be able to use request in clean method
        # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
        # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
        class metaform(form):
            def __new__(cls, *args, **kwargs):
                kwargs['my_user'] = request.user
                return form(*args, **kwargs)
        return metaform

    def get_actions(self, request):
        actions = super(packageAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
            del actions['mass_update']
#            del actions['export_as_csv']
        return actions

    def get_queryset(self, request):
        # Re-create queryset with entity list returned by list_entities_allowed
        if request.user.is_superuser:
            return package.objects.all()
        else:
            return package.objects.filter(entity__pk__in = request.user.subuser.id_entities_allowed()).distinct()


class packagehistoryAdmin(ueAdmin):
    list_display = ('date','machine','status','name','description','command','filename','package')
    search_fields = ('status','name','description','command')
    list_filter = (entityFilter, machineFilter,packageHistoryFilter,statusFilter,
            ('date', DateFieldListFilter))
    ordering =('-date',)
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return True

    def __init__(self, *args, **kwargs):
        super(packagehistoryAdmin, self).__init__(*args, **kwargs)
        #self.list_display_links = (None, )
        self.list_display_links = ()

    def get_queryset(self, request):
        # Re-create queryset with entity list returned by list_entities_allowed
        if request.user.is_superuser:
            return packagehistory.objects.all()
        else:
            return packagehistory.objects.filter(machine__entity__pk__in = request.user.subuser.id_entities_allowed()).distinct()

    def get_actions(self, request):
        actions = super(packagehistoryAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['mass_update']
        return actions


class packageprofileForm(ModelForm):
    class Meta:
        model = packageprofile
        fields = '__all__'

    # Custom form to be able to use request in clean method
    # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
    # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
    def __init__(self, *args, **kwargs):
        self.my_user = kwargs.pop('my_user')
        super(packageprofileForm, self).__init__(*args, **kwargs)
        self.fields['editor'].choices =([(self.my_user.id,self.my_user.username)])
        self.fields['editor'].widget.can_add_related = False
        if not self.my_user.is_superuser and 'entity' in self.fields:
            #restrict entity choice
            self.fields['entity'].queryset = entity.objects.filter(pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
            self.fields['entity'].required = True
            # Restrict packages choice
            self.fields['packages'].queryset = package.objects.filter(entity__pk__in = self.my_user.subuser.id_entities_allowed()).\
                    order_by('name').distinct()
            # Restrict parent choice
            self.fields['parent'].queryset = packageprofile.objects.filter(entity__pk__in = self.my_user.subuser.id_entities_allowed()).\
                    order_by('name').distinct()
        if 'entity' in self.fields:
            self.fields['entity'].widget.can_add_related = False

    def clean_editor(self):
        return self.my_user


class packageprofileAdmin(ueAdmin):
    list_display = ('name','description', 'parent','get_packages','editor','exclusive_editor')
    filter_horizontal = ('packages','entity')
    form = packageprofileForm
    fieldsets = (
            (_('packageprofile|general information'), {'fields': ('name','description', 'parent','packages')}),
                (_('package|permissions'), {
                    'classes': ('grp-collapse grp-closed',),
                    'fields': ('entity','editor', 'exclusive_editor')}),
                )

    def changelist_view(self, request, extra_context=None):
        # Show a warning if user is not superuser
        if not request.user.is_superuser:
            messages.info(request,_('Warning: you will not be able to update a profile that you didn\'t create if exclusive editor is set to yes for this package'))
        return super(packageprofileAdmin, self).changelist_view(request, extra_context)

    # Prevent deletion of objects when user hasn't enough permission
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        return True

    # Prevent to change objects when user hasn't enough permission
    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        else:
            return request.user.is_superuser or request.user.has_perm('deploy.change_packageprofile')

    def get_form(self, request, obj=None, **kwargs):
        form = super(packageprofileAdmin, self).get_form(request, obj, **kwargs)
        # Custom form to be able to use request in clean method
        # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
        # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
        class metaform(form):
            def __new__(cls, *args, **kwargs):
                kwargs['my_user'] = request.user
                return form(*args, **kwargs)
        return metaform

    def get_actions(self, request):
        actions = super(packageprofileAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
            del actions['mass_update']
        #    del actions['export_as_csv']
        return actions

    def get_queryset(self, request):
        # Re-create queryset with entity list returned by list_entities_allowed
        if request.user.is_superuser:
            return packageprofile.objects.all()
        else:
            return packageprofile.objects.filter(entity__pk__in = request.user.subuser.id_entities_allowed()).distinct()


class timeprofileForm(ModelForm):
    class Meta:
        model = timeprofile
        fields = '__all__'

    # Custom form to be able to use request in clean method
    # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
    # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
    def __init__(self, *args, **kwargs):
        self.my_user = kwargs.pop('my_user')
        super(timeprofileForm, self).__init__(*args, **kwargs)
        self.fields['editor'].choices =([(self.my_user.id,self.my_user.username)])
        self.fields['editor'].widget.can_add_related = False
        if not self.my_user.is_superuser and 'entity' in self.fields:
            #restrict entity choice
            self.fields['entity'].queryset = entity.objects.filter(pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
            self.fields['entity'].required = True
        if 'entity' in self.fields:
            self.fields['entity'].widget.can_add_related = False

    def clean_editor(self):
        return self.my_user


class timeprofileAdmin(ueAdmin):
    list_display = ('name','description','start_time','end_time','editor','exclusive_editor')
    search_fields = ('name','description')
    filter_horizontal = ('entity',)
    form = timeprofileForm
    fieldsets = (
            (_('timeprofile|general information'), {'fields': ('name','description', 'start_time','end_time')}),
                (_('package|permissions'), {
                    'classes': ('grp-collapse grp-closed',),
                    'fields': ('entity','editor', 'exclusive_editor')}),
                )

    def changelist_view(self, request, extra_context=None):
        # Show a warning if user is not superuser
        if not request.user.is_superuser:
            messages.info(request,_('timeprofile|Warning: you will not be able to update a wake on lan task that you didn\'t create if exclusive editor is set to yes for this package'))
        else:
            self.list_editable = ('start_time','end_time')
        return super(timeprofileAdmin, self).changelist_view(request, extra_context)

    # Prevent deletion of objects when user hasn't enough permission
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        return True

    # Prevent to change objects when user hasn't enough permission
    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        else:
            return request.user.is_superuser or request.user.has_perm('deploy.change_timeprofile')

    def get_form(self, request, obj=None, **kwargs):
        form = super(timeprofileAdmin, self).get_form(request, obj, **kwargs)
        # Custom form to be able to use request in clean method
        # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
        # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
        class metaform(form):
            def __new__(cls, *args, **kwargs):
                kwargs['my_user'] = request.user
                return form(*args, **kwargs)
        return metaform

    def get_actions(self, request):
        actions = super(timeprofileAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
            del actions['mass_update']
        #    del actions['export_as_csv']
        return actions

    def get_queryset(self, request):
        # Re-create queryset with entity list returned by list_entities_allowed
        if request.user.is_superuser:
            return timeprofile.objects.all()
        else:
            return timeprofile.objects.filter(entity__pk__in = request.user.subuser.id_entities_allowed()).distinct()


class packagewakeonlanForm(ModelForm):
    class Meta:
        model = packagewakeonlan
        fields = '__all__'

    # Custom form to be able to use request in clean method
    # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
    # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
    def __init__(self, *args, **kwargs):
        self.my_user = kwargs.pop('my_user')
        super(packagewakeonlanForm, self).__init__(*args, **kwargs)
        self.fields['editor'].choices =([(self.my_user.id,self.my_user.username)])
        self.fields['editor'].widget.can_add_related = False
        if not self.my_user.is_superuser and 'entity' in self.fields:
            #restrict entity choice
            self.fields['entity'].queryset = entity.objects.filter(pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
            self.fields['entity'].required = True
            self.fields['machines'].queryset = machine.objects.filter(entity__pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
        if 'entity' in self.fields:
            self.fields['entity'].widget.can_add_related = False

    def clean_editor(self):
        return self.my_user


class packagewakeonlanAdmin(ueAdmin):
    list_display = ('name','description','date','status','editor','exclusive_editor')
    search_fields = ('name','description')
    filter_horizontal = ('machines','entity')
    form = packagewakeonlanForm
    fieldsets = (
            (_('packagewakeonlan|general information'), {'fields': ('name','description', 'date','status','machines')}),
                (_('package|permissions'), {
                    'classes': ('grp-collapse grp-closed',),
                    'fields': ('entity','editor', 'exclusive_editor')}),
                )

    def changelist_view(self, request, extra_context=None):
        # Show a warning if user is not superuser
        if not request.user.is_superuser:
            messages.info(request,_('packagewakeonlan|Warning: you will not be able to update a wake on lan task that you didn\'t create if exclusive editor is set to yes for this package'))
        else:
            self.list_editable = ('date','status')
        return super(packagewakeonlanAdmin, self).changelist_view(request, extra_context)

    # Prevent deletion of objects when user hasn't enough permission
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        return True

    # Prevent to change objects when user hasn't enough permission
    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        else:
            return request.user.is_superuser or request.user.has_perm('deploy.change_packagewakeonlan')

    def get_form(self, request, obj=None, **kwargs):
        form = super(packagewakeonlanAdmin, self).get_form(request, obj, **kwargs)
        # Custom form to be able to use request in clean method
        # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
        # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
        class metaform(form):
            def __new__(cls, *args, **kwargs):
                kwargs['my_user'] = request.user
                return form(*args, **kwargs)
        return metaform

    def get_actions(self, request):
        actions = super(packagewakeonlanAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
            del actions['mass_update']
        #    del actions['export_as_csv']
        return actions

    def get_queryset(self, request):
        # Re-create queryset with entity list returned by list_entities_allowed
        if request.user.is_superuser:
            return packagewakeonlan.objects.all()
        else:
            return packagewakeonlan.objects.filter(entity__pk__in = request.user.subuser.id_entities_allowed()).distinct()


class packageconditionForm(ModelForm):
    class Meta:
        model = packagecondition
        fields = '__all__'

    # Custom form to be able to use request in clean method
    # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
    # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
    def __init__(self, *args, **kwargs):
        self.my_user = kwargs.pop('my_user')
        super(packageconditionForm, self).__init__(*args, **kwargs)
        self.fields['editor'].choices =([(self.my_user.id,self.my_user.username)])
        self.fields['editor'].widget.can_add_related = False
        if not self.my_user.is_superuser and 'entity' in self.fields:
            #restrict entity choice
            self.fields['entity'].queryset = entity.objects.filter(pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
            self.fields['entity'].required = True
        if 'entity' in self.fields:
            self.fields['entity'].widget.can_add_related = False

    def clean_editor(self):
        return self.my_user


class packageconditionAdmin(ueAdmin):
    list_display = ('name','depends','softwarename','softwareversion','editor','exclusive_editor','get_condition_packages')
    filter_horizontal = ('entity',)
    list_filter = (conditionEntityFilter, myConditionsFilter)
    form = packageconditionForm
    fieldsets = (
            (_('packagecondition|general information'), {'fields': ('name','depends', 'softwarename', 'softwareversion')}),
                (_('packagecondition|permissions'), {
                    'classes': ('grp-collapse grp-closed',),
                    'fields': ('entity','editor', 'exclusive_editor')}),
                )
    def changelist_view(self, request, extra_context=None):
        # Show a warning if user is not superuser
        if not request.user.is_superuser:
            messages.info(request,_('packagecondition|Warning: you will not be able to update a condition that you didn\'t create if exclusive editor is set to yes for this package'))
        return super(packageconditionAdmin, self).changelist_view(request, extra_context)

    # Prevent deletion of objects when user hasn't enough permission
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        return True

    # Prevent to change objects when user hasn't enough permission
    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        else:
            return request.user.is_superuser or request.user.has_perm('deploy.change_packagecondition')

    def get_form(self, request, obj=None, **kwargs):
        form = super(packageconditionAdmin, self).get_form(request, obj, **kwargs)
        # Custom form to be able to use request in clean method
        # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
        # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
        class metaform(form):
            def __new__(cls, *args, **kwargs):
                kwargs['my_user'] = request.user
                return form(*args, **kwargs)
        return metaform

    def get_actions(self, request):
        actions = super(packageconditionAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
            del actions['mass_update']
        #    del actions['export_as_csv']
        return actions

    def get_queryset(self, request):
        # Re-create queryset with entity list returned by list_entities_allowed
        if request.user.is_superuser:
            return packagecondition.objects.all()
        else:
            return packagecondition.objects.filter(entity__pk__in = request.user.subuser.id_entities_allowed()).distinct()


class impexForm(ModelForm):
    class Meta:
        model = impex
        fields = '__all__'

    # Custom form to be able to use request in clean method
    # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
    # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
    def __init__(self, *args, **kwargs):
        self.my_user = kwargs.pop('my_user')
        super(impexForm, self).__init__(*args, **kwargs)
        self.fields['editor'].choices =([(self.my_user.id,self.my_user.username)])
        self.fields['editor'].widget.can_add_related = False
        # Prepare entity for the future
        #if not self.my_user.is_superuser and self.fields.has_key('entity'):
        #    #restrict entity choice
        #    self.fields['entity'].queryset = entity.objects.filter(pk__in = self.my_user.subuser.id_entities_allowed()).order_by('name').distinct()
        #    self.fields['entity'].required = True
        #if self.fields.has_key('entity'):
        #    self.fields['entity'].widget.can_add_related = False

    def clean_editor(self):
        return self.my_user


class impexAdmin(ueAdmin):
    list_display = ('date','name','description','filename_link','package','editor')
    list_display_links=('name',)
    search_fields = ('name','description')
    readonly_fields = ('packagesum',)
    form = impexForm
    # For the moment only Super Admin an superuser can use import
    # Entity aren't show. They will be usefull only in the future (if admin profile will be able to use impex)
    fieldsets = (
        (_('impex|general information'), {'fields': ('name','description', 'filename', 'package','editor')}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj: # editing an existing object
            return self.readonly_fields + ('filename', 'package')
        return self.readonly_fields

    # Prevent deletion of objects when user hasn't enough permission
    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        return True

    # Prevent to change objects when user hasn't enough permission
    def has_change_permission(self, request, obj=None):
        if obj is not None:
            return request.user.is_superuser or obj.editor == request.user or obj.exclusive_editor == 'no'
        else:
            return request.user.is_superuser or request.user.has_perm('deploy.change_impex')

    def get_form(self, request, obj=None, **kwargs):
        form = super(impexAdmin, self).get_form(request, obj, **kwargs)
        # Custom form to be able to use request in clean method
        # http://stackoverflow.com/questions/1057252/how-do-i-access-the-request-object-or-any-other-variable-in-a-forms-clean-met/1057640#1057640
        # http://stackoverflow.com/questions/2683689/django-access-request-object-from-admins-form-clean
        class metaform(form):
            def __new__(cls, *args, **kwargs):
                kwargs['my_user'] = request.user
                return form(*args, **kwargs)
        return metaform

admin.site.register(packagewakeonlan, packagewakeonlanAdmin)
admin.site.register(timeprofile, timeprofileAdmin)
admin.site.register(packagecondition, packageconditionAdmin)
admin.site.register(packageprofile, packageprofileAdmin)
admin.site.register(packagehistory, packagehistoryAdmin)
admin.site.register(package, packageAdmin)
admin.site.register(impex, impexAdmin)
