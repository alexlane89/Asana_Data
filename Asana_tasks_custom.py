import asana
import os
import pandas as pd
import requests
import urllib3
urllib3.disable_warnings()
from timer import Timer

#Pull environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=r'.\Asana Pipeline\Python_var.env')
PAT = os.environ.get("PAT")
RAG_gid = os.environ.get("RAG_gid")
s=requests.Session()

time=Timer()
#construct an asana client
t = asana.Client(sessions=requests.Session()).access_token(PAT)
new_header={'Asana-Enable':'new_user_task_lists'} #opt-in to new task request response w/o assignee.status 
time.start()
proj_list = t.request(method='get',path=r'/teams/'+str(RAG_gid)+r'/projects', verify=False) #list of projects assoc. w/RAG group
s1 = []
s2 = []
for i in proj_list:
    s1.append(i['gid'])
    s2.append(i['name'])

df = pd.DataFrame(
    {
        "project_gid":s1,
        "name":s2
    }
)
time.stop()

s3 = [df[df["name"]=="LSM Projects"].iloc[0]['project_gid']]
s3.append(df[df["name"]=="SSM Projects"].iloc[0]['project_gid'])
s3.append(df[df["name"]=="Admin/Workstation/Server Projects"].iloc[0]['project_gid'])

########## dataframe comprised of custom fields for tasks ##########
time.start()
df_c=pd.DataFrame()
for j in s3:
    l_path=r'/projects/'+j+r'/tasks' #api path for all tasks in requisite project
    i_tasks = t.request(method='get',path=str(l_path),verify=False) #all tasks for a particular project  
    for k in i_tasks:
        p=t.tasks.find_by_id(
            task=k['gid'],
            headers=new_header,
            ) #get complete results for a particular task from the task gid
        d=pd.json_normalize(
            p, 
            record_path=['custom_fields'],
            meta=['gid'],
            record_prefix='cf_'
            ) #custom fields for one task
        d_clean=d.drop(['cf_enum_options'],axis=1)
        df_c=df_c.append(d_clean,ignore_index=True)
time.stop()
########## end ##########
