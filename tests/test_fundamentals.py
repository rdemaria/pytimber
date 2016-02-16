import pytimber
from datetime import datetime, timedelta

log = pytimber.LoggingDB(source='all')

now = datetime.now()
fundamental = 'CPS:TOF**:TOF'
log.get('CPS:TGM%', now, now + timedelta(hours = -1), fundamental)
