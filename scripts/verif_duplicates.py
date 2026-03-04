# -*- coding: utf-8 -*-
import csv
import os
from inventory.models import machine, entity, net, osdistribution, software
from deploy.models import packagehistory
from django.db.models import Count, Max
from netaddr import IPNetwork, IPAddress


def run():
	remove_duplicates()


def remove_duplicates():
	duplicates = machine.objects.values('name').annotate(
		count=Count('id'),
		max_lastsave=Max('lastsave')
	).filter(count__gt=1)

	for duplicate in duplicates:
		print(duplicate['name'], duplicate['max_lastsave'])
		current_host_obj = machine.objects.filter(
			name=duplicate['name'],
			lastsave=duplicate['max_lastsave']
		)[0]
		print("Curent machine : %s (%s) : %d -> Profile=%s" % (
			current_host_obj.name,
			current_host_obj.lastsave,
			current_host_obj.id,
			current_host_obj.packageprofile
		))

		for host_obj in machine.objects.filter(
			name=duplicate['name']
		).exclude(lastsave=duplicate['max_lastsave']):
			#for host_obj in machine.objects.filter(name = duplicate['name']):
				#if host_obj.name.startswith(current_host_obj.name):
					#print("Removed %s (%s) : %d -> %s" % (host_obj.name, host_obj.lastsave, host_obj.id, host_obj.packageprofile))
					#software.objects.filter(host_id=host_obj.id).delete()
					#osdistribution.objects.filter(host_id=host_obj.id).delete()
					#net.objects.filter(host_id=host_obj.id).delete()
					#packagehistory.objects.filter(machine_id=host_obj.id).delete()
					#machine.objects.filter(id=host_obj.id).delete()
				#else:
			print("Duplicated is %s (%s) : %d -> Profile=%s" % (
				host_obj.name,
				host_obj.lastsave,
				host_obj.id,
				host_obj.packageprofile
			))
				#current_host_obj.packageprofile = host_obj.packageprofile
				#current_host_obj.save()
