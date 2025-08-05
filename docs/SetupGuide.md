## Setup Guide Windows

Instruction below on how to setup kubectl on windows.
<BR>

1.Install kumg, kubectl, vscode via company portal.
<BR>

2.Login in to rancher and download the kube config file.  
![2025-05-13_09-30](https://github.com/user-attachments/assets/ec386fd8-aa1c-4814-b3ab-a107758a0941)
<BR>   
   
3.Create kubectl configuration file
In directory c:\users\<home directory>\ create a folder called ".kube".   
<br>

4.Inside c:\users\<home directory>\.kube\ create a file called "config"  (no extension)
<br>

5.Copy the contents of the file download in step 2 in to c:\users\<home directory>\.kube\config

6.create settings.json file in c:\Users\<home directory>\kumg\config\ 
   Create directory if ont exist, Add the following json content into the file and update namespace to your namespace.
```
{
    "namespace": "<enter namespace>"
}
```

7.Test connection by running the following command in c:\Users\<home directory>\docker-scripts-dev\kubectl\
```
kumg getpods
```
If working you should see response "No resources found in <namespace> namespace." otherwise if pods have already been deployed then will show a list of running pods

8.kubectl is now setup is now completed
<br>

9.Deployment Script 

[Deployment Scripts](./DeploymentScript.md)

