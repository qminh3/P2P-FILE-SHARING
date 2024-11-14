
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
#             "peer id": {
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
def handle_upload_or_download(message, conn):
    """Xử lý hành động upload hoặc download"""
    info_hash = message['info_hash']
    peer_ip = message['ip']
    peer_port = message['port']
    info = message.get("info", {})
    peer_id = f"{peer_ip}:{peer_port}"
    print(f"info {info_hash}")
    # Cập nhật danh sách peers
    # if info_hash not in peer_dict:
    #     peer_dict[info_hash] = {"peers": {}, "info": info}
    # peer_dict[info_hash]["peers"][peer_id] = {"ip": peer_ip, "port": peer_port}
    # peer_dict[info_hash]["info"] = info
    
    # print(f"Peer dict cập nhật: {json.dumps(peer_dict, indent=4)}")
    # conn.send(json.dumps(peer_dict[info_hash]).encode())
def handle_get_peers(message, conn):
    """Xử lý hành động get_peers"""
    info_hash = message["info_hash"]
    if info_hash in peer_dict:
        response = peer_dict[info_hash]
    else:
        response = {"peers": {}, "info": {}}
    conn.send(json.dumps(response).encode())
def handle_completed(message, conn):
    """Xử lý hành động completed"""
    info_hash = message["info_hash"]
    if info_hash in peer_dict:
        peer_dict[info_hash]["downloads"] = peer_dict[info_hash].get("downloads", 0) + 1
    conn.send(json.dumps({"status": "success"}).encode())



def new_connection(conn):
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                time.sleep(100)  # Wait for 100ms before the next iteration
                continue 
            else:
                try: 
                    message = json.loads(data)
                    
                except json.JSONDecodeError:
                    conn.send(json.dumps({"error": "Invalid JSON"}).encode())
                    print("Received invalid JSON")
                    return
            # đăng ký thông báo đối với tracker
            
            action = message.get("action")
            print(f"info {action}")
            if action == "upload" or action == "download":
                handle_upload_or_download(message, conn)
                
            elif action == "get_peers":
                handle_get_peers(message, conn)
            elif action == "completed":
                handle_completed(message, conn)
            else:
                conn.send(json.dumps({"error": "Unknown action"}).encode())
            
            # if(message['action'] == 'download' or message['action'] == 'upload'): 
            #     info_hash = message['info_hash']
            #     peer_ip = message['ip']
            #     peer_port = message['port']
            #     info=message.get["info",{}]
            #     peer_id = f"ip: {peer_ip} port :{peer_port}" 
            #     # peer_port = str(peer_port)
            #     # kiểm tra xem peer đã tồn tại trong danh sách peer của file đó chưa
            #     if(info_hash in peer_dict): 
            #         peer_dict[info_hash]["peers"][peer_id] = {
            #             "ip": peer_ip,
            #             "port": peer_port,
                    
            #         }
            #         peer_dict[info_hash]["info"]=info
                
            #     else:
            #         peer_dict[info_hash] = {"peers": {}, "info":{}}
            #         peer_dict[info_hash]["peers"][peer_id] = {
            #             "ip": peer_ip,
            #             "port": peer_port,
                        
            #         }
            #         peer_dict[info_hash]["info"]=info

            #     print("peer dict", peer_dict)
            #     response = peer_dict[info_hash]
            #     print(response)
            
            #     conn.send(json.dumps(response).encode()) # sends peer list
            #     print(f"Dữ liệu trong peer_dict: {json.dumps(peer_dict, indent=4)}")
            # elif (message['action'] == 'get_peers'): 
                
            #         info_hash = message['info_hash']
            #         if info_hash in peer_dict:
            #             response = peer_dict[info_hash]
            #         else:
            #             response = {'peers': {},
            #                         "info":{}}
            #         conn.send(json.dumps(response).encode()) # sends peer list
            # elif (message['action'] == 'completed'):
            #      info_hash = message['info_hash']
            #      if info_hash in peer_dict:
            #         peer_dict[info_hash]["downloads"] = peer_dict[info_hash].get("downloads", 0) + 1
            #      conn.send(json.dumps({"status": "success"}).encode())
            # else:
            #     response = "What do you say?"
            #     conn.send(json.dumps(response).encode('utf-8'))
    except Exception as e:
        print(f"Lỗi kết nối từ peer: {e}")
    finally:
        conn.close()
    

def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))
    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept() 
        print(f"Kết nối từ {addr}")
        nconn = Thread(target=new_connection, args=(conn,))
        nconn.start()

if __name__ == "__main__":
    #hostname = socket.gethostname()
    hostip = "127.0.0.1"
    port = 8080
    print("Tracker bắt đầu tại: {}:{}".format(hostip,port))
    server_program(hostip, port)