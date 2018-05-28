from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _
from inventory.models import entity
from deploy.models import packagehistory, packagecondition
from django.utils.encoding import force_unicode

# Filter dedicate to packagehistory pages
class entityFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('entity')
 
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'entity'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return entity.objects.all().order_by('name').values_list('name','name')
        else:
            return entity.objects.filter(pk__in = request.user.subuser.id_entities_allowed).order_by('name').values_list('name','name')
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'entity' in request.GET:
                return queryset.filter(machine__entity__name__iexact=self.value())
         else:
             return queryset

class machineFilter(SimpleListFilter):
    title = _('hostFilter')
    parameter_name = 'machine'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return packagehistory.objects.all().order_by('machine__name').values_list('machine__name','machine__name').distinct()
        else:
            return packagehistory.objects.filter(machine__entity__pk__in = request.user.subuser.id_entities_allowed).order_by('machine__name').values_list('machine__name','machine__name').distinct()
    
    def queryset(self, request, queryset):
         if self.value() is not None:
             if 'machine' in request.GET:
                 return queryset.filter(machine__name__iexact=self.value())
         else:
             return queryset

class statusFilter(SimpleListFilter):
    title = _('statusFilter')
    parameter_name = 'status'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return packagehistory.objects.all().order_by('status').values_list('status','status').distinct()
        else:
            return packagehistory.objects.filter(machine__entity__pk__in = request.user.subuser.id_entities_allowed).order_by('status').values_list('status','status').distinct()
    
    def queryset(self, request, queryset):
         if self.value() is not None:
             if 'status' in request.GET:
                 return queryset.filter(status__iexact=self.value())
         else:
             return queryset.exclude(status__startswith='Warning')

class packageHistoryFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('package')
 
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'package_name'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            all_packagehistory = packagehistory.objects.all()
            ph_list = list()
            for ph in all_packagehistory:
                if (ph.name, ph.name) not in ph_list:
                    ph_list.append((ph.name, ph.name))
            return ph_list        
            #return packagehistory.objects.all().order_by('name').values_list('name','name')
        else:

            all_packagehistory = packagehistory.objects.filter(machine__entity__pk__in = request.user.subuser.id_entities_allowed)
            ph_list = list()
            for ph in all_packagehistory:
                if (ph.name, ph.name) not in ph_list:
                    ph_list.append((ph.name, ph.name))
            return ph_list        
            #return packagehistory.objects.filter(machine__entity__pk__in = request.user.subuser.id_entities_allowed).order_by('name').values_list('name','name')
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'package_name' in request.GET:
                return queryset.filter(name__iexact=self.value())
         else:
             return queryset

# Filters dedicated to package pages
class packageEntityFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('entity')
 
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'package_entity'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return entity.objects.all().order_by('name').values_list('name','name')
        else:
            return entity.objects.filter(pk__in = request.user.subuser.id_entities_allowed).order_by('name').values_list('name','name')
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'package_entity' in request.GET:
                return queryset.filter(entity__name__iexact=self.value())
         else:
             return queryset
# Filters dedicated to package pages
class myPackagesFilter(SimpleListFilter):
    title = _('only my packages')
    parameter_name = 'my_packages'

    def choices(self, cl):
        yield {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.parameter_name]),
            'display': _('no'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_unicode(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def lookups(self, request, model_admin):
        return [('True',_('yes')),]
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'my_packages' in request.GET:
                return queryset.filter(editor=request.user)
         else:
             return queryset


class conditionFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('packagecondition')
 
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'package_condition'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return packagecondition.objects.all().order_by('name').values_list('name','name').distinct()
        else:
            return packagecondition.objects.filter(entity__pk__in = request.user.subuser.id_entities_allowed).order_by('name').values_list('name','name')
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'package_condition' in request.GET:
                return queryset.filter(conditions__name__iexact=self.value())
         else:
             return queryset
# Filters dedicated to condition pages
class conditionEntityFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('entity')
 
    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'condition_entity'
 
    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return entity.objects.all().order_by('name').values_list('name','name')
        else:
            return entity.objects.filter(pk__in = request.user.subuser.id_entities_allowed).order_by('name').values_list('name','name')
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'condition_entity' in request.GET:
                return queryset.filter(entity__name__iexact=self.value())
         else:
             return queryset

class myConditionsFilter(SimpleListFilter):
    title = _('only my conditions')
    parameter_name = 'my_conditions'

    def choices(self, cl):
        yield {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.parameter_name]),
            'display': _('no'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_unicode(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def lookups(self, request, model_admin):
        return [('True',_('yes')),]
    
    def queryset(self, request, queryset):
         if self.value() is not None:
            if 'my_conditions' in request.GET:
                return queryset.filter(editor=request.user)
         else:
             return queryset

