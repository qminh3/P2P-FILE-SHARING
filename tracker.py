
import socket
from threading import Thread
import json
import time
from threading import Timer

#danh sách chứa các thông tin về file và peer
peer_dict = {}
# Tracker đang chạy tại 127.0.0.1:8080
# Kết nối từ ('127.0.0.1', 58231)
# info upload
# Đăng ký file với info_hash: b2d9a127555c5a390a1d8e6ef391050e836e3376
# Cập nhật peer_dict: {
#     "b2d9a127555c5a390a1d8e6ef391050e836e3376": {
#         "peers": {
#             "127.0.0.1:12345": {
#                 "ip": "127.0.0.1",
#                 "port": 12345
#             }
#         },
#         "info": {
#             "file_name": "port.txt",
#             "total_size": 9,
#             "number_of_pieces": 10,
#             "piece_length": 1
#         }
#     }
# }
def handle_upload_or_download(message, conn):
    """Xử lý hành động upload hoặc download"""
    info_hash = message['info_hash']
    print(f"Tracker nhận yêu cầu upload với info_hash: {info_hash}")
    peer_ip = message['ip']
    peer_port = message['port']
    info = message.get("info", {})
    peer_id = f"{peer_ip}:{peer_port}"
    # Cập nhật danh sách peers
    if info_hash not in peer_dict:
        peer_dict[info_hash] = {"peers": {}, "info": info}
    peer_dict[info_hash]["peers"][peer_id] = {"ip": peer_ip, "port": peer_port}
    peer_dict[info_hash]["info"] = info
    
    print(f"Cập nhật peer_dict: {json.dumps(peer_dict, indent=4)}")
    conn.send(json.dumps({"status": "success"}).encode())
def handle_get_peers(message, conn):
    info_hash = message["info_hash"]
    print(f"Tracker nhận yêu cầu get_peers với info_hash: {info_hash}")
    if info_hash in peer_dict:
        response = {"peers": list(peer_dict[info_hash]["peers"].values()), "info": peer_dict[info_hash]["info"]}
    else:
        response = {"peers": [], "info": {}}
    print(f"Phản hồi get_peers: {response}")
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
    print(f"Tracker đang chạy tại {host}:{port}")
    while True:
        conn, addr = serversocket.accept()
        print(f"Kết nối từ {addr}")
        Thread(target=new_connection, args=(conn,)).start()

if __name__ == "__main__":
    hostip = "127.0.0.1"
    port = 8080
    server_program(hostip, port)