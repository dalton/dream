from copy import copy, deepcopy
import json
import time
import random
import operator
import datetime

from dream.plugins import plugin

class CreateCapacityStations(plugin.InputPreparationPlugin):
    """ Input preparation 
        creates the CapacityStationBuffer and CapacityStationExit for each CapacityStation
    """

    def preprocess(self, data):
        nodes=copy(data['graph']['node'])
        originalData=deepcopy(data)
        for (stationId, node) in nodes.iteritems():
            _class=node['_class']
            if _class=='dream.simulation.applications.CapacityStations.CapacityStation.CapacityStation':
                nextCapacityStationBufferId=self.getNextCapacityStationBufferId(data,stationId)  
                # the nextCapacityStationBufferId should point to the buffer  
                if nextCapacityStationBufferId:
                    nextCapacityStationBufferId+='_B'            
                stationName=node['name']
                # create the CapacityStationBuffer
                bufferName=stationName+'_Buffer'
                bufferId=stationId+'_B'
                requireFullProject=data['graph']['node'][stationId].pop('requireFullProject',None)
                data['graph']['node'][bufferId]={
                    "_class": "dream.simulation.applications.CapacityStations.CapacityStationBuffer.CapacityStationBuffer", 
                    "name": bufferName, 
                    "wip": [],
                    'requireFullProject':requireFullProject
                }
                if requireFullProject:
                    data['graph']['node'][bufferId]['notRequiredOperations']=self.findNotRequiredOperations(originalData,stationId)                

                # create an edge that connects the CapacityStationBuffer to the CapacityStation
                data['graph']['edge'][bufferId+'_to_'+stationId]={
                    "source": bufferId, 
                    "destination": stationId, 
                    "data": {}, 
                    "_class": "Dream.Edge"
                }
                # create the CapacityStationExit
                exitName=stationName+'_Exit'
                exitId=stationId+'_E'

                data['graph']['node'][exitId]={
                    "_class": "dream.simulation.applications.CapacityStations.CapacityStationExit.CapacityStationExit", 
                    "name": exitName, 
                    "nextCapacityStationBufferId": nextCapacityStationBufferId
                }
                # create an edge that connects the CapacityStationBuffer to the CapacityStation
                data['graph']['edge'][stationId+'_to_'+exitId]={
                    "source": stationId, 
                    "destination": exitId, 
                    "data": {}, 
                    "_class": "Dream.Edge"
                }                    
                        
                # XXX another patch, these should be inputted
                if stationId=='PPASB':
                    data['graph']['node'][stationId]['sharedResources']={ 
                         "stationIds": ["ASBTST"], 
                         "priority": 3
                         }
                    data['graph']['node'][stationId]['notProcessOutsideThreshold']=1
                if stationId=='ASBTST':
                    data['graph']['node'][stationId]['sharedResources']={ 
                         "stationIds": ["PPASB"], 
                         "priority": 2
                         }
                    data['graph']['node'][stationId]['notProcessOutsideThreshold']=1
                
        # add also a CapacityStationController
        # XXX some of the attributes should be inputted by the user 
        data['graph']['node']['CSC']={
            "dueDateThreshold": 14, 
            "name": "CSC", 
            "prioritizeIfCanFinish": 1, 
            "interval": "1", 
            "start": "0", 
            "interruptions": {}, 
            "_class": "dream.simulation.applications.CapacityStations.CapacityStationController.CapacityStationController"
         }
        return data
    
    # gets the data and the stationId
    # returns the successorId and erases the edge
    def getNextCapacityStationBufferId(self,data,stationId):
        successorId=None
        edgeToErase=None
        for (edgeId, edge) in data['graph']['edge'].iteritems():
            if data['graph']['edge'][edgeId]['source']==stationId:
                successorId=data['graph']['edge'][edgeId]['destination']   
                edgeToErase=edgeId
                break
        if edgeToErase:
            data['graph']['edge'].pop(edgeToErase,None)
        return successorId
    
    # for an assembly station finds which are the not required operations
    def findNotRequiredOperations(self,data,stationId):
        requiredOperations=[]
        nodes=data['graph']['node']
        notRequiredOperations=nodes.keys()
        for node_id, node in nodes.iteritems():
            currentId=node_id
            while 1:
                successorList = self.getSuccessors(data, currentId)
                if not successorList:
                    break
                successorId=successorList[0]
                if successorId==stationId:
                    requiredOperations.append(node_id)
                    break
                currentId=successorId
        for element in deepcopy(notRequiredOperations):
            if element in requiredOperations:
                notRequiredOperations.remove(element)
        return notRequiredOperations
        



