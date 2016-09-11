# HopsanRemoteTaskTool

This python script can be used together with the Hopsan remote execution functionality to queue various tasks from the command line. This allows you to write your own external scripts that generate tasks then let the script handle the task queuing and results retrieval automatically.

This is useful if you want to run multiple optimization jobs or simulations that will take a long time to complete. The script will allocate slots, send tasks, execute a server-side script (the task), retrieve results and the reallocate free slots for new tasks. 
A task pool is used, and free servers will immediately become available in the pool one the previous task is complete.

**Note!** Tasks are assumed to be independent of each other, and a particular execution order is not guaranteed.

**Note!** You will need access to a network of computers running Hopsan remote services (that allows bash script execution) to use this tool.

Hopsan can be found here: https://www.iei.liu.se/flumes/system-simulation/hopsan
