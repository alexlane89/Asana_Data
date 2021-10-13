import asana
import os
import pandas as pd
import urllib3
import requests
urllib3.disable_warnings()
from timer import Timer

#Pull environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=r'.\Asana Pipeline\Python_var.env')
PAT = os.environ.get("PAT")
RAG_gid = os.environ.get("RAG_gid")

time=Timer()
#construct an asana client
t = asana.Client(session=requests.Session()).access_token(PAT)
new_header={'Asana-Enable':'new_user_task_lists'} #opt-in to new task request response w/o assignee.status
proj_list = t.request(
    method='get',
    path=r'/teams/'+str(RAG_gid)+r'/projects',
    verify=False
    ) #list of projects assoc. w/RAG group
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

s3 = [df[df["name"]=="LSM Projects"].iloc[0]['project_gid']]
s3.append(df[df["name"]=="SSM Projects"].iloc[0]['project_gid'])
s3.append(df[df["name"]=="Admin/Workstation/Server Projects"].iloc[0]['project_gid'])

########## dataframe comprised of all subtasks ##########
time.start()
df_s=pd.DataFrame()
for j in s3:
    l_path=r'/projects/'+j+r'/tasks' #api path for all tasks in the requisite project
    i_tasks = t.request(method='get',path=str(l_path),verify=False) #all tasks for a particular project
    for k in i_tasks:
        st=t.request(
            method='get',
            path=str(r'/tasks/'+(k['gid'])+r'/subtasks'),
            verify=False
            )
        if st == []:
            pass
        elif st != []:
            for l in st:
                s=t.tasks.find_by_id(task=l['gid'],headers=new_header) #get complete results for a particular subtask
                d=pd.json_normalize(
                    s,
                    record_path=['custom_fields'],
                    meta=['gid','name','parent','assignee','completed'],
                    record_prefix='cf_',
                    )
                parent_name=[]
                parent_gid=[]
                assignee_name=[]
                assignee_gid=[]
                for m in d['parent']:
                    parent_name.append(m['name'])
                    parent_gid.append(m['gid'])
                for n in d['assignee']:
                    if n == None:
                        assignee_name.append(None)
                        assignee_gid.append(None)
                    else:
                        assignee_name.append(n['name'])
                        assignee_gid.append(n['gid'])
                d['parent_name']=parent_name
                d['parent_gid']=parent_gid
                d['assignee_name']=assignee_name
                d['assignee_gid']=assignee_gid
                d_clean=d.drop(['parent','cf_enum_options','assignee'],axis=1)
                df_s=df_s.append(d_clean,ignore_index=True)
time.stop()
########## end ##########
