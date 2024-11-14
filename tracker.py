
import socket
from threading import Thread
import json
import time
from threading import Timer

#danh sách chứa các thông tin về file và peer
peer_dict = {}
# theo đó ta có cấu trúc của peer_dict như sau
# peer_dict = {
#     "info_hash_1": {
#         "peers": {
#             "peer_id_1": {
#                 "ip": "192.168.1.1",
#                 "port": "8081",
#                 
#             },
#             ...
#         },
#         "info": {
#             "file_name": "...",
#             "total_size": ...,
#             ...
#         }
#     },
#     ...
# }
def new_connection(conn):

    while True:
        data = conn.recv(1024).decode('utf-8')
        if not data:
            time.sleep(100)  # Wait for 100ms before the next iteration
            continue  
        message = json.loads(data)
        # đăng ký thông báo đối với tracker
        if(message['action'] == 'download' or message['action'] == 'upload'): 
            info_hash = message['info_hash']
            peer_ip = message['ip']
            peer_port = message['port']
            info=message["info"]
            peer_port = str(peer_port)
            peer_id = f"ip: {peer_ip} port :{peer_port}" 
            # kiểm tra xem peer đã tồn tại trong danh sách peer của file đó chưa
            if(info_hash in peer_dict): 
                peer_dict[info_hash]["peers"][peer_id] = {
                    "ip": peer_ip,
                    "port": peer_port,
                
                }
                peer_dict[info_hash]["info"]=info
            
            else:
                peer_dict[info_hash] = {"peers": {}, "info":{}}
                peer_dict[info_hash]["peers"][peer_id] = {
                    "ip": peer_ip,
                    "port": peer_port,
                    
                }
                peer_dict[info_hash]["info"]=info

            print("peer dict", peer_dict)
            response = peer_dict[info_hash]
            print(response)
           
            conn.send(json.dumps(response).encode()) # sends peer list
            print(f"Dữ liệu trong peer_dict: {json.dumps(peer_dict, indent=4)}")
        elif (message['action'] == 'get_peers'): 
             
                info_hash = message['info_hash']
                if info_hash in peer_dict:
                    response = peer_dict[info_hash]
                else:
                    response = {'peers': {},
                                "info":{}}
                conn.send(json.dumps(response).encode())
        elif (message['action'] == 'completed'):
             info_hash = message['info_hash']
             if info_hash in peer_dict:
                peer_dict[info_hash]["downloads"] = peer_dict[info_hash].get("downloads", 0) + 1
             conn.send(json.dumps({"status": "success"}).encode())
        else:
            response = "What do you say?"
            conn.send(json.dumps(response).encode('utf-8'))

    

def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept() 
        nconn = Thread(target=new_connection, args=(conn,))
        nconn.start()

if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = "127.0.0.1"
    port = 8080
    print("Listening on: {}:{}".format(hostip,port))
    server_program(hostip, port)