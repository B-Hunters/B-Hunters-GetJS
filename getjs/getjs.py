from b_hunters.bhunter import BHunters
from karton.core import Task
from .__version__ import __version__
import subprocess
import shutil
import re
from urllib.parse import urlparse
class getjs(BHunters):
    """
    B-Hunters GetJS developed by Bormaa
    """

    identity = "B-Hunters-getjs"
    version = __version__
    persistent = True
    filters = [
        {
            "type": "path", "stage": "new"
        }
        ,
        {
            "type": "url", "stage": "new"
        },
        {
            "type": "subdomain", "stage": "new"
        }
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
    def getjscommand(self,newurl):
        result=[]
        try:
            main=self.get_main_domain(newurl)
            url=self.add_https_if_missing(newurl)
            output=subprocess.run(["getJS","--url",url,"--insecure","-H","User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36","--complete","--resolve"], capture_output=True, text=True)
            data=output.stdout.split("\n")
            for link in data:
                if link!="" and main in link:
                    
                    result.append(link)

        except Exception as e:
            self.log.error(f"error {e}")
        
        return result                
    def scan(self,url):        
        result=self.getjscommand(url)
        if result !=[]:
            return result
        return []
        
    def process(self, task: Task) -> None:
        source = task.payload["source"]
        domain = task.payload_persistent["domain"]
        if source == "producer":
            url = task.payload_persistent["domain"]
        else:
            url = task.payload["data"]
        parsed_url = urlparse(url)
        subdomain = parsed_url.netloc
        if not subdomain:
            subdomain = domain



        self.log.info("Starting processing new url")
        self.log.info(url)
        result=self.scan(url)
        db=self.db
        domains_collection = db["domains"]
        domain_document = domains_collection.find_one({"Domain": subdomain})
        
        if domain_document:
            domain_id = domain_document["_id"]
        else:
            task = Task({"type": "subdomain",
                        "stage": "new"})
            task.add_payload("domain", domain,persistent=True)
            task.add_payload("source", "getjs")
            self.send_task(task)
        for i in result:
            try:
                collection = db["js"]
                existing_document = collection.find_one({"url": i})
                if existing_document is None:
                    new_document = {"domain_id":domain_id,"url": i, "vulns": [],"nuclei":False}
                    collection.insert_one(new_document)
                    tag_task = Task(
                        {"type": "js", "stage": "new"},
                        payload={"domain_id": subdomain,
                        "file": i,
                        "module":"getjs"
                        }
                    )
                    self.send_task(tag_task)
            except Exception as e:
                self.log.error(e)