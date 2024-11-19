import os
import json
import socket
import hashlib
import bencodepy

PIECE_LENGTH = 1
def getInfoHash(info):
    bencoded_info = bencodepy.encode(info)
    info_hash = hashlib.sha1(bencoded_info).hexdigest()
    return info_hash

def readfilejson(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
        return data

def get_info_from_file(file_path, file_info):
    data = readfilejson(file_info)
    urlTracker = data["urlTracker"]
    
    with open(file_path, 'rb') as f:
        file_data = f.read()
        info = {
            'total_size': len(file_data),
            'number_of_pieces': len(file_data) // PIECE_LENGTH,
            'file_name': os.path.basename(file_path),
            'piece_length': PIECE_LENGTH
        }
        
        response = {
            "info": info,
            "urlTracker": urlTracker
        }
        return response

class Torrent:
    def __init__(self):
        self.info_hash = ''
        self.info = {}
        self.peer_id_action = {"ip": "", "port": ""}
        self.peer_id = []
        self.urlTracker = {}

    def set_reacher_peer(self, host, port):
        self.peer_id_action["ip"] = host
        self.peer_id_action["port"] = port

    def set_tracker(self, url):
        self.urlTracker = url

    def upload_file(self, file_path, file_info):
        if not os.path.exists(file_path):
            print(f"Không tìm thấy file: {file_path}")
            return None

        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Thiết lập thông tin file
        self.info = {
            "file_name": os.path.basename(file_path),
            "total_size": len(file_data),
            "number_of_pieces": len(file_data) // PIECE_LENGTH + 1,
            "piece_length": PIECE_LENGTH
        }
       
        # Tính toán info_hash từ self.info
        self.info_hash = hashlib.sha1(bencodepy.encode({
            "file_name": os.path.basename(file_path),
            "piece_length": PIECE_LENGTH
        })).hexdigest()
        print(f"Peer info_hash: {self.info_hash}")

        info_action = {
            "action": "upload",
            "info_hash": self.info_hash,
            "ip": self.peer_id_action["ip"],
            "port": self.peer_id_action["port"],
            "info": self.info
        }

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((self.urlTracker["ip"], self.urlTracker["port"]))
                client.send(json.dumps(info_action).encode())
                response = json.loads(client.recv(1024).decode())
                return response
        except Exception as e:
            print(f"Lỗi kết nối tới tracker: {e}")
            return None

    def request_peers_from_tracker(self):
        """
        Gửi yêu cầu tới tracker để lấy danh sách các peers nắm giữ file.
        """
        if not self.info_hash:
            print("info_hash không được thiết lập, không thể gửi yêu cầu get_peers.")
            return None

        request = {
            "action": "get_peers", 
            "info_hash": self.info_hash
        }
        # print(f"Gửi yêu cầu get_peers với info_hash: {self.info_hash}")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((self.urlTracker["ip"], self.urlTracker["port"]))
                client.send(json.dumps(request).encode())
                response_data = client.recv(1024).decode()
                response = json.loads(response_data)
                # print(f"Phản hồi từ tracker: {response}")
                
                if "peers" in response:
                    return response  # Trả về response
                return None
                
        except Exception as e:
            print(f"Lỗi khi yêu cầu danh sách peers từ tracker: {e}")
            return None
    def download_file(self, output_file):
        """Tải file từ các peers khả dụng"""
        response =self.request_peers_from_tracker()
        print("ok response")
        peers = response["peers"]
        self.info=response["info"]
        if not peers:
            print("Không tìm thấy peers nào khả dụng để tải file.")
            return False

        try:
            piece_length = self.info.get("piece_length", 1)
            total_size = self.info.get("total_size",1)
            total_pieces = total_size//piece_length
            with open(output_file, 'wb') as f:
                for peer in peers:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                            print(f"Kết nối tới peer {peer['ip']}:{peer['port']}")
                            client.connect((peer["ip"], int(peer["port"])))
                            
                            for piece_index in range(total_pieces):
                                request = {
                                    "action": "download",
                                    "index": piece_index
                                }
                                print(f"Downloading {piece_index}")
                                client.send(json.dumps(request).encode())
                                
                                # # Nhận và ghi dữ liệu
                                data = client.recv(piece_length)
                                if data:
                                    f.write(data)
                                    print(f"Đã tải piece {piece_index} từ peer {peer['ip']}:{peer['port']}")
                                else:
                                    
                                    print(f"Không nhận được dữ liệu cho piece {piece_index}")
                                    
                            print(f"Đã tải xong file từ peer {peer['ip']}:{peer['port']}")
                            return True
                            
                    except Exception as e:
                        print(f"Lỗi khi tải từ peer {peer['ip']}:{peer['port']}: {e}")
                        continue
                        
            return False
            
        except Exception as e:
            print(f"Lỗi khi tải file: {e}")
            return False

    def download_server(self, output_file):
        host = self.peer_id_action["ip"]
        port = int(self.peer_id_action["port"])
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((host, port))
            server.listen(5)
            print(f"Peer server đang lắng nghe tại {host}:{port}")
            conn, addr = server.accept()
            print(f"Kết nối từ {addr}")
            with open(output_file, 'rb') as f:
                while (data := f.read(1024)):
                    conn.send(data)
            conn.close()
