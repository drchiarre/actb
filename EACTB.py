# -*- coding: utf-8 -*-

##############################################################################################
#  This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 #
# International License. To view a copy of this license, visit                               # 
#                                                                                            #
#   http://creativecommons.org/licenses/by-nc-sa/4.0/                                        #
#
# or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.           #
##############################################################################################

#####################################################################
#			Program name: EACTB.py				                    #
#			Author: Davide Chiarella                                #
#			Email: davide.chiarella@cnr.it                          #
#			Input: label for run such as a number                   #
#			Output:                                                 #
#                   - 1 file containing list of remaining arguments # 
#                       per epoch                           		#
#                   - 1 file containing opinion distribution of     # 
#                       agents per epoch (array lenght 100 0 -> 1)	#
#                   - 1 file containing results of each run called  # 
#                       totale_run.txt                              #
#####################################################################


from random import randrange
import random
import networkx as nx
from graphviz import Digraph
import itertools
import numpy
import sys
import os
import tempfile

num_run = sys.argv[1]

# scenario number
num_scenario=1
# agent memory
S=4 
# total # arguments
argomenti_totali = 40
# number of agents
popolazione = 20
# resiliency not implemented
p1 = 0
# enthusiasm not implemented
p2 = 1
# homophily h=0 ---> preferential update
h = 0
# preferential update
pref_update_percentage = 0.7
#  preferential communication
pref_comm_percentage = 0.7
#  preferential update 3 
pref_update3_percentage = 1
# preferential communication 3 
pref_comm3_percentage = 0
# VU number of pro arguments to juxtapose
VU_pros = 1
# test epochs only for test purposes
epochs = 120000

# opinion precision: opinion is rounded to the specified number of decimals
# it rules also the lenght of the "array-dictionary" for world_opinion
opinion_precision = 2
# verbose only for debug purposes
#verbose = True
verbose = False
# enabling/disabling logging: everything that happens in an epoch is printed on screen (or use the redirect!!!)
log = True
#log = False
#condition of stop
stop= False

# check VU_pros < S
if(VU_pros >= S):
  print("VU_pros variable incompatible with S variable")
  exit()
# world_opinion initialization: it is used for 3d graphs
world_opinion = {}
step = 10**(opinion_precision* -1)
world_opinion[0.0] = 0
for i in range(1,((10**opinion_precision)+1)):
  world_opinion[round(step*i,2)] = 0
print(world_opinion)

class Agent:
  # id agent, opinion ,  arguments array
  def __init__(self, id, arg_recency, opinion):
    self.id = id
    self.arg_recency = arg_recency
    self.opinion = opinion
  def print(self):
    print("AGENT_ID: {0} OPINION: {1} ARGUMENTS: {2}".format(str(self.id),str(self.opinion),str(self.arg_recency)))# if log else None

class Argument:
  def __init__(self, id, value):
    self.id = id
    self.value = value
  def print(self):
    print("ID_ARG: "+str(self.id) + " VALUE: "+ str(self.value))
  def SetStrenght(self, value):
    self.value = value


def MemoriaCasuale(argument_set):
  memoria=[]
  i = 0
  while i < S:
    # from 1 to argomenti_totali, because 0 is the topic
    arg_scelto = argument_set[randrange(0,argomenti_totali)].id
    if  arg_scelto not in memoria:
      memoria.append(arg_scelto)
      i = i + 1
  return memoria

def MemoriaCasualeSpecifica(argument_set, number_pos, number_neg):
  memoria=[]
  i = 0
  while i < S:
    if (i in range(number_pos)):
      # remember that by HP we have all positives argument in the first half
      # argument_set
      arg_scelto = argument_set[randrange(0,argomenti_totali/2)].id
      if  arg_scelto not in memoria:
        memoria.append(arg_scelto)
        i = i + 1
    elif(i in range(number_pos,number_pos+number_neg)):
      # remember that by HP we have all negatives argument in the second half
      # argument_set
      arg_scelto = argument_set[randrange(argomenti_totali/2,argomenti_totali)].id
      if  arg_scelto not in memoria:
        memoria.append(arg_scelto)
        i = i + 1
  random.shuffle(memoria)
  return memoria

def Discussion(agent1, agent2):
  papabili = [item for item in agent1.arg_recency if item not in agent2.arg_recency]
  if papabili:
    new = papabili[random.randrange(0, len(papabili))]
    agent2.arg_recency.pop(0)
    agent2.arg_recency.append(new)
    return True
  else:
    print("Siamo due gocce d'acqua")
  return True
  
def DiscussionRep(agent1, agent2):
  new = agent1.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  agent2.arg_recency.pop(0)
  agent2.arg_recency.append(new)
  return True
  
def DiscussionRep2(agent1, agent2):
  new = agent1.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  if (new in agent2.arg_recency):
    index_target = agent2.arg_recency.index(new)
    agent2.arg_recency.pop(index_target)
    agent2.arg_recency.append(new)
    return False
  else:
    agent2.arg_recency.pop(0)
    agent2.arg_recency.append(new)
  return True

def DiscussionRep3(agent1, agent2):
  new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  if (new in agent1.arg_recency):
    index_target = agent1.arg_recency.index(new)
    agent1.arg_recency.pop(index_target)
    agent1.arg_recency.append(new)
    return False
  else:
    agent1.arg_recency.pop(0)
    agent1.arg_recency.append(new)
  return True

def PrefArgumentOld(agent):
  opinion = agent.opinion
  if (opinion == 0.5):
    return agent.arg_recency[random.randrange(0, len(agent.arg_recency))]
  arg_chosen = -1
  for x in agent.arg_recency:
    polarity = IsPosOrCon(x,0,knowledge_graph)
    if ((opinion > 0.5) and (polarity == 1)) or ((opinion < 0.5) and (polarity == -1)):
      arg_chosen = x
      return arg_chosen
  return -1

def PrefArgument(agent):
  opinion = agent.opinion
  if (opinion == 0.5):
    return agent.arg_recency[random.randrange(0, len(agent.arg_recency))]
  arg_chosen = []
  for x in agent.arg_recency:
    polarity = IsPosOrCon(x,0,knowledge_graph)
    if ((opinion > 0.5) and (polarity == 1)) or ((opinion < 0.5) and (polarity == -1)):
      arg_chosen.append(x)
  return arg_chosen[random.randrange(0, len(arg_chosen))]

def PrefArgument2(agent):
  opinion = agent.opinion
  if (opinion == 0.5):
    return agent.arg_recency[random.randrange(0, len(agent.arg_recency))]
  arg_chosen_list = []
  arg_strenght_list = []
  for x in agent.arg_recency:
    polarity = IsPosOrCon(x,0,knowledge_graph)
    print(f"Agent {agent.id} {agent.arg_recency} {agent.opinion}: argument {x} with polarity {polarity} under scrutiny")
    if ((opinion > 0.5) and (polarity == 1)) or ((opinion < 0.5) and (polarity == -1)):

      arg_chosen_list.append(x)
      agent_knowledge_graph = knowledge_graph.subgraph(agent.arg_recency).copy()
      arg_strenght_list.append(polarity * CalculateArgumentStrenght(x, agent_knowledge_graph))
  print(f"Arguments list of Agent {agent.id} with right polarity: {arg_chosen_list}")
  print(f"Related arguments strenght : {arg_strenght_list}")
  index_of_max = arg_strenght_list.index(max(arg_strenght_list))
  print(f"Strongest argument is: {arg_chosen_list[index_of_max]}")
  return arg_chosen_list[index_of_max]

def VigilantUpdate(agent1, agent2, num_in_fav=1):
  second_arg = []
  new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  polarity = IsPosOrCon(new,0,knowledge_graph)
  polarity = int(polarity)
  if( ((polarity == 1) and (agent1.opinion > 0.5)) or ((polarity == -1) and (agent1.opinion < 0.5)) or  (agent1.opinion == 0.5)):
    print(f"NORMAL: Agent {agent2.id} is passing to Agent {agent1.id} argument {new} which is in line of its opinion {agent1.opinion}.")
    if (new in agent1.arg_recency):
      index_target = agent1.arg_recency.index(new)
      agent1.arg_recency.pop(index_target)
      agent1.arg_recency.append(new)
      return False
    else:
      agent1.arg_recency.pop(0)
      agent1.arg_recency.append(new)
    return True
  else:
    arg_chosen_list = []
    print(f"VIGILANT UPDATE: Agent {agent2.id} is passing to Agent {agent1.id} argument {new} which is not in line of its opinion {agent1.opinion}.")
    print(f"VIGILANT UPDATE: Agent {agent1.id} will choose {num_in_fav} arguments to rebut {new}.")
    print(f"Argomenti di {agent1.id}: {agent1.arg_recency} .")
    for x in range(1,argomenti_totali+1):
      polarity = IsPosOrCon(x,0,knowledge_graph)
      print(f"Argument {x} with polarity {polarity} under scrutiny.") #if verbose else None
 
      if ( (((agent1.opinion > 0.5) and (polarity == 1)) or ((agent1.opinion < 0.5) and (polarity == -1))) and (x not in agent1.arg_recency)):
        print(f"Argument {x} added to pool.") #if verbose else None
        arg_chosen_list.append(x)

    print(f"List of possible args to choose: {arg_chosen_list}")
    for x in range(num_in_fav):
      pro_to_add = random.choice(arg_chosen_list)
      second_arg.append(pro_to_add)
      arg_chosen_list.remove(pro_to_add)
	  
    print(f"Chosen arg to juxtapose to {new}: {second_arg}")
    # removing num_in_fav+1 arguments
    for x in range(num_in_fav+1):
     agent1.arg_recency.pop(0)
    # adding the cons arg
    agent1.arg_recency.append(new)
    # adding num_in_fav pro arguments
    agent1.arg_recency.extend(second_arg)
    return True

def PrefUpdateArgumentsList(arg_list, opinion, pref_update_percentage,num_in_fav):
  branch =  random.uniform(0, 1)
  arg_list_target = []
  removed = 0
  if(opinion < 0.5):
    opinion = -1
  elif(opinion > 0.5):
    opinion = 1
  else:
    for x in range(num_in_fav+1):
      arg_list.pop(0)
      return arg_list
  if(branch <= pref_update_percentage):
    print(f"Preferential update ENABLED: branch prob {branch}% ---- pref update prob {pref_update_percentage}%")
    for index, arg in enumerate(arg_list):
        polarity = IsPosOrCon(arg,0,knowledge_graph)
        polarity = int(polarity)
        if(polarity != opinion):
          arg_list_target.append(arg_list[index])
    print(f"Args cons to my opinion: {arg_list_target} .")
    print(f"Lenght of args_list_target: {len(arg_list_target)} .") 
    for x in arg_list_target:
        print(f"Removing {x} from {arg_list} .") 
        arg_list.remove(x)
    while((len(arg_list)-S)>0):
        arg_list.pop(0)
    return arg_list
  else:
    print(f"Preferential update DISABLED: branch prob {branch}% ---- pref update prob {pref_update_percentage}%")
    while((len(arg_list)-S)>0):
      arg_list.pop(0)
    return arg_list

def VigilantUpdatePrefUpdate(agent1, agent2, num_in_fav=1):
  second_arg = []
  new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  polarity = IsPosOrCon(new,0,knowledge_graph)
  polarity = int(polarity)
  if( ((polarity == 1) and (agent1.opinion > 0.5)) or ((polarity == -1) and (agent1.opinion < 0.5)) or  (agent1.opinion == 0.5)):
    print(f"NORMAL: Agent {agent2.id} is passing to Agent {agent1.id} argument {new} which is in line of its opinion {agent1.opinion}.")
    if (new in agent1.arg_recency):
      index_target = agent1.arg_recency.index(new)
      agent1.arg_recency.pop(index_target)
      agent1.arg_recency.append(new)
      return False
    else:
      agent1.arg_recency.pop(0)
      agent1.arg_recency.append(new)
    return True
  else:
    arg_chosen_list = []
    print(f"VIGILANT UPDATE: Agent {agent2.id} is passing to Agent {agent1.id} argument {new} which is not in line of its opinion {agent1.opinion}.")
    print(f"VIGILANT UPDATE: Agent {agent1.id} will choose {num_in_fav} arguments to rebut {new}.")
    print(f"Argomenti di {agent1.id}: {agent1.arg_recency} .") 
    for x in range(1,argomenti_totali+1):
      polarity = IsPosOrCon(x,0,knowledge_graph)
      print(f"Argument {x} with polarity {polarity} under scrutiny.") #if verbose else None

      if ( (((agent1.opinion > 0.5) and (polarity == 1)) or ((agent1.opinion < 0.5) and (polarity == -1))) and (x not in agent1.arg_recency)):
        print(f"Argument {x} added to pool.") #if verbose else None
        arg_chosen_list.append(x)

    print(f"Argomenti di {agent1.id}: {agent1.arg_recency} .") 
    print(f"List of possible args to choose: {arg_chosen_list}")
    for x in range(num_in_fav):
      pro_to_add = random.choice(arg_chosen_list)
      second_arg.append(pro_to_add)
      arg_chosen_list.remove(pro_to_add)
      
    print(f"Chosen arg to juxtapose to {new}: {second_arg}")
    args_long_list = agent1.arg_recency + [new] + second_arg
    print(f"My head is turning, too many args: {args_long_list}")
    # removing args
    # if P then PrefUpdate and remove num_in_fav+1 arguments
    agent1.arg_recency = PrefUpdateArgumentsList(args_long_list, agent1.opinion, pref_update_percentage, num_in_fav)
    print(f"I rearranged the ideas. Now my args are: {args_long_list}")
    return True

def PrefUpdateArgumentsList2(arg_present, suggested_arg, rebut_args,opinion, pref_update_percentage,num_in_fav):
  branch =  random.uniform(0, 1)
  arg_list_target = []
  removed = 0
  if(opinion < 0.5):
    opinion = -1
  elif(opinion > 0.5):
    opinion = 1
  else:
    for x in range(num_in_fav+1):
      print(f"Neutral opinion: adding {suggested_arg} and throwing away {arg_present[0]}")
      arg_present.append(suggested_arg)
      arg_present.pop(0)
      print(f"Removing oldest args and getting the following memory: {arg_present}.%")
      return arg_present
  if(branch <= pref_update_percentage):
    print(f"Preferential update ENABLED: branch prob {branch}% ---- pref update prob {pref_update_percentage}%")
    polarity = IsPosOrCon(suggested_arg,0,knowledge_graph)
    polarity = int(polarity)
    if(polarity != opinion):
        print(f"Not accepting arg {suggested_arg} which goes against my opinion {opinion}, but adding new ones in favour {rebut_args}.%")
        arg_present.extend(rebut_args)
        while((len(arg_present)-S)>0):
            arg_present.pop(0)
        print(f"Removing oldest args and getting the following memory: {arg_present}.%")
        return arg_present
    else:
        print(f"Accepting arg {suggested_arg} which is in favour of my opinion {opinion} and adding also new ones in favour {rebut_args}.%")
        arg_present.append(suggested_arg)
        arg_present.extend(rebut_args)
        while((len(arg_present)-S)>0):
            arg_present.pop(0)
        print(f"Removing oldest args and getting the following memory: {arg_present}.%")
        return arg_present
  else:
    print(f"Preferential update DISABLED: branch prob {branch}% ---- pref update prob {pref_update_percentage}%")
    # adding suggested_arg 
    arg_present.append(suggested_arg)
    # adding rebut_args 
    arg_present.extend(rebut_args)
    while((len(arg_present)-S)>0):
        arg_present.pop(0)
    return arg_present

def VigilantUpdatePrefUpdate2(agent1, agent2, num_in_fav=1):
  second_arg = []
  new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  polarity = IsPosOrCon(new,0,knowledge_graph)
  polarity = int(polarity)
  if( ((polarity == 1) and (agent1.opinion > 0.5)) or ((polarity == -1) and (agent1.opinion < 0.5)) or  (agent1.opinion == 0.5)):
    print(f"NORMAL: Agent {agent2.id} is passing to Agent {agent1.id} argument {new} which is in line of its opinion {agent1.opinion}.")
    if (new in agent1.arg_recency):
      index_target = agent1.arg_recency.index(new)
      agent1.arg_recency.pop(index_target)
      agent1.arg_recency.append(new)
      return False
    else:
      agent1.arg_recency.pop(0)
      agent1.arg_recency.append(new)
    return True
  else:
    arg_chosen_list = []
    print(f"VIGILANT UPDATE: Agent {agent2.id} is passing to Agent {agent1.id} argument {new} which is not in line of its opinion {agent1.opinion}.")
    print(f"VIGILANT UPDATE: Agent {agent1.id} will choose {num_in_fav} arguments to rebut {new}.")
    print(f"Argomenti di {agent1.id}: {agent1.arg_recency} .") 
    for x in range(1,argomenti_totali+1):
      polarity = IsPosOrCon(x,0,knowledge_graph)
      print(f"Argument {x} with polarity {polarity} under scrutiny.") #if verbose else None

      if ( (((agent1.opinion > 0.5) and (polarity == 1)) or ((agent1.opinion < 0.5) and (polarity == -1))) and (x not in agent1.arg_recency)):
        print(f"Argument {x} added to pool.") #if verbose else None
        arg_chosen_list.append(x)

    print(f"Argomenti di {agent1.id}: {agent1.arg_recency} .") 
    print(f"List of possible args to choose: {arg_chosen_list}")
    for x in range(num_in_fav):
      pro_to_add = random.choice(arg_chosen_list)
      second_arg.append(pro_to_add)
      arg_chosen_list.remove(pro_to_add)
      
    print(f"Chosen arg to juxtapose to {new}: {second_arg}")
    print(f"My head is turning, too many args: {agent1.arg_recency + [new] + second_arg}")
    # removing args
    # if P then PrefUpdate and remove num_in_fav+1 arguments
    agent1.arg_recency = PrefUpdateArgumentsList2(agent1.arg_recency,new,second_arg, agent1.opinion, pref_update_percentage, num_in_fav)
    print(f"I rearranged the ideas. Now my args are: {agent1.arg_recency}")
    return True


def OneOfStrongest(agent):
  arg_strenght_list = []
  agent_knowledge_graph = knowledge_graph.subgraph(agent.arg_recency).copy()
  for x in agent.arg_recency:
    arg_strenght_list.append(CalculateArgumentStrenght(x, agent_knowledge_graph))
  print(f"Arguments list of Agent {agent.id}: {agent.arg_recency}")
  print(f"Related arguments strenght : {arg_strenght_list}")
  m = max(arg_strenght_list)
  index_list_max = [i for i, j in enumerate(arg_strenght_list) if j == m]
  index_of_chosen = random.choice(index_list_max)
  print(f"Strongest random argument chosen is: {agent.arg_recency[index_of_chosen]}")
  return agent.arg_recency[index_of_chosen]  
  
def FindTheWeakest(agent):
  opinion = agent.opinion
  if (opinion == 0.5):
    print("You should not be here!!!!!!!")
    return agent.arg_recency[random.randrange(0, len(agent.arg_recency))]
  arg_chosen_list = []
  arg_strenght_list = []
  for x in agent.arg_recency:
    polarity = IsPosOrCon(x,0,knowledge_graph)
    if ((opinion > 0.5) and (polarity == 1)) or ((opinion < 0.5) and (polarity == -1)):
      arg_chosen_list.append(x)
      agent_knowledge_graph = knowledge_graph.subgraph(agent.arg_recency).copy()
      arg_strenght_list.append(polarity * CalculateArgumentStrenght(x, agent_knowledge_graph))
  print(f"Arguments list of Agent {agent.id} with right polarity: {arg_chosen_list}")
  print(f"Related arguments strenght : {arg_strenght_list}")
  index_of_min = arg_strenght_list.index(min(arg_strenght_list))
  print(f"Weakest argument is: {arg_chosen_list[index_of_min]}")
  return arg_chosen_list[index_of_min]


def DiscussionPrefComm1PrefUpdate1(agent1, agent2):
  branch_update = random.uniform(0, 1)
  branch_communication = random.uniform(0, 1)
  if (branch_update > pref_update_percentage) and (branch_communication > pref_comm_percentage):
    print("Normal communication and update happening")
    new = agent2.arg_recency[random.randrange(0, len(agent2.arg_recency))]
    polarity = IsPosOrCon(new,0,knowledge_graph)
    polarity = int(polarity)
    print(f"Agent {agent2.id} with opinion {agent2.opinion} chose argument {new} which has polarity {polarity}\n")
    if (new in agent1.arg_recency):
        index_target = agent1.arg_recency.index(new)
        agent1.arg_recency.pop(index_target)
        agent1.arg_recency.append(new)
        print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
        return False
    else:
        agent1.arg_recency.pop(0)
        agent1.arg_recency.append(new)
        return True
  if (branch_communication <= pref_comm_percentage):
    # PREF COMMUNICATION ENABLED
    new = PrefArgument(agent2)
    # calculating on the global knowledge graph the polarity of argument new
    polarity = IsPosOrCon(new,0,knowledge_graph)
    polarity = int(polarity)
    print(f"Agent {agent2.id} with opinion {agent2.opinion} chose argument {new} which has polarity {polarity}\n")
    if (branch_update <= pref_update_percentage):
        # PREF COMMUNICATION ENABLED AND PREF UPDATE ENABLED
        print(f"Preferential Communication ENABLED and Preferential update ENABLED: \n\tbranch communication prob {branch_communication}% ---- pref communication prob {pref_comm_percentage}%\n\tbranch update prob {branch_update}% ---- pref update prob {pref_update_percentage}%")
        if(agent1.opinion == 0.5):
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                return True
            else:
                agent1.arg_recency.pop(0)
                agent1.arg_recency.append(new)
                print(f"Agent {agent1.id}: I am not CHOOSY [opinion {agent1.opinion}]: argument {new} accepted\n")
                return True
        if( ((polarity== 1) and (agent1.opinion > 0.5)) or ((polarity== -1) and (agent1.opinion < 0.5)) ):
            print(f"Agent {agent1.id}: We are brother! My opinion [{agent1.opinion}] agrees with argument {new}\n")
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                return False
            else:
                agent1.arg_recency.pop(0)
                agent1.arg_recency.append(new)
                return True
        else:
            print(f"Agent {agent1.id}: No way man! My opinion [{agent1.opinion}] disagrees with argument {new}\n")
            return False
    else:
        # PREF COMMUNICATION ENABLED AND PREF UPDATE DISABLED
        print(f"Preferential Communication ENABLED and Preferential update DISABLED: \n\tbranch communication prob {branch_communication}% ---- pref communication prob {pref_comm_percentage}%\n\tbranch update prob {branch_update}% ---- pref update prob {pref_update_percentage}%")
        if (new in agent1.arg_recency):
            index_target = agent1.arg_recency.index(new)
            agent1.arg_recency.pop(index_target)
            agent1.arg_recency.append(new)
            print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
            return False
        else:
            agent1.arg_recency.pop(0)
            agent1.arg_recency.append(new)
            return True
  else:
    # PREF COMMUNICATION DISABLED  
    new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
    # calculating on the global knowledge graph the polarity of argument x
    polarity = IsPosOrCon(new,0,knowledge_graph)
    polarity = int(polarity)
    print(f"Preferential Communication DISABLED (communication prob {branch_communication}% ---- pref communication prob {pref_comm_percentage})\n")
    print(f"Agent {agent2.id} with opinion {agent2.opinion} chose argument {new} which has polarity {polarity}\n")
    if (branch_update <= pref_update_percentage):
        # # PREF COMMUNICATION DISABLED  and # PREF UPDATE ENABLED
        print(f"Preferential Communication DISABLED and Preferential update ENABLED: \n\tbranch communication prob {branch_communication}% ---- pref communication prob {pref_update_percentage}%\n\tbranch update prob {branch_update}% ---- pref update prob {pref_update_percentage}%")
        if(agent1.opinion == 0.5):
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
                return True
            else:
                agent1.arg_recency.pop(0)
                agent1.arg_recency.append(new)
                print(f"Agent {agent1.id}: I am not CHOOSY [opinion {agent1.opinion}]: argument {new} accepted\n")
                return True            
        if( ((polarity== 1) and (agent1.opinion > 0.5)) or ((polarity== -1) and (agent1.opinion < 0.5)) ):
            print(f"Agent {agent1.id}: We are brother! My opinion [{agent1.opinion}] agrees with argument {new}\n")
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
                return False
            else:
                agent1.arg_recency.pop(0)
                agent1.arg_recency.append(new)
                return True
        else:
            print(f"Agent {agent1.id}: No way man! My opinion [{agent1.opinion}] disagrees with argument {new}\n")
            return False
  return False

def DiscussionPrefUpdate1(agent1, agent2):
  new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  polarity = IsPosOrCon(new,0,knowledge_graph)
  polarity = int(polarity)
  print(f"Argument chosen is {new} and its polarity is: {polarity}\n")
  if(agent1.opinion == 0.5):
    if (new in agent1.arg_recency):
      index_target = agent1.arg_recency.index(new)
      agent1.arg_recency.pop(index_target)
      agent1.arg_recency.append(new)
      return True
    else:
      agent1.arg_recency.pop(0)
      agent1.arg_recency.append(new)
      print(f"Agent {agent1.id}: I am not CHOOSY [opinion {agent1.opinion}]: argument {new} accepted\n")
      return True
  if( ((polarity== 1) and (agent1.opinion > 0.5)) or ((polarity== -1) and (agent1.opinion < 0.5)) ):
    print(f"We are brother! My opinion [{agent1.opinion}] agrees with argument {new}\n")
    if (new in agent1.arg_recency):
      index_target = agent1.arg_recency.index(new)
      agent1.arg_recency.pop(index_target)
      agent1.arg_recency.append(new)
      return False
    else:
      agent1.arg_recency.pop(0)
      agent1.arg_recency.append(new)
      return True
  else:
    print(f"No way man! My opinion [{agent1.opinion}] disagrees with argument {new}\n")
    return False

def DiscussionPrefComm3PrefUpdate3(agent1, agent2):
  branch_update = random.uniform(0, 1)
  branch_communication = random.uniform(0, 1)
  if (branch_update > pref_update3_percentage) and (branch_communication > pref_comm3_percentage):
    print("Normal communication and update happening")
    new = agent2.arg_recency[random.randrange(0, len(agent2.arg_recency))]
    polarity = IsPosOrCon(new,0,knowledge_graph)
    polarity = int(polarity)
    print(f"Agent {agent2.id} with opinion {agent2.opinion} chose argument {new} which has polarity {polarity}\n")
    if (new in agent1.arg_recency):
        index_target = agent1.arg_recency.index(new)
        agent1.arg_recency.pop(index_target)
        agent1.arg_recency.append(new)
        print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
        return False
    else:
        agent1.arg_recency.pop(0)
        agent1.arg_recency.append(new)
        return True
  if (branch_communication <= pref_comm3_percentage):
    # PREF COMMUNICATION 2 ENABLED
    new = PrefArgument2(agent2)
    # calculating on the global knowledge graph the polarity of argument new
    polarity = IsPosOrCon(new,0,knowledge_graph)
    polarity = int(polarity)
    print(f"Agent {agent2.id} with opinion {agent2.opinion} chose argument {new} which has polarity {polarity}\n")
    if (branch_update <= pref_update3_percentage):
        # PREF COMMUNICATION ENABLED AND PREF UPDATE ENABLED
        print(f"Preferential Communication 2 ENABLED and Preferential update 2 [aka Pref Discarding] ENABLED: \n\tbranch communication prob {branch_communication}% ---- pref communication prob {pref_comm3_percentage}%\n\tbranch update prob {branch_update}% ---- pref update prob {pref_update3_percentage}%")
        if(agent1.opinion == 0.5):
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                print(f"Agent {agent1.id} [opinion {agent1.opinion}] has already argument {new} so it is refreshing time\n")
                return True
            else:
                agent1.arg_recency.pop(0)
                agent1.arg_recency.append(new)
                print(f"Agent {agent1.id}: I am not CHOOSY [opinion {agent1.opinion}]: argument {new} accepted\n")
                return True
        if( ((polarity== 1) and (agent1.opinion > 0.5)) or ((polarity== -1) and (agent1.opinion < 0.5)) ):
            print(f"Agent {agent1.id}: We are brother! My opinion [{agent1.opinion}] agrees with argument {new}\n")
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                print(f"Agent {agent1.id} [opinion {agent1.opinion}] has already argument {new} so it is refreshing time\n")
                return False
            else:
                weakest_arg = FindTheWeakest(agent1)
                print(f"Agent {agent1.id}: removing argument {weakest_arg} cause it is the weakest and replacing with argument {new}\n")
                agent1.arg_recency.pop(agent1.arg_recency.index(weakest_arg))
                agent1.arg_recency.append(new)
                return True
        else:
            print(f"Agent {agent1.id}: No way man! My opinion [{agent1.opinion}] disagrees with argument {new}\n")
            return False
    else:
        # PREF COMMUNICATION ENABLED 2 AND PREF UPDATE DISABLED
        print(f"Preferential Communication 2 ENABLED and Preferential update 2 DISABLED: \n\tbranch communication prob {branch_communication}% ---- pref communication prob {pref_comm3_percentage}%\n\tbranch update prob {branch_update}% ---- pref update prob {pref_update3_percentage}%")
        if (new in agent1.arg_recency):
            index_target = agent1.arg_recency.index(new)
            agent1.arg_recency.pop(index_target)
            agent1.arg_recency.append(new)
            print(f"Agent {agent1.id} [opinion {agent1.opinion}] has already argument {new} so it is refreshing time\n")
            return False
        else:
            agent1.arg_recency.pop(0)
            agent1.arg_recency.append(new)
            return True
  else:
    # PREF COMMUNICATION DISABLED  
    new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
    # calculating on the global knowledge graph the polarity of argument x
    polarity = IsPosOrCon(new,0,knowledge_graph)
    polarity = int(polarity)
    print(f"Preferential Communication 2 DISABLED (communication prob {branch_communication}% ---- pref communication prob {pref_comm3_percentage})\n")
    print(f"Agent {agent2.id} with opinion {agent2.opinion} chose argument {new} which has polarity {polarity}\n")
    if (branch_update <= pref_update3_percentage):
        # # PREF COMMUNICATION DISABLED  and # PREF UPDATE ENABLED
        print(f"Preferential Communication 2 DISABLED and Preferential update 2 [aka Pref Discarding] ENABLED: \n\tbranch communication prob {branch_communication}% ---- pref communication prob {pref_comm3_percentage}%\n\tbranch update prob {branch_update}% ---- pref update prob {pref_update3_percentage}%")
        if(agent1.opinion == 0.5):
            print(f"Agent {agent1.id} is not aligned so it takes whatever it comes")
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
                return True
            else:
                agent1.arg_recency.pop(0)
                agent1.arg_recency.append(new)
                print(f"Agent {agent1.id}: I am not CHOOSY [opinion {agent1.opinion}]: argument {new} accepted\n")
                return True            
        if( ((polarity== 1) and (agent1.opinion > 0.5)) or ((polarity== -1) and (agent1.opinion < 0.5)) ):
            print(f"Agent {agent1.id}: We are brother! My opinion [{agent1.opinion}] agrees with argument {new}\n")
            if (new in agent1.arg_recency):
                index_target = agent1.arg_recency.index(new)
                agent1.arg_recency.pop(index_target)
                agent1.arg_recency.append(new)
                print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
                return False
            else:
                weakest_arg = FindTheWeakest(agent1)
                print(f"Agent {agent1.id}: removing argument {weakest_arg} cause it is the weakest and replacing with argument {new}\n")
                agent1.arg_recency.pop(arg_recency.index(weakest_arg))
                agent1.arg_recency.append(new)
                return True
        else:
            print(f"Agent {agent1.id}: No way man! My opinion [{agent1.opinion}] disagrees with argument {new}\n")
            return False
  return False


argument_set=[]

with open('A_nodi_scenario'+str(num_scenario)+'B.txt', "r", encoding='utf-8-sig' ) as f:
    nodes_read = f.readlines()

for x in nodes_read:
  x = x.split(",")
  argument_set.append(Argument(int(x[0]),float(x[1].strip())))
  print(x[0] + " " + x[1],end='') if verbose else None

edges=[]

with open('A_archi_scenario'+str(num_scenario)+'B.txt', "r", encoding='utf-8-sig' ) as f:
    archi = f.readlines()

for x in archi:
  x = x.split(",")

  edges.append([int(x[0]),int(x[1]),x[2].strip()])


knowledge_graph = nx.DiGraph()

for i in argument_set:
  knowledge_graph.add_node(i.id,value=i.value)

for i in edges:
  knowledge_graph.add_edge(i[0],i[1],polarity=int(i[2]))

print("Scenario number: "+str(num_scenario)+'\n',end='')
print("Number of nodes: ",end='')
print(knowledge_graph.number_of_nodes())
print("Number of edges: ",end='')
print(knowledge_graph.number_of_edges())
knowledge_graph.nodes.data()

# calculate from a knowledge graph the polarity of an argument: there must be a path from source_arg to target_arg/topic
def IsPosOrCon(source_arg, target_arg, knowledge_graph):
  polarity_list = []
  if nx.has_path(knowledge_graph, source_arg, target_arg):
    
    sp = nx.shortest_path(knowledge_graph, source=source_arg, target=target_arg, weight='polarity')
    # Create a graph from 'sp'
    pathGraph = nx.path_graph(sp)  # does not pass edges attributes

    # Read attributes from each edge
    for ea in pathGraph.edges():
        #print from_node, to_node, edge's attributes
        print(ea, knowledge_graph.edges[ea[0], ea[1]]) if verbose else None
        aux = knowledge_graph.edges[ea[0], ea[1]]
        polarity_list.append(aux["polarity"])
    polarity = numpy.prod(polarity_list)
    # to avoid precision issues
    polarity = int(polarity)
  else:
    # no path from source argument to target argument ==> w(a)
    polarity=0
 
  return(polarity)

def CalculateArgumentStrenght(arg_id, agent_knowledge_graph):
  all_nodes = agent_knowledge_graph.nodes.data()
  all_edges = agent_knowledge_graph.edges.data()
  arg_values = []
  node_ancestor = []
  strenght = -1

  # sanitize
  if isinstance(arg_id, list):
    arg_id = int(arg_id[0])

  print("Node " + str(arg_id) + " degree: " + str(agent_knowledge_graph.degree(arg_id))) if verbose else None

  if(agent_knowledge_graph.degree(arg_id) == 0):
    # isolated node
    print("Isolated node: " + str(arg_id) +" with value " + str(all_nodes[arg_id]['value']) ) if verbose else None
    strenght = round(strenght,3)
    return(all_nodes[arg_id]['value'])
  elif (agent_knowledge_graph.degree(arg_id) == 1):
    # it has one edge: try to decide if in or out
    if(agent_knowledge_graph.out_degree(arg_id) == 1):
      # it is a leaf because it has got only exiting edges
      print("Leaf with only exiting: " + str(arg_id) +" with value " +  str(all_nodes[arg_id]['value']) ) if verbose else None
      strenght = round(strenght,3)
      return(all_nodes[arg_id]['value'])
    else:
      # it is a "root" beacuse has got 1 incoming edge
      node_all_edges = agent_knowledge_graph.in_edges(arg_id)
      node_all_edges = list(node_all_edges)
      node_ancestor.append(node_all_edges[0][0])
      polarity = IsPosOrCon(node_all_edges[0][0],arg_id,agent_knowledge_graph)
      print("Node ancestor is: " + str(node_ancestor) + " with polarity " + str(polarity)) if verbose else None
      ancestor_strenght = polarity * CalculateArgumentStrenght(node_ancestor, agent_knowledge_graph)
      print("Ancestor strenght is: " + str(ancestor_strenght)) if verbose else None
      print("Resiliency is: " + str(p1*all_nodes[arg_id]['value'])) if verbose else None
      print("Changement is: " + str((p2*((1+(ancestor_strenght/len(node_ancestor)))/2)))) if verbose else None
      
      strenght = (p1*all_nodes[arg_id]['value'])+ (p2*((1+(ancestor_strenght/len(node_ancestor)))/2))
      print("Root [it is just an edge away from topic]: " + str(arg_id)+ " with strenght " + str(strenght) ) if verbose else None
      strenght = round(strenght,3)
      return(strenght)
  elif ((agent_knowledge_graph.degree(arg_id) == 2) and (agent_knowledge_graph.out_degree(arg_id) == 1) and (agent_knowledge_graph.in_degree(arg_id) == 1)):
    # node with one incoming and one exiting edge
    node_all_edges = agent_knowledge_graph.in_edges(arg_id)
    node_all_edges = list(node_all_edges)
    node_ancestor.append(node_all_edges[0][0])
    polarity = IsPosOrCon(node_all_edges[0][0],arg_id,agent_knowledge_graph)
    ancestor_strenght = polarity * CalculateArgumentStrenght(node_ancestor, agent_knowledge_graph)
    strenght = (p1*all_nodes[arg_id]['value'])+ (p2*((1+(ancestor_strenght/len(node_ancestor)))/2))
    print("Node with one incoming and one exiting edge: " + str(strenght) ) if verbose else None
    strenght = round(strenght,3)
    return(strenght)

# calculates opinion of agent 
def CalculateOpinion(agent_arg_indexes, agent_knowledge_graph, agent_opinion):
  
  # this is a dictionary
  arg_values = {}
  opinion = -1
  old_opinion = agent_opinion

  # cycle for calculating arguments strenght values relative to subjective knowledge graph
  for x in agent_arg_indexes:
    # calculating on the global knowledge graph the polarity of argument x
    polarity = IsPosOrCon(x,0,knowledge_graph)
    polarity = int(polarity)
    print("Calculating strenght of argument " + str(x)) if verbose else None
    arg_values[x] = polarity * CalculateArgumentStrenght(x, agent_knowledge_graph)
    arg_values[x] = round(arg_values[x],2)
  
  print("Calculated values for agent's args are: " + str(arg_values)) if log else None
  sum_ancestors = 0

  for key in arg_values:
    sum_ancestors = sum_ancestors + arg_values[key]
    print(sum_ancestors) if verbose else None

  print("Sum of ancestors: " + str(sum_ancestors)) if verbose else None
  f_a = (1+(sum_ancestors/len(arg_values)))/2
  opinion = (p1*old_opinion)+ (p2*f_a)
  #return a round opinion to 2 decimal
  return round(opinion,opinion_precision)

def IsPerfectConsensus(agents_list, S):
    arguments_remained = []
    for x in agents:
        arguments_remained = arguments_remained + x.arg_recency
    arguments_remained = sorted(set(arguments_remained))
    print("Arguments remained are:" + str(arguments_remained)) if log else None
    if(len(arguments_remained) < ((2*S)-1)):
        ###OLD CONDITION perfect consensun reached i.e. arguments remained is equal to S cardinality
        # perfect consensun reached i.e. arguments remained is less than 2S - 1 cardinality
        return True
    else:
        return False

def RemainingArguments(agents):
    arguments_remained = []
    for x in agents:
        arguments_remained = arguments_remained + x.arg_recency
    arguments_remained = sorted(set(arguments_remained))
    return arguments_remained
    
def AverageOpinion(agents):
    average_opinion = []
    for x in agents:
        average_opinion.append(x.opinion)
    average_opinion = sum(average_opinion) / len(average_opinion)
    return average_opinion

#### TRYING TO INITIALIZE########
all_arg_indexes = list(range(1,argomenti_totali+1))
print(all_arg_indexes) if verbose else None
all_nodes = knowledge_graph.nodes.data()
print("------------- STARTING GRAPH -----------------")
print(all_nodes)
print("------------- --------- -----------------")

def Similarity(agent1,agent2):
  return(1 - abs(agent1.opinion - agent2.opinion))

def Probability(similarity_list,speaker_index,target):
  numeratore = similarity_list[target]**h
  denominatore = []
  print("Candidato: " + str(target)) if verbose else None
  for i,x in enumerate(similarity_list):
    if ((i != speaker_index)):
      denominatore.append(x**h)
  denominatore = sum(denominatore)
  result = numeratore/denominatore
  print("Numeratore " + str(numeratore) + " Denominatore " + str(denominatore)) if verbose else None
  print("Probabilità di: " + str(target) + " " + str(numeratore/denominatore) +" "+ str(result)) if verbose else None
  print("##########") if verbose else None
  return(result)

def DiscussionPrefDiscarding(agent1, agent2):
  new = agent2.arg_recency[random.randrange(0, len(agent1.arg_recency))]
  print("Speaker Agent " + str(agent1.id) + " arguments "+ str(agent1.arg_recency) +"\n") #if log else None
  print("Chosen Agent " + str(agent2.id) + " arguments "+ str(agent2.arg_recency) +"\n") #if log else None
  print("Agent " + str(agent2.id) + " is passing argument "+ str(new)+" to agent "+ str(agent1.id) +"\n") #if log else None
  if (new in agent1.arg_recency):
    index_target = agent1.arg_recency.index(new)
    agent1.arg_recency.pop(index_target)
    agent1.arg_recency.append(new)
    print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
    print("Speaker Agent " + str(agent1.id) + " arguments "+ str(agent1.arg_recency) +"\n") #if log else None
    print("Chosen Agent " + str(agent2.id) + " arguments "+ str(agent2.arg_recency) +"\n") #if log else None
    print("################################\n") #if log else None
    return False
  else:
    arg_values = {}
    print("Checking if argument " + str(new) + ", sent by chosen, is good\n") #if log else None
    
    arg_list = agent1.arg_recency
    arg_list.append(new)
    agent_knowledge_graph = knowledge_graph.subgraph(arg_list).copy()

	# cycle for calculating arguments strenght values relative to subjective knowledge graph
    for x in arg_list:

        arg_values[x] = CalculateArgumentStrenght(x, agent_knowledge_graph)
        arg_values[x] = round(arg_values[x],2)
        print("Strenght of argument " + str(x) +" is " + str(arg_values[x])) #if log else None    
    print ("List of arguments strenght " + str(arg_values))
    arg_to_remove = min(arg_values, key=arg_values.get)
    print ("Removing argument " + str(arg_to_remove) + " because is the weakest and oldest")
    agent1.arg_recency.remove(arg_to_remove)
    print("Speaker Agent " + str(agent1.id) + " arguments "+ str(agent1.arg_recency) +"\n") #if log else None
    print("Chosen Agent " + str(agent2.id) + " arguments "+ str(agent2.arg_recency) +"\n") #if log else None
    print("################################\n") #if log else None
    return True

def DiscussionPrefComm2PrefUpdate2(agent1, agent2):
  print(f"Speaker Agent {agent1.id} arguments {agent1.arg_recency}\n") #if log else None
  print(f"Chosen Agent {agent2.id} arguments {agent2.arg_recency}\n") #if log else None
  new = OneOfStrongest(agent2)
  print("Agent " + str(agent2.id) + " is passing argument "+ str(new)+" to agent "+ str(agent1.id) +"\n") #if log else None
  if (new in agent1.arg_recency):
    index_target = agent1.arg_recency.index(new)
    agent1.arg_recency.pop(index_target)
    agent1.arg_recency.append(new)
    print("Agent " + str(agent1.id) + " has already argument "+ str(new)+" so it is refreshing time\n") #if log else None
    print("Speaker Agent " + str(agent1.id) + " arguments "+ str(agent1.arg_recency) +"\n") #if log else None
    print("Chosen Agent " + str(agent2.id) + " arguments "+ str(agent2.arg_recency) +"\n") #if log else None
    print("################################\n") #if log else None
    return False
  else:
    # this is a dictionary
    arg_values = {}
    print("Checking if argument " + str(new) + ", sent by chosen, is good\n") #if log else None
    arg_list = agent1.arg_recency
    arg_list.append(new)
    agent_knowledge_graph = knowledge_graph.subgraph(arg_list).copy()
	# cycle for calculating arguments strenght values relative to subjective knowledge graph
    for x in arg_list:
        arg_values[x] = CalculateArgumentStrenght(x, agent_knowledge_graph)
        arg_values[x] = round(arg_values[x],2)
        print("Strenght of argument " + str(x) +" is " + str(arg_values[x])) #if log else None    
    print ("List of arguments strenght " + str(arg_values))
    arg_to_remove = min(arg_values, key=arg_values.get)
    print ("Removing argument " + str(arg_to_remove) + " because is the weakest and oldest")
    agent1.arg_recency.remove(arg_to_remove)
    print("Speaker Agent " + str(agent1.id) + " arguments "+ str(agent1.arg_recency) +"\n") #if log else None
    print("Chosen Agent " + str(agent2.id) + " arguments "+ str(agent2.arg_recency) +"\n") #if log else None
    print("################################\n") #if log else None
    return True	
	
agents=[]


for i in range(int(popolazione)):
	#returns a number between 0 (included) and S+1 (not included)
    configuration=random.randrange(0, S+1)
    print(f"Configurazione scelta per {i}: {configuration}")
    agents.append(Agent(i, MemoriaCasualeSpecifica(argument_set,configuration,(S - configuration)),0.5))
    agent_graph_aux = knowledge_graph.subgraph(agents[i].arg_recency).copy()
    agents[i].opinion = CalculateOpinion(agents[i].arg_recency, agent_graph_aux,agents[i].opinion)
    agents[i].print()
    del agent_graph_aux



opinion_axis = []

# saving for each epoch the opinion of each agent
# world_opinion will be of 100 lenght because opinion is set to be two decimal values
def World_Opinion_Calculate():
  for x in agents:
    world_opinion[x.opinion] = world_opinion[x.opinion] + 1
  return world_opinion.values()

# starting instant scenario
# initializing opinion_axis with starting opinion
world_opinion = dict.fromkeys(world_opinion, 0)
opinion_axis.append(World_Opinion_Calculate())
# resetting all keys to zero
world_opinion = dict.fromkeys(world_opinion, 0)
print(f"Starting opinion of epoch 1: \n{opinion_axis}")

print("Dawn of ages ---- epoch 0 ----")
for d in range(int(popolazione)):
	agents[d].print()


file_globale = "totale_run.txt"
g = open(file_globale, "a", encoding='utf-8-sig' )

# starting experiments for epochs
num_epoch = 0

# directory for temporary file
tempfile.tempdir = "./"

# open file of epoch here so no RAM problem with opinion held in memoryview
f = tempfile.NamedTemporaryFile(mode='w+t', prefix="epoch_temp_",delete=False)
print(f"\nCreated temp file: {f.name}\n") # if verbose else None

# open file of arguments evolotion through epochs 
f_args = tempfile.NamedTemporaryFile(mode='w+t', prefix="args_evolution_temp_",delete=False)
print(f"Created temp file: {f_args.name}\n") # if verbose else None

#for x in range(epochs):
while not(stop):
  print("-------------------------------------------------------------------------") if log else None
  print(f"----------------------EPOCH NUMBER {num_epoch}---------------------------------") if log else None
  print("-------------------------------------------------------------------------") if log else None
  speaker_index = random.randrange(0, len(agents))
  print(f"Speaker is {speaker_index}") if log else None
  chosen_index = -1
  similarity_list = []
  probability_list = []
  remaining_arguments = []
  average_opinion = 0
  topic_opinion = -1
  opinion_graph = nx.DiGraph()
  for i in range(popolazione):
    if i != speaker_index:
      sim = Similarity(agents[speaker_index],agents[i])
      similarity_list.append(sim)
    else:
      similarity_list.append(-1)
  print(f"SIMILARITY FOR {speaker_index}") if log else None
  print(similarity_list) if log else None

  for i in range(popolazione):
    if i != speaker_index:
      prob = Probability(similarity_list,speaker_index,i)
      probability_list.append(prob)
    else:
      probability_list.append(-1)

  print(f"PROBABILITY FOR {speaker_index}") if log else None
  # set probability to speak with myself to zero
  probability_list [speaker_index] = 0
  print(probability_list) if log else None
  print(f"Prob sum: {sum(probability_list)}") if verbose else None
  chosen_index = random.choices(population=range(popolazione),weights=probability_list,k=1)
  # chosen_index is a list, but we set K=1 so it is only one value. we set that value to int
  chosen_index = chosen_index[0]
  print(f"Args for {speaker_index}: {agents[speaker_index].arg_recency}" ) if log else None
  print(f"Args for {chosen_index}: {agents[chosen_index].arg_recency}" ) if log else None
  print(type(chosen_index)) if verbose else None

  ######################################################################################
  # Be carefull: you have to change this part to change communication and update methods
  ######################################################################################

  #DiscussionRep3(agents[speaker_index], agents[chosen_index])
  
  # preferential discarding
  #DiscussionPrefDiscarding(agents[speaker_index], agents[chosen_index])
  
  # preferential update 1
  # branch = random.uniform(0, 1)
  # if(branch<= pref_update_percentage):
      # print(f"Preferential update ENABLED: branch prob {branch}% ---- pref update prob {pref_update_percentage}%")
      # DiscussionPrefUpdate1(agents[speaker_index], agents[chosen_index])
  # else:
      # print("Normal communication happening")
      # DiscussionRep3(agents[speaker_index], agents[chosen_index])
	  
  # Preferential Communication 1 and Preferential Update 1 ---- PUO e PCO 
  DiscussionPrefComm1PrefUpdate1(agents[speaker_index], agents[chosen_index])
  
  # Preferential Communication 2 and Preferential Update 2 --- non preso in considerazione
  #DiscussionPrefComm2PrefUpdate2(agents[speaker_index], agents[chosen_index])
  
  # Vigilant Update 
  #VigilantUpdate(agents[speaker_index], agents[chosen_index],VU_pros)

  # Vigilant Update Pref Update
  #VigilantUpdatePrefUpdate2(agents[speaker_index], agents[chosen_index],VU_pros)

  agent_graph = knowledge_graph.subgraph(agents[speaker_index].arg_recency).copy()
  print("Speaker agent is " + str(speaker_index) + " with opinion " + str(agents[speaker_index].opinion)) if log else None
  agents[speaker_index].opinion = CalculateOpinion(agents[speaker_index].arg_recency, agent_graph,agents[speaker_index].opinion)
  print("Speaker agent " + str(speaker_index) + " new opinion is " + str(agents[speaker_index].opinion) + " with arguments: " + str(agents[speaker_index].arg_recency)) if log else None
  print("Chosen (sender) agent is " + str(chosen_index) + " with opinion " + str(agents[chosen_index].opinion)) if log else None
  print("Chosen (sender) " + str(chosen_index) + " has these arguments: " + str(agents[chosen_index].arg_recency)) if log else None
  
  f.writelines(str(list(World_Opinion_Calculate())))
  f.writelines("\n")
  f_args.writelines(str(RemainingArguments(agents)))
  f_args.writelines("\n")
  # check if we must stop
  all_except_extremist = list(world_opinion.values())
  negative_ones = int(all_except_extremist[0])
  positive_ones = int(all_except_extremist[-1])
  print(f"DISTRIBUTION FOR ALL_: {all_except_extremist}") if log else None
  all_except_extremist = all_except_extremist[1:(len(world_opinion)-1)]
  print(f"ALL_EXCEPT_EXTREMIST: {all_except_extremist}") if verbose else None
  # printing new list of agents
  for d in range(int(popolazione)):
    agents[d].print() if log else None
  if(sum(all_except_extremist) == 0 and ( ( negative_ones != int(popolazione) ) and ( positive_ones != int(popolazione) )) ):
    # bipolarization happens!
    stop = True
    remaining_arguments = RemainingArguments(agents)
    average_opinion = AverageOpinion(agents)
    opinion_graph = knowledge_graph.subgraph(remaining_arguments).copy()
    topic_opinion = CalculateOpinion(remaining_arguments, opinion_graph,0)
    print(f"BIPOLARIZATION REACHED:\t epoch number {num_epoch}\t--- CONS cardinality {world_opinion[0.0]}\tPROS cardinality {world_opinion[1.0]}\t Remaining arguments {remaining_arguments}\t AVG Opinion {average_opinion} Topic Opinion {topic_opinion}")
    g.write(f"{num_run}\tBIPOLARIZATION REACHED\tepoch number\t{num_epoch}\tRemaining arguments\t{remaining_arguments}\tAVG Opinion\t{average_opinion}\tTopic Opinion\t{topic_opinion}\tCONS cardinality\t{world_opinion[0.0]}\tPROS cardinality\t{world_opinion[1.0]}")
    g.write("\n")
  if(IsPerfectConsensus(agents,S)):
    # perfect consensus
    stop = True
    remaining_arguments = RemainingArguments(agents)
    average_opinion = AverageOpinion(agents)
    opinion_graph = knowledge_graph.subgraph(remaining_arguments).copy()
    topic_opinion = CalculateOpinion(remaining_arguments, opinion_graph,0)
    print(f"PERFECT CONSENSUS REACHED:\tepoch number {num_epoch}\t Remaining arguments {remaining_arguments}\t AVG Opinion {average_opinion} Topic Opinion {topic_opinion}")
    g.write(f"{num_run}\tPERFECT CONSENSUS REACHED\tepoch number\t{num_epoch}\tRemaining arguments\t{remaining_arguments}\tAVG Opinion\t{average_opinion}\tTopic Opinion\t{topic_opinion}")
    g.write("\n")
	
  if(num_epoch == 6000000):
    stop = True
    # end of times
    remaining_arguments = RemainingArguments(agents)
    average_opinion = AverageOpinion(agents)
    opinion_graph = knowledge_graph.subgraph(remaining_arguments).copy()
    topic_opinion = CalculateOpinion(remaining_arguments, opinion_graph,0)
    print(f"END OF TIMES REACHED:\tepoch number {num_epoch}\t Remaining arguments {remaining_arguments}\t AVG Opinion {average_opinion} Topic Opinion {topic_opinion}")
    g.write(f"{num_run}\tEND OF TIMES REACHED\tepoch number\t{num_epoch}\tRemaining arguments\t{remaining_arguments}\tAVG Opinion\t{average_opinion}\tTopic Opinion\t{topic_opinion}\t SITUATION:\t{str(list(World_Opinion_Calculate()))}")
    g.write("\n")

  # reset world_opinion keys to zeros
  world_opinion = dict.fromkeys(world_opinion, 0)
  num_epoch = num_epoch + 1

file_epoche= 'A_epoche_scenario'+str(num_scenario)+'_'+str(popolazione)+'agenti_run_'+num_run+'_S'+str(S)+'_epoch_' + str(num_epoch) + '_.txt'
file_args= 'A_args_through_epochs_scenario'+str(num_scenario)+'_'+str(popolazione)+'agenti_run_'+num_run+'_S'+str(S)+'_epoch_' + str(num_epoch) + '_.txt'

g.close()
f.close()
f_args.close()

os.rename(f.name, file_epoche)
os.rename(f_args.name, file_args)

print(f"\nCreated file: {file_epoche}\n")  if verbose else None

print("The end of time\n")
for x in agents:
  x.print() #if log else None