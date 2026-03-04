# -*- coding: utf-8 -*-
import csv
import os
from inventory.models import machine, entity, net, osdistribution, software
from deploy.models import packagehistory
from django.db.models import Count, Max
from netaddr import IPNetwork, IPAddress


def run():
	host_name = 'PC-00'
	autoset_entity(host_name)

	# Test for all
	#for host in machine.objects.all():
	#	autoset_entity(host.name)


def autoset_entity(host_name):
	# Get the most recent date for the specified machine name
	lastsave__max = machine.objects.filter(name=host_name).aggregate(Max('lastsave'))['lastsave__max']

	# Automatic set the entity
	host_obj = machine.objects.filter(name=host_name, lastsave=lastsave__max)[0]
	if host_obj:

		#print("%s %s -> current entity id=%d" % (host_obj.name, lastsave__max, host_obj.entity_id))

		# Get ip address
		host_ip = net.objects.filter(host_id=host_obj.id).values_list('ip', flat=True)
		is_ip_matched = 0  # Test to stop after first ip match an entity
		for host_ip_addr in host_ip:
			if is_ip_matched:
				break
			host_ip_addr = "".join(host_ip_addr)
			print("test ip %s" % (host_ip_addr))

			# Search entity
			for entity_obj in entity.objects.exclude(ip_range__isnull=True).exclude(ip_range__exact=''):
				network = entity_obj.ip_range.split(',')
				for network_range in network:
					#print(network_range)
					try:
						if IPAddress(host_ip_addr) in IPNetwork(network_range):
							if host_obj.entity_id != entity_obj.id:
								#print("%s is in %s %s -> id = %d" % (host_ip_addr, entity_obj.ip_range, entity_obj.name, entity_obj.id))
								host_previous_entity = entity.objects.filter(id=host_obj.entity_id)[0]
								print("Entity updated for %s from '%s' to '%s'" % (host_obj.name, host_previous_entity.name, entity_obj.name))
								#host_obj.entity_id = entity_obj.id
								#host_obj.save()
							else:
								print("Entity is correct for %s : '%s'" % (host_obj.name, entity_obj.name))
							is_ip_matched = 1
					except Exception:
						print("Error: Invalid network in ip range for entity '%s' : '%s'" % (entity_obj.name, network_range))
						pass
