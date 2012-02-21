'''
Tool for creating JSON Object for usage in Timemap display.
'''
from abc import abstractmethod, ABCMeta

from georgia_lynchings.events.models import get_metadata

class Mapdata(object):
    '''The abstract class for creating json data for map display.
    :meth:`format` method should be overridden in the subclass.
    '''

    #This allows methods to be marked as abstract
    __metaclass__ = ABCMeta

    def get_json(self):
        '''Get json object for map display.
        '''
        return self.format(get_metadata())
        
    @abstractmethod
    def format(self, metadata):
        '''Format the metadata results into a json structure for map display.
        **This method must be implemented in the subclass**
        '''
