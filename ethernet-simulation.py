import simpy
import math
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys


# First  define some global variables. You should change values
class G:
    RANDOM_SEED = 33
    SIM_TIME =100000   
    SLOT_TIME = 1
    LONG_SLEEP_TIMER = 1000000000

    #these are the default values for parameters
    N = 30
    ARRIVAL_RATES = [0.001, 0.002, 0.004, 0.008, 0.012,0.016,0.02,0.024,0.028]  
    RETRANMISSION_POLICIES = ["pp", "op", "beb", "lb"]
    
    #If the user passes input, reset the parameters
    if(len(sys.argv)!=1):
        ARRIVAL_RATES = [float(sys.argv[3])]
        N = int(sys.argv[1])
        RETRANMISSION_POLICIES=[sys.argv[2]]

        
class Server_Process(object):
    def __init__(self, env, dictionary_of_nodes, retran_policy):
        self.env = env
        self.dictionary_of_nodes = dictionary_of_nodes 
        self.retran_policy = retran_policy 
       # self.slot_stat = slot_stat
        self.current_slot = 1
        self.action = env.process(self.run())    

        #These variales keep track of the number of times a slot was succesful, idle, or collision had occured.
        self.sucess_count=0
        self.collision_count=0
        self.idle_count=0
    def run(self):
        #print("Server process started")
        
        while True: 
            # sleep for slot time
            yield self.env.timeout(G.SLOT_TIME)
            
            #stores the indexes of the active nodes in a slot 
            active_nodes_index=[]

            #code for finding all the active nodes in the slot
            for node_number in range(1,len(self.dictionary_of_nodes)):
                if(self.dictionary_of_nodes[node_number].next_slot_number==self.current_slot):
                    active_nodes_index.append(node_number)
           
           

            if(self.retran_policy=="pp"): #retransmission policy pp
                
                                
                if(len(active_nodes_index)>1): #there is a collision(retransmission)
                    self.collision_count+=1
                    for index_number in active_nodes_index:
                        self.dictionary_of_nodes[index_number].next_slot_number = self.current_slot+ np.random.geometric(0.5)
                
                elif(len(active_nodes_index)==1): #success
                
                    self.sucess_count+=1
                    self.dictionary_of_nodes[active_nodes_index[0]].packet_number-=1
                    
                    if(self.dictionary_of_nodes[active_nodes_index[0]].packet_number!=0):
                        self.dictionary_of_nodes[active_nodes_index[0]].next_slot_number=self.current_slot+1
                
                else: #idle
                    self.idle_count+=1
                self.current_slot+=1                             
            
            elif(self.retran_policy=="op"):#retransmission policy op
                                
                if(len(active_nodes_index)>1): #there is a collision
                    self.collision_count+=1
                    for index_number in active_nodes_index:
                        self.dictionary_of_nodes[index_number].next_slot_number = self.current_slot+ np.random.geometric(1/G.N)
                elif(len(active_nodes_index)==1): #sucess
                    self.sucess_count+=1
                    self.dictionary_of_nodes[active_nodes_index[0]].packet_number-=1
                    
                    if(self.dictionary_of_nodes[active_nodes_index[0]].packet_number!=0):
                        self.dictionary_of_nodes[active_nodes_index[0]].next_slot_number=self.current_slot+1
                else: #idle
                    self.idle_count+=1
                self.current_slot+=1
            
            elif(self.retran_policy=="lb"): #retransmission policy lb
                if(len(active_nodes_index)>1): #there is a collision(set retransmission slot numbers, increase retransmission attempts for packet, and check if retransmitted in same slot)
                    self.collision_count+=1
                    for index_number in active_nodes_index:
                        self.dictionary_of_nodes[index_number].next_slot_number = self.current_slot + np.random.randint(min(self.dictionary_of_nodes[index_number].retransmission_attempts,1024)+1)+1
                        self.dictionary_of_nodes[index_number].retransmission_attempts += 1
                elif(len(active_nodes_index)==1): #sucess
                    self.sucess_count+=1
                    self.dictionary_of_nodes[active_nodes_index[0]].packet_number -= 1
                                        
                    if(self.dictionary_of_nodes[active_nodes_index[0]].packet_number!=0):
                        self.dictionary_of_nodes[active_nodes_index[0]].next_slot_number = self.current_slot+1
                        self.dictionary_of_nodes[active_nodes_index[0]].retransmission_attempts=1
                else: #idle
                    self.idle_count+=1
                self.current_slot+=1
            
            else: #retransmission policy beb
                        
                if(len(active_nodes_index)>1): #there is a collision(set retransmission slot numbers, increase retransmission attempts for packet, and check if retransmitted in same slot)
                    self.collision_count+=1
                    for index_number in active_nodes_index:
                        self.dictionary_of_nodes[index_number].next_slot_number = self.current_slot + np.random.randint(pow(2,min(self.dictionary_of_nodes[index_number].retransmission_attempts,10))+1)+1
                        self.dictionary_of_nodes[index_number].retransmission_attempts += 1
                elif(len(active_nodes_index)==1): #sucess
                    self.sucess_count+=1
                    self.dictionary_of_nodes[active_nodes_index[0]].packet_number -=1
                    if(self.dictionary_of_nodes[active_nodes_index[0]].packet_number!=0):
                        self.dictionary_of_nodes[active_nodes_index[0]].next_slot_number = self.current_slot+1
                        self.dictionary_of_nodes[active_nodes_index[0]].retransmission_attempts=1
                else: #idle
                    self.idle_count+=1
                self.current_slot+=1


                    
        
class Node_Process(object): 
    def __init__(self, env, id, arrival_rate):
        
        self.env = env
        self.id = id
        self.arrival_rate = arrival_rate
        
        #total number of packets in the node
        self.packet_number=0
        #the slot number the node will transmit next
        self.next_slot_number=0
        #the number of times a retransmission was attempted for the head packet of the node
        self.retransmission_attempts=1
        
        # Other state variables
        
        self.action = env.process(self.run())
        

    def run(self):
        
        while True:
             # Infinite loop for generating packets
            yield self.env.timeout(random.expovariate(self.arrival_rate))
            
            # packet arrivals 
         #   print("Arrival Process Started:", self.id)
            
            if(self.packet_number==0): #packet is the first arrival in an empty node
                self.next_slot_number=math.ceil(self.env.now) 
                
            self.packet_number += 1
        
        



def main():
    print("Simiulation Analysis of Random Access Protocols")
    random.seed(G.RANDOM_SEED)
    #lists to hold the throughputs for each transmission policy(used for plotting) 
    throughputList_pp=[]
    throughputList_op=[]
    throughputList_lb=[]
    throughputList_beb=[]
    retran=G.RETRANMISSION_POLICIES

    for retran_policy in retran:
        for arrival_rate in G.ARRIVAL_RATES:#for each of the arrival rates  
            env = simpy.Environment()
       #     slot_stat = StatObject()
            dictionary_of_nodes  = {} 

            for i in list(range(1,G.N+1)):
                node = Node_Process(env, i, arrival_rate)
                dictionary_of_nodes[i] = node


            server_process = Server_Process(env, dictionary_of_nodes,retran_policy)
            env.run(until=G.SIM_TIME)

            # code to determine throughput and append to its respective list
            throughput=(server_process.sucess_count)/(server_process.current_slot)
            if(retran_policy=="pp"):
                throughputList_pp.append(throughput)
            elif(retran_policy=="op"):
                throughputList_op.append(throughput)
            elif(retran_policy=="lb"):
                throughputList_lb.append(throughput)
            else:
                throughputList_beb.append(throughput)
            if(len(sys.argv)!=1):
                format_float = "{:.2f}".format(throughput)
                print(format_float)
                
    # code to plot 
    if(len(sys.argv)==1):
        Lamda_times_N=[0.03, 0.06, 0.12, 0.24, 0.36,0.48,0.6,0.72,0.84]
        plt.plot(Lamda_times_N,throughputList_pp)
        plt.plot(Lamda_times_N,throughputList_op)
        plt.plot(Lamda_times_N,throughputList_beb)
        plt.plot(Lamda_times_N,throughputList_lb)
        plt.xlabel('Offered Load (Lamda * N)')
        plt.ylabel('Achieved Throughput')
        blue_patch = mpatches.Patch(color='blue', label='pp')
        orange_patch = mpatches.Patch(color='orange', label='op')
        green_patch = mpatches.Patch(color='green', label='beb')
        red_patch = mpatches.Patch(color='red', label='lb')
        plt.legend(handles=[blue_patch,orange_patch,green_patch,red_patch])


        plt.show()
    
if __name__ == '__main__': main()
