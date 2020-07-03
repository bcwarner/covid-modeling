import mesa
import numpy as np

class BaseHuman(mesa.Agent):
	def __init__(self, unique_id, model, pos=(0,0), infected=False, masked=True, incubation_period=0, contagion_counter=0, immune=False, immunocompromised=False, susceptibility=1, schedule=[[0, 0, 0]], quarantined=False, recovered=False):
		super().__init__(unique_id, model)
		self.infected = infected
		self.masked = masked
		self.incubation_period = incubation_period 
		self.contagion_counter = contagion_counter
		self.immune = immune
		self.immunocompromised = immunocompromised
		self.susceptibility = np.double(susceptibility)
		self.schedule = np.reshape(schedule, (-1, 3)) # Effectively a list of tuples representing (t, x, y)
		self.quarantined = quarantined
		self.recovered = recovered
		self.pos = pos

	def step(self):
		pass

class Student(BaseHuman):
	def __init__(self, unique_id, model, pos=(0,0), infected=False, masked=True, incubation_period=0, contagion_counter=0, immune=False, immunocompromised=False, susceptibility=1, schedule=[[0, 0, 0]], quarantined=False, recovered=False):
		super().__init__(unique_id, pos, model, infected, masked, incubation_period, contagion_counter, immune, immunocompromised, susceptibility, schedule, quarantined)

class Faculty(BaseHuman):
	def __init__(self, unique_id, model, pos=(0,0), infected=False, masked=True, incubation_period=0, contagion_counter=0, immune=False, immunocompromised=False, susceptibility=1, schedule=[[0, 0, 0]], quarantined=False, recovered=False):
		super().__init__(unique_id, pos, model, infected, masked, incubation_period, contagion_counter, immune, immunocompromised, susceptibility, schedule, quarantined)

class BaseEnvironment(mesa.Agent):
	def __init__(self, unique_id, model, pos=(0,0)):
		super().__init__(unique_id, model)
		self.pos = pos

	def step(self):
		pass

# added 07/03 
class UnexposedCell(BaseEnvironment): # unreachable by agents 
	def __intit__(self, unique_id, model, pos=(0,0)):
		super().__init__(unique_id,model)

class InfectableCell(BaseEnvironment): # could contain particles, air, surfaces, etc 
	def __init__(self, unique_id, model, pos=(0,0), infected = False, transmissionLikelyhood = 1, decay = 1):
		super().__init__(unique_id, model, pos) 
		self.infected = infected
		self.transmissionLikelyhood = transmissionLikelyhood
		self.decay = decay

class SurfaceCell(InfectableCell): # interactable at edges, cannot be entered 
	def __init__(self, unique_id, model, pos=(0,0), infected = False, transmissionLikelyhood = 1, decay = 1, cleaningInterval = 1, cleaned = True):
		super().__init__(unique_id, model, pos, infected, transmissionLikelyhood, decay) 
		self.cleaningInterval = cleaningInterval
		self.cleaned = cleaned

class AirCell(InfectableCell): # can be traveled through 
	def __init__(self, unique_id, model, pos=(0,0), infected = False, transmissionLikelyhood = 1, decay = 1, ventilationDirection = -1, ventilationDecay = 1):
		super().__init__(unique_id, model, pos, infected, transmissionLikelyhood, decay) 
		self.ventilationDirection = ventilationDirection
		self.ventilationDecay = ventilationDecay

class Door(SurfaceCell): # upon interaction telleports agent to other side 
	def __init__(self, unique_id, model, pos=(0,0), infected = False, transmissionLikelyhood = 1, decay = 1, cleaningInterval = 1, cleaned = True):
		super().__init__(unique_id, model, pos, infected, transmissionLikelyhood, decay, cleaningInterval, cleaned)

'''
this one seemed a little complicated and I wasn't quite sure how to appraoch it 
class VentilatorCell(UnexposedCell):
	def __intit__(self, unique_id, model, pos=(0,0), ventilationDecay):
		super().__init__(unique_id,model)
'''
