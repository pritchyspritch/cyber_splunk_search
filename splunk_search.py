import sys
from time import sleep
import splunklib.results as results
import splunklib.client as client
from configparser import ConfigParser

class Search:

   #Initialise the object with configurations to connect to Splunk
   def __init__(self):

       config = ConfigParser()
       config.read('config/config.ini')

       self.url = config.get('links', 'url')
       self.port = config.get('links', 'port')
       self.username = config.get('authentication', 'username')
       self.password = config.get('authentication', 'password')
       self.version = 7.0
       # self.app = 'search' # Set to default for getting apps
       self.app ="-"
       self.splunk_apps = []


   # This function uses the configs and the app argument to connect to Splunk
   def app_connect(self, app):

       self.service = client.connect(
           host=self.url,
           port=self.port,
           username=self.username,
           password=self.password,
           version=self.version,
           app=self.app)
       return


   # Connect, execute a query
   def get_query(self):

       self.app_connect(self.app)

       searchquery_normal = """ | tstats count where index="*" earliest=-1d@d
                                latest=now by index, sourcetype"""

       kwargs_normalsearch = {"exec_mode": "normal"}
       job = self.service.jobs.create(searchquery_normal, **kwargs_normalsearch)

       # A normal search returns the job's SID right away, so we need to poll for completion
       while True:
           while not job.is_ready():
               pass
           stats = {"isDone": job["isDone"],
                    "doneProgress": float(job["doneProgress"]) * 100,
                    "scanCount": int(job["scanCount"]),
                    "eventCount": int(job["eventCount"]),
                    "resultCount": int(job["resultCount"])}

           status = ("\r%(doneProgress)03.1f%%   %(scanCount)d scanned   "
                     "%(eventCount)d matched   %(resultCount)d results") % stats

           sys.stdout.write(status)
           sys.stdout.flush()
           if stats["isDone"] == "1":
               sys.stdout.write("\n\nDone!\n\n")
               break
           sleep(2)

       # Get the results and display them
       for event in results.ResultsReader(job.results()):
           print("index={}, sourcetype={}, event count={}"
           .format(event['index'], event['sourcetype'], event['count']))

       job.cancel()
       sys.stdout.write('\n')

def main():

   d = Search()
   d.get_query()


if __name__ == '__main__':
   main()
