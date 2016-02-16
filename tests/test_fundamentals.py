import pytimber
from datetime import datetime, timedelta

log = pytimber.LoggingDB(source='all')

now = datetime.now()
fundamental = 'CPS:%:SFTPRO%'
log.get('CPS.TGM:USER%', now - timedelta(minutes = 10), now, fundamental)
