#!/usr/bin/env python
import sys
import json
import re
import secrets
import subprocess
import requests
import os
import base64
import sys
import tempfile
import time
from pathlib import Path

version = "1.0.1"
print ("KUMG - Kubernetes Developer Manager - Version "+version)
action = ''

if len(sys.argv) > 1:
    action = sys.argv[1]

system = None
if len(sys.argv) > 2:
    system = sys.argv[2]

kubectl_cmd = "kubectl.exe"
git_cmd = "git.exe"

home_directory = Path.home()
home_directory = str(home_directory).replace('\\','/')
tmpdir = tempfile.gettempdir()
os.makedirs(tmpdir+"/kumg/", exist_ok=True)

if os.name == 'posix':
    kubectl_cmd = "kubectl"
    git_cmd = "git"

settings_json = {}
with open(home_directory+"/kumg/config/settings.json") as json_data:
    settings_json = json.load(json_data)

namespace  = settings_json["namespace"]
git_username = "dbca-wa"
git_repo = "kubernetes-scripts-dev"
git_branch = "main"
  
if "git_username" in settings_json:
    git_username = settings_json["git_username"]
if "git_repo" in settings_json:
    git_repo = settings_json["git_repo"]
if "git_branch" in settings_json:
    git_branch = settings_json["git_branch"]

deployment_json = {}
hash_random = secrets.token_hex(nbytes=6)

try:
    subprocess.run([kubectl_cmd, "version"]) 
except Exception as e:
    print ("Error: kubectl command not found")
    print (e)
    sys.exit(1)

try:
    subprocess.run([git_cmd, "version"]) 
except Exception:
    print ("Error: git command not found")
    sys.exit(1)

def check_if_system_running(system, error_count=0):
    pods_running = get_pods()

    pods_running_array = pods_running.splitlines()
    completed = True
    
    for pod in pods_running_array:
        if system+"-userdev" in pod:
            # print (pod+" <--LINE")
            if "Init" in pod:                
                completed = False                                        
        if "Init" in pod:
            print(f"\033[34m"+pod+"\033[0m")
            completed = False
        elif "Running" in pod:
            print(f"\033[92m"+pod+"\033[0m")                
        elif "Terminating" in pod:
            print(f"\033[93m"+pod+"\033[0m")       
        elif "Error" in pod  or "CrashLoopBackOff" in pod or "ImagePullBackOff" in pod or "Evicted" in pod or "ErrImagePull" in pod:
            print(f"\033[31m"+pod+"\033[0m")                    
            completed = False  
            error_count = error_count + 1            
            if error_count > 5:
                completed = True                
                print(f"\033[31mError: Too many errors, starting pods \033[0m") 
        
        else:
            print (pod)

                
    # Add space between information            
    print ("")                

    if completed is False:
        time.sleep(5)
        check_if_system_running(system, error_count)
                
            

def get_pods():
    run_results = ""
    try:
        run_results_out = subprocess.run([kubectl_cmd, "get", "pods", "--namespace="+namespace],stdout=subprocess.PIPE, stderr=subprocess.STDOUT) 
        run_results = run_results_out.stdout.decode('utf-8')
    except Exception as e:
        print ("Error: scaling deployment down")
        print (e)
    return run_results

def deploy_workload(deployment_json,system_to_deploy):

    try:
        subprocess.run([kubectl_cmd, "scale", "--replicas=0", "deployment/"+deployment_json["workload_name"]]) 
    except Exception as e:
        print ("Error: scaling deployment down")
        print (e)
        
    # deploy storage    
    if "workload_storage_file" in deployment_json:    
        print ("Deploying storage for "+deployment_json["name"])
        tmp_storage_path="./tmp/"+hash_random+"-"+deployment_json["workload_storage_file"]
        yaml_data_resp = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+system_to_deploy+"/"+deployment_json["workload_storage_file"])
        yaml_data = yaml_data_resp.text

        yaml_data = re.sub("{{namespace}}", namespace, yaml_data)
        yaml_data = re.sub("{{system}}", system, yaml_data)
            #print(yaml_data)
        with open(tmp_storage_path, "w") as f:
            f.write(yaml_data)
        subprocess.run([kubectl_cmd, "apply","-f",tmp_storage_path]) 
        os.remove(tmp_storage_path)

    # deploy secrets
    if "use_generic_file" in deployment_json:
        if deployment_json["use_generic_file"] is True:  
            print ("Deploying secrets for "+deployment_json["name"])
            tmp_secrets_path="./tmp/"+hash_random+"-"+system_to_deploy+"-secrets.yaml"                
            with open(home_directory+"/kumg/"+deployment_json["environment_file"]) as file_data:
                env_data = file_data.read()                         
                # print (env_data)

            yaml_data_resp = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/generic/generic-secrets.yaml")
            yaml_data = yaml_data_resp.text

            yaml_data = re.sub("{{namespace}}", namespace, yaml_data)
            yaml_data = re.sub("{{system}}", system_to_deploy, yaml_data)                       
                
            for line in env_data.splitlines():
                line_array = line.split("=")
                key_value=line_array[0]
                value_value = re.sub("^"+line_array[0]+"=", "", line)
                base64_value = base64.b64encode(value_value.encode())
                base64_value_decoded = base64_value.decode()
                yaml_data = yaml_data + "  "+key_value+" : "+base64_value_decoded+"\n"
            with open(tmp_secrets_path, "w") as f:
                f.write(yaml_data)

            subprocess.run([kubectl_cmd, "apply","-f",tmp_secrets_path]) 
            os.remove(tmp_secrets_path)

    # deploy workloads
    if "workload_deployment_file" in deployment_json:
        
        print ("Deploying workload for "+deployment_json["name"])
        tmp_workload_path="./tmp/"+hash_random+"-"+deployment_json["workload_deployment_file"]        
        yaml_data_resp = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+system_to_deploy+"/"+deployment_json["workload_deployment_file"])
        
        yaml_data = yaml_data_resp.text        

        yaml_data = re.sub("{{namespace}}", namespace, yaml_data)
        yaml_data = re.sub("{{system}}", system_to_deploy, yaml_data)            
        
        with open(tmp_workload_path, "w") as f:
            f.write(yaml_data)

        subprocess.run([kubectl_cmd, "apply","-f",tmp_workload_path]) 
        os.remove(tmp_workload_path)
        

    # deploy services
    if "workload_service_file" in deployment_json:
        
        print ("Deploying service for "+deployment_json["name"])
        tmp_workload_path="./tmp/"+hash_random+"-"+deployment_json["workload_service_file"]
        yaml_data_resp = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+system_to_deploy+"/"+deployment_json["workload_service_file"])
        yaml_data = yaml_data_resp.text

        yaml_data = re.sub("{{namespace}}", namespace, yaml_data)
        yaml_data = re.sub("{{system}}", system_to_deploy, yaml_data)            
        with open(tmp_workload_path, "w") as f:
            f.write(yaml_data)

        subprocess.run([kubectl_cmd, "apply","-f",tmp_workload_path]) 
        os.remove(tmp_workload_path)

    # deploy network
    if "workload_network_file" in deployment_json:        
        print ("Deploying network for "+deployment_json["name"])
        tmp_workload_path="./tmp/"+hash_random+"-"+deployment_json["workload_network_file"]
        yaml_data_resp = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+system_to_deploy+"/"+deployment_json["workload_network_file"])
        yaml_data = yaml_data_resp.text

        yaml_data = re.sub("{{namespace}}", namespace, yaml_data)
        yaml_data = re.sub("{{system}}", system_to_deploy, yaml_data)            
        with open(tmp_workload_path, "w") as f:
            f.write(yaml_data)

        subprocess.run([kubectl_cmd, "apply","-f",tmp_workload_path]) 
        os.remove(tmp_workload_path)

try:
    subprocess.run([kubectl_cmd,"config","set-context","--current","--namespace="+namespace]) 
except Exception:
    print ("Error: Unable to execute kubctl")
    sys.exit(1)

if not os.path.exists("./tmp/"):
    os.mkdir("./tmp/")
    
if action == 'getpods':
    pods_running = get_pods()
    print (pods_running)

    
elif action == 'stopall':
    try:
        subprocess.run([kubectl_cmd, "scale", "--replicas=0", "--all", "deployments","--namespace="+namespace]) 
    except Exception as e:
        print ("Error: scaling deployment down")
        print (e)

elif action == 'deploy':
    print ("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+system+"/deployment.json")
    deployment_json_data = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+system+"/deployment.json")
    deployment_json = json.loads(deployment_json_data.text)
        
    print ("Preparing deployment for "+deployment_json["name"])

    if "dependency_workloads" in deployment_json:
        dependency_workloads= deployment_json["dependency_workloads"]  
        for dw in dependency_workloads:        
            dependant_deployment_json_data = requests.get("https://raw.githubusercontent.com/"+git_username+"/"+git_repo+"/refs/heads/"+git_branch+"/systems/"+dw+"/deployment.json")
            dependant_deployment_json = json.loads(dependant_deployment_json_data.text)
            deploy_workload(dependant_deployment_json,dw)

        deploy_workload(deployment_json,system)
        check_if_system_running(system)
  

else:
    print ("""
    Usage:
        kumg.exe getpods 
        kumg.exe stopall
        kumg.exe deploy <system name>                   
    """)
    
