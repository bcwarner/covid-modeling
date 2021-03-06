import mesa
import numpy as np
import numpy.linalg
import numpy.random
import random

# CONSTANTS -------------------
immuno_increase = 1.5       # how much more likely are immunocompromised people to get sick 
c_l0_mult = 1.0             # how much more likely are c_l0 people to get sick
c_l1_mult = 0.5             # how much more likely are c_l1 people to get sick
c_l2_mult = 0.25            # how much more likely are c_l2 people to get sick
percent_asymptomatic = 0.38 # what percent of people will show symptoms
masked_infect_rate = 0.01   # how likey is a masked person to infect a cell 
unmasked_infect_rate = 0.10 # how likely is an unmasked person to infect a cell
shedding_symp = 14          # how long are symptomatic people contagious
shedding_asymp = 19         # how long are asymptomatic people contagious 
shedding_immuno = 28        # how long are immunocompromised people contagious
# ------------------------------

class BaseHuman(mesa.Agent):
	def __init__(self, unique_id, model, pos=(0,0), caution_level = 1, masked=False, immunocompromised = False, severity = 0.5, infected=False, symptomatic = False, incubation_period=0, viral_shedding=14, quarantined=False, recovered=False, immune=False, next_pos=(0, 0), seat = (0, 0), arrived = False):
		super().__init__(unique_id, model)
		self.caution_level = caution_level
		self.masked = masked
		self.immunocompromised = immunocompromised
		self.severity = np.double(severity)
		self.infected = infected
		self.symptomatic = symptomatic 
		self.incubation_period = incubation_period 
		self.viral_shedding = viral_shedding
		self.recovered = recovered
		self.immune = immune
		self.next_pos = next_pos
		self.seat = seat
		self.pos = pos
		self.last_pos = None
		self.arrived = arrived 
		self.unique_id = unique_id
		self.r0 = 0
		self.quarantined = False # LET 40-41 HANDLE QUARANTINING DO NOT CHANGE
		#print(caution_level, masked, severity, infected,  symptomatic, incubation_period, viral_shedding, recovered, immune, schedule, pos, unique_id, quarantined)
		if quarantined:
			self.quarantine(initialized=False)
		# since this changes, this shouldn't be here, use latter half instead self.steps_per_hour = self.model.steps_per_hour 

	def update_r0(self):
		self.r0 += 1
#
# self.init_infect()
# Set severity of symptoms and duration of viral_shedding of agent based off of immunocompromised 
# status. Set random agents as asymptomatic
	def init_infect(self):
		self.infected = True
		# Fix later: this won't be feasible if we're doing 600 steps per hour
		#self.viral_shedding = infection_duration  # * 24 * self.steps_per_hour # todo: find a distribution
		if self.immunocompromised:
			self.severity = random.uniform(0.75, 1.0) # give agent random severity
			self.viral_shedding = shedding_immuno # set duration of viral shedding
			self.incubation_period = 0 # immunocompromised agents will immediately  show symptoms
			return
		else:
			self.severity = random.random()
		if self.severity < percent_asymptomatic: # 38 % of people will be asymptomatic todo: find more reasonable numbers
			self.viral_shedding = shedding_asymp
			self.incubation_period = shedding_asymp
			self.symptomatic = False # aysmptomatic people will never develop symptoms
		else:
			r = random.random()
			if r <= 0.50:
				self.incubation_period = random.randint(3, 5) # 50% of people have incubation period of 3 - 5 days
			elif 0.50 < r <= 0.75:
				self.incubation_period = random.randint(0, 2) # 25% of people have incubation period of 0 - 2 days
			elif 0.75 < r:
				self.incubation_period = 6 # 25% of people have incubation period of 6 days 
			self.viral_shedding = shedding_symp
			self.symptomatic = True
#
# self.infect(contact, amount)
# Calculate chance of infection of agent based off of  their catuion level, the status of their contact 
# (human or environment). Infect agent based off of chance of infection.
	def infect(self, contact=None, amount=1.0): 
		# cannot become infected in invulnerable zone
		if self.pos in self.model.entrance_pos:
			return
		# don't infect if we've recovered or already infected
		if self.immune == True or self.infected == True:
			return
		chance = 1.0 # default chance 
		increase = amount # default increase in contraction
		# determine infection duration
		if isinstance(contact, BaseHuman):
			if contact.symptomatic:
				if not contact.immunocompromised:
					infection_duration = shedding_symp
				else:
					infection_duration = shedding_immuno
			elif not contact.symptomatic:
				infection_duration = shedding_asymp
		if self.immunocompromised:
			increase = immuno_increase # immunocomprimised peopel have greater chance at infection 
		if self.caution_level == 0: # chance of infection based off of how caution agent is 
			if isinstance(contact, BaseHuman): # varying chance based on how the agent came in contact with virus 
				chance = (contact.viral_shedding / infection_duration) * c_l0_mult# assumes infected people are most viral at start of infected period 
			else:
				chance = 0.1
		elif self.caution_level == 1:
			if isinstance(contact, BaseHuman):
				chance = (contact.viral_shedding / infection_duration) * c_l1_mult
			else:
				chance = 0.01
		elif self.caution_level == 2:
			if isinstance(contact, BaseHuman):
				chance = (contact.viral_shedding / infection_duration) * c_l2_mult
			else:
				chance = 0.001
		r, c = random.random(), chance * increase / self.model.steps_per_hour # need to figure out a balance between speed and feasibility in running
		if r < c:
			self.init_infect()
			if isinstance(contact, BaseHuman):
				contact.update_r0()
		else:
			return
#
# self.infect_cell(cell)
# Infect cell based off of status of agent.
	def infect_cell(self, neighbor):
		chance = 1.0 # default chance of infecting cell 
		if self.masked:
			chance = 1#(self.viral_shedding / 14) * masked_infect_rate # lower chance of infecting environment if masked 
		if random.random() < chance:
			amt = 1
			if self.masked:
				amt *= (1 - self.model.mask_efficacy)
			neighbor.infect(amount = amt / self.model.steps_per_hour, contact=self) # In the future, the initial amount may be important.
#
# self.recover()
# Update conditon of agent if recovered.
	def recover(self):
		self.infected = False
		self.viral_shedding = 0
		self.recovered = True
		self.immune = True
		if self.quarantined == True:
			self.pos = self.last_pos
			#print("Placed agent", self.unique_id)
			self.model.grid.place_agent(self, self.last_pos)
			self.quarantined = False
#
# self.quarantine(initialized)
# Store agent's last postion and remove from grid.
	def quarantine(self, initialized=True):
		self.last_pos = self.pos
		if initialized == True:
			self.model.grid.remove_agent(self)
			#print("Removed agent", self.unique_id)
		self.quarantined = True
#
# self.update_infection()
# Update infection status of agent, reduce viral shedding, set symptoms, recover if necessary.
	def update_infection(self):
		if not self.infected: # if not infected don't do anything 
			return
		self.viral_shedding -= 1 / self.model.steps_per_hour # reduce infection
		# determine incubation_period
		if self.symptomatic:
			if not self.immunocompromised:
				infection_duration = shedding_symp
			else:
				infection_duration = shedding_immuno
		elif not self.symptomatic:
			infection_duration = shedding_asymp
		if infection_duration - self.incubation_period <= self.viral_shedding: # develop symptoms after incubation period of virus
			self.symptomatic == True
		if self.viral_shedding <= 0: # set as recovered 
			self.recover()
#
# self.check_new_pos(pos = (x, y))
# Check contents of position and alter path of agent if obstacle in pos.
	def check_new_pos(self, pos):
		X, Y = pos[0], pos[1]
		if True in [isinstance(x, BaseHuman) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents((X, Y))]: # if obstacle in way
			#print("Obstacle")
			if True in [isinstance(x, BaseHuman) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents((self.pos[0], Y))]:
				X, Y = random.choice([(self.pos[0] - 1, Y), (self.pos[0] + 1, Y)])
			elif True in [isinstance(x, BaseHuman) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents((X, self.pos[1]))]:
				X, Y = random.choice([(X, self.pos[1] + 1), (X, self.pos[1] - 1)])
			else:
				choices = [(self.pos[0], self.pos[1] - 1), (self.pos[0] + 1, self.pos[1])]
				X, Y = random.choice(choices)
		if X < 0: # don't move off grid 
			X = 0
		elif X >= self.model.grid.width:
			X = self.model.grid.width - 1
		if Y < 0:
			Y += 1	
		elif Y >= self.model.grid.height:
			Y = self.model.grid.height - 1
		new_pos = (X, Y)
		return new_pos
#
# self.scheduled_move()
# Find goal position of agent. Update agent's position to move towards goal position. Check that agent
# can enter new position.
	def scheduled_move(self):
		goalX, goalY = self.next_pos[0], self.next_pos[1]
		X, Y = self.pos[0], self.pos[1]
		if goalX == X and goalY == Y: # if already arrived don't move
			return
		elif goalX < X:
			X -= 1
		elif goalX > X:
			X += 1
		if goalY < Y:
			Y -= 1
		elif goalY > Y:
			Y += 1
		new_pos = (X, Y)
		if new_pos[0] != goalX and new_pos[1] != goalY: # if haven't arrived check for obstacles 
			new_pos = self.check_new_pos(new_pos)
		if new_pos[0] == self.next_pos[0] and new_pos[1] == self.next_pos[1]:
			self.arrived = True 
		self.model.grid.move_agent(self, new_pos)
#
# self.move()
# Move agent towards scheduled position. Check infection status of surrounding cells and infect agent if
# necessaty. Infect cells surrounding agent if agent is infected.
	def move(self):
		if self.quarantined == True:
			return
		self.scheduled_move()
		# setting radius to 1 since it can pass through the walls
		for neighbor in self.model.grid.get_neighbors(self.pos, True, False): # second arg Moore, thrid arg include center, thrid arg radius 
			if not self.infected: # what will happen to uninfected agents
				if neighbor.infected:
					self.infect(contact=neighbor if isinstance(neighbor, BaseHuman) else neighbor.contact) # let infect() determmine if they should move from recovered to another category
			if self.infected: # what will infected agents do
				if not neighbor.infected and isinstance(neighbor, InfectableCell):
					self.infect_cell(neighbor)
#
# self.step()
# Move agent and update their infection.
	def step(self):
		self.move()
		self.update_infection()
		
class Student(BaseHuman):
	def __init__(self, unique_id, model, pos=(0,0), infected=False, masked=True, incubation_period=0, viral_shedding=14, immune=False, severity = 0.5, quarantined=False, caution_level = 1, next_pos=(0, 0), seat = (0, 0), recovered=False, arrived = False):
		super().__init__(unique_id, model, pos=pos, infected=infected, masked=masked, incubation_period=incubation_period, viral_shedding=viral_shedding, immune=immune, severity=severity, caution_level=caution_level, next_pos = next_pos, seat = seat, quarantined=quarantined, arrived = arrived)

class Faculty(BaseHuman):
	def __init__(self, unique_id, model, pos=(0,0), infected=False, masked=True, incubation_period=0, viral_shedding=14, immune=False, severity = 0.5, quarantined=False, caution_level = 1, next_pos=(0, 0), seat = (0, 0), recovered=False, arrived = False):
		super().__init__(unique_id, model, pos=pos, infected=infected, masked=masked, incubation_period=incubation_period, viral_shedding=viral_shedding, immune=immune, severity=severity, caution_level=caution_level, next_pos = next_pos, seat = seat, quarantined=quarantined, arrived = arrived)

class BaseEnvironment(mesa.Agent):
	def __init__(self, unique_id, model, pos=(0,0)):
		super().__init__(unique_id, model)
		self.pos = pos
		self.infected = False # default

	def step(self):
		pass

class UnexposedCell(BaseEnvironment): # unreachable by agents 
	def __init__(self, unique_id, model, pos=(0,0)):
		super().__init__(unique_id,model)
		self.infected = False

	def step(self):
		self.infected = False

class InfectableCell(BaseEnvironment): # could contain particles, air, surfaces, etc
	# decay in all cases is how much is left after one iteratoin
	def __init__(self, unique_id, model, pos=(0,0), infected = np.double(0), viral_shedding=0, transmissionLikelihood = 1, decay = .50):
		super().__init__(unique_id, model, pos) 
		self.infected = infected
		self.viral_shedding = viral_shedding
		self.transmissionLikelihood = transmissionLikelihood
		self.decay = decay
		self.contact = None

	def decay_cell(self):
		self.infected *= self.decay
		if self.infected < 0.1: # infected air only lasts for ~ 4 steps 
			self.infected = 0
			pass
		# if CovidModel.schedule.steps % infection_duration == 0: 
			# self.cleanse()

	def infect(self, amount = 1.0, contact=None):
		if contact is not None:
			self.contact = contact
		self.infected = min(self.infected + amount, 1.0) # Make sure we don't go past maximum capacity.

	def cleanse(self, percent = 1.0):
		self.infected *= (1 - percent)
		if self.infected < 0.001:
			self.infected == False

	def infect_agents(self):
		if not self.infected:
			return 
		for agent in self.model.grid.get_cell_list_contents(self.pos):
			if isinstance(agent, BaseHuman) and not agent.infected and not agent.recovered:
				if random.random() < self.infected:
					agent.infect(contact=self.contact, amount=self.infected) # In the future, the initial amount may be important.

	def step(self):
		self.decay_cell()
		self.infect_agents()

class SurfaceCell(InfectableCell): # interactable at edges, cannot be entered 
	def __init__(self, unique_id, model, pos=(0,0), infected = np.double(0), transmissionLikelihood = 1, decay = 1, cleaningInterval = -1, cleaned = True):
		super().__init__(unique_id, model, pos, infected, transmissionLikelihood, decay) 
		self.cleaningInterval = cleaningInterval
		self.lastCleaned = 0
		self.cleaned = cleaned

	def step(self):
		self.clean()
		

	def clean(self):
		self.lastCleaned += 1
		if self.cleaningInterval >= self.lastCleaned:
			self.lastCleaned = 0
			self.cleanse(1.0) # how effective are our cleaning measures?

class AirCell(InfectableCell): # can be traveled through 
	def __init__(self, unique_id, model, pos=(0,0), infected = np.double(0), transmissionLikelihood = 1, decay = 1, ventilationDirection = -1, ventilationDecay = 1):
		super().__init__(unique_id, model, pos, infected, transmissionLikelihood, decay) 
		self.ventilationDirection = ventilationDirection
		self.ventilationDecay = ventilationDecay

	def step(self):
		super().step()
		self.ventilate()
		

	def ventilate(self):
		possible_steps = self.model.grid.get_neighborhood(
			self.pos,
			moore=True, # can move diagonaly
			include_center=False)
		targets = []
		dx, dy = 0, 0
		target = None
		while len(targets) == 0:
			rand = False # quick hack to allow random directions
			if self.ventilationDirection == -1:
				rand = True
				self.ventilationDirection = np.random.random() * np.pi * 2
			dx, dy = int(np.round(np.cos(self.ventilationDirection))), int(np.round(np.sin(self.ventilationDirection)))
			x, y = dx + self.pos[0], dy + self.pos[1]
			if rand == True:
				self.ventilationDirection = -1
			targets = [z for z in possible_steps if z == (x, y) in possible_steps]
			horiz = dx + self.pos[0], self.pos[1]
			vert = self.pos[0], self.pos[1] + dy
			if horiz not in possible_steps:
				horiz = self.pos
			if vert not in possible_steps:
				vert = self.pos
			if True in [isinstance(x, UnexposedCell) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents(vert)] and True in [isinstance(x, UnexposedCell) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents(horiz)]:
				targets = []
				continue
				# check to see that we aren't passing a corner.
		target = targets[0]

		part_total = 0 
		# this would make it so that amount ventilated proportional to number of agents in cell, bad idea?
		for t in self.model.grid.get_cell_list_contents(target):
			if isinstance(t, InfectableCell):
				part_total += self.infected * (1 - self.ventilationDecay)
				t.infect(self.infected * (1 - self.ventilationDecay), contact=self.contact) # maybe make this so that the amount of particulates lost = particulate gains in other cells
			if isinstance(t, BaseHuman):
				t.infect(contact=self.contact)
		self.infected -= part_total

class Door(SurfaceCell): # upon interaction telleports agent to other side 
	def __init__(self, unique_id, model, pos=(0,0), infected = False, transmissionLikelihood = 1, decay = 1, cleaningInterval = 1, cleaned = True):
		super().__init__(unique_id, model, pos, infected, transmissionLikelihood, decay, cleaningInterval, cleaned)

class VentilatorCell(UnexposedCell):
	def __init__(self, unique_id, model, pos=(0,0), ventilationDecay=lambda rx, ry: 1 / (np.linalg.norm([rx, ry], 2)), maxRadius = 5):
		super().__init__(unique_id,model)
		self.ventilationDecay = ventilationDecay

	def step(self):
		self.ventilate()
		

	def ventilate(self):
		# rough outline complete later
		for x in range(self.model.width):
			for y in range(self.model.height):
				rx, ry = tuple(np.array(self.pos) - np.array((x, y)))
				cont = self.model.grid.get_cell_list_contents((x, y))
				cell.cleanse(self.ventilationDecay(rx, ry))
'''

	# agents will move randomly to a sqaure next to their current square
	def get_new_pos_near(self):
		possible_steps = self.model.grid.get_neighborhood(
			self.pos,
			moore=True, # can move diagonaly
			include_center=False)
		new_position = self.random.choice(possible_steps)	
		if True not in [isinstance(x, UnexposedCell) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents(new_position)]:
			if new_position is None:
				pass
				#print("new_pos of agent" + str(self.unique_id) + " is None")
			return new_position
		else:
			return self.get_new_pos_near()

	# agents will move randomly throughout grid
	def get_new_pos_far(self):
		new_position = random.randrange(self.model.width), random.randrange(self.model.height)  # get new position for agent w/in bounds of grid
		if True not in [isinstance(x, UnexposedCell) or isinstance(x, SurfaceCell) for x in self.model.grid.get_cell_list_contents(new_position)]: # Fixed it to work
			#say get_cell_list_contents is unexposed cell but agent will move there any way
			return new_position
		else:
			return self.get_new_pos_far()
'''