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

    def get_json(self, add_fields=[]):
        '''Get json object for map display.
        
            :param add_fields: add extra fields to the core metadata.        
        '''
        return self.format(get_metadata(add_fields))
        
    @abstractmethod
    def format(self, metadata):
        '''Format the metadata results into a json structure for map display.
        **This method must be implemented in the subclass**
        '''
