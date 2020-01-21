from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from inventory.models import software
from inventory.models import entity, machine, software, osdistribution


class enableFilter(SimpleListFilter):
    title = _('Activate advanced filter')
    parameter_name = 'enablefilter'

    def lookups(self, request, model_admin):
        return [('True', _('yes')), ]

    def queryset(self, request, queryset):
        return queryset

    def choices(self, cl):
        yield {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.parameter_name]),
            'display': _('no'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_text(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }


class as_or_notFilter(SimpleListFilter):
    title = _('As software or not?')
    parameter_name = 'asornot'

    def lookups(self, request, model_admin):
        if 'enablefilter' in request.GET:
            return [('True', _('as_not_software')), ]
        else:
            return

    def queryset(self, request, queryset):
        return queryset

    def choices(self, cl):
        yield {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.parameter_name]),
            'display': _('as_software'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_text(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }


class softwareFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('software')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'softname'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        if 'enablefilter' in request.GET:
            if request.user.is_superuser:
                return software.objects.all().order_by('name').values_list('name', 'name').distinct()
            return software.objects.filter(host__entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('name').values_list('name', 'name').distinct()
        else:
            return

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if 'asornot' in request.GET and 'enablefilter' in request.GET:
            if self.value() is not None:
                if 'softversion' in request.GET:
                    if software.objects.filter(version__iexact=request.GET['softversion'], name__iexact=self.value()).exists():
                        return queryset.exclude(software__version__iexact=request.GET['softversion'], software__name__iexact=self.value())
                    else:
                        return queryset.exclude(software__name__iexact=self.value())
                else:
                    return queryset.exclude(software__name__iexact=self.value())
        elif 'enablefilter' in request.GET:
            if self.value() is not None:
                if 'softversion' in request.GET:
                    if software.objects.filter(version__iexact=request.GET['softversion'], name__iexact=self.value()).exists():
                        return queryset.filter(software__name__iexact=self.value(), software__version__iexact=request.GET['softversion'])
                    else:
                        return queryset.filter(software__name__iexact=self.value())
                else:
                    return queryset.filter(software__name__iexact=self.value())
            else:
                return queryset
        else:
            return queryset


class versionFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('softversion')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'softversion'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """

        if 'enablefilter' in request.GET:
            if 'softname' in request.GET:
                if request.user.is_superuser:
                    return software.objects.filter(name__iexact=request.GET['softname']).order_by('version').values_list('version', 'version').distinct()
                else:
                    return software.objects.filter(
                        host__entity__pk__in=request.user.subuser.id_entities_allowed,
                        name__iexact=request.GET['softname']).order_by('version').values_list('version', 'version').distinct()
        else:
            return

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        return queryset


class entityFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('entity')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'entity'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return entity.objects.all().order_by('name').values_list('name', 'name')
        else:
            return entity.objects.filter(pk__in=request.user.subuser.id_entities_allowed()).order_by('name').values_list('name', 'name')

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'entity' in request.GET:
                list_head_entity = [entity.objects.get(name__iexact=self.value())]
                entity_children_list = entity.get_all_children(list_head_entity, list())
                return queryset.filter(entity__name__in=entity_children_list)
        return queryset


class domainFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('domain')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'domain'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('domain').values_list('domain', 'domain').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('domain').values_list('domain', 'domain').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'domain' in request.GET:
                return queryset.filter(domain__iexact=self.value())
        else:
            return queryset


class usernameFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('username')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'username'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('username').values_list('username', 'username').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('username').values_list('username', 'username').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'username' in request.GET:
                return queryset.filter(username__iexact=self.value())
        else:
            return queryset


class languageFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('language')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'language'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('language').values_list('language', 'language').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('language').values_list('language', 'language').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'language' in request.GET:
                return queryset.filter(language__iexact=self.value())
        else:
            return queryset


class typemachineFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('typemachine')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'typemachine'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('typemachine__name').values_list('typemachine__name', 'typemachine__name').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('typemachine__name').values_list('typemachine__name', 'typemachine__name').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'typemachine' in request.GET:
                return queryset.filter(typemachine__name__iexact=self.value())
        else:
            return queryset


class osdistributionFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('osdistribution')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'osdistribution'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return osdistribution.objects.all().order_by('name').values_list('name', 'name').distinct()
        else:
            return osdistribution.objects.filter(host__entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('name').values_list('name', 'name').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'osdistribution' in request.GET:
                return queryset.filter(osdistribution__name__iexact=self.value())
        else:
            return queryset


class timeprofileFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('timeprofile')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'timeprofile'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('timeprofile__name').values_list('timeprofile__name', 'timeprofile__name').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('timeprofile__name').values_list('timeprofile__name', 'timeprofile__name').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'timeprofile' in request.GET:
                return queryset.filter(timeprofile__name__iexact=self.value())
        else:
            return queryset


class packageprofileFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('packageprofile')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'packageprofile'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('packageprofile__name').values_list('packageprofile__name', 'packageprofile__name').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('packageprofile__name').values_list('packageprofile__name', 'packageprofile__name').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'packageprofile' in request.GET:
                return queryset.filter(packageprofile__name__iexact=self.value())
        else:
            return queryset


class osnameFilter(SimpleListFilter):
    title = _('osname')
    parameter_name = 'osname'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.filter().order_by('osdistribution__name').values_list('osdistribution__name', 'osdistribution__name').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('osdistribution__name').values_list('osdistribution__name', 'osdistribution__name').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'osname' in request.GET:
                return queryset.filter(name__iexact=self.value())
        else:
            return queryset


class osversionFilter(SimpleListFilter):
    title = _('osversion')
    parameter_name = 'osversion'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('osdistribution__version').values_list('osdistribution__version', 'osdistribution__version').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('osdistribution__version').values_list('osdistribution__version', 'osdistribution__version').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'osversion' in request.GET:
                return queryset.filter(version__iexact=self.value())
        else:
            return queryset


class osarchFilter(SimpleListFilter):
    title = _('osarch')
    parameter_name = 'osarch'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('osdistribution__arch').values_list('osdistribution__arch', 'osdistribution__arch').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('osdistribution__arch').values_list('osdistribution__arch', 'osdistribution__arch').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'osarch' in request.GET:
                # Allow filter to be used with machine or osdistribution objects
                if type(queryset[0]) == machine:
                    return queryset.filter(osdistribution__arch__iexact=self.value())
                else:
                    return queryset.filter(arch__iexact=self.value())
        else:
            return queryset


class hostFilter(SimpleListFilter):
    title = _('hostFilter')
    parameter_name = 'host'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('name').values_list('name', 'name').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('name').values_list('name', 'name').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'host' in request.GET:
                return queryset.filter(host__name__iexact=self.value())
        else:
            return queryset


class commentFilter(SimpleListFilter):
    title = _('commentFilter')
    parameter_name = 'comment'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            return machine.objects.all().order_by('comment').values_list('comment', 'comment').distinct()
        else:
            return machine.objects.filter(entity__pk__in=request.user.subuser.id_entities_allowed()).order_by('comment').values_list('comment', 'comment').distinct()

    def queryset(self, request, queryset):
        if self.value() is not None:
            if 'comment' in request.GET:
                return queryset.filter(comment__iexact=self.value())
        else:
            return queryset
