from flask import Flask

cnSnapshots = {}

class Computenode(object):

	# class variable shared by all instances
	# kind = 'computenode'
	name = None
	# create empty Lists for Parameters
	filesystem = None
	hardware = None
	network = None
	meta = None
	power = None
	storage = None
	vms = None

	def __init__(self, name):
		self.name = name
		# create empty Lists for Parameters
		self.filesystem = {}
		self.hardware = {}
		self.network = {}
		self.meta = {}
		self.power = {}
		self.storage = {}
		self.vms = {}
		cnSnapshots[name] = self
	
	def __repr__(self):
		return self.name+' Object'

	def update_filesystem(self, params):
		self.filesystem = params

	def update_hardware(self, params):
		self.hardware = params

	def update_network(self, params):
		self.network = params

	def update_meta(self, params):
		self.meta = params

	def update_power(self, params):
		self.power = params
	
	def update_storage(self, params):
		self.storage = params

	def update_vms(self, params):
		self.vms = params

	def display_data(self):
		print "filesystem: ", + self.filesystem
