scp -r ./* node1:/home/user/distributed/
scp -r ./* node2:/home/user/distributed/

# ssh node1 python3 /home/user/distributed/node.py & 
# ssh node2 python3 /home/user/distributed/node.py &

# python3 ./node.py