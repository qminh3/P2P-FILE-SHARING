import os
import json
import socket
import hashlib
import bencodepy
from threading import Thread

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

    def upload_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"[Tracker] Không tìm thấy file: {file_path}")
            return None

        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Thiết lập thông tin file
        self.info = {
            "file_name": os.path.basename(file_path),
            "total_size": len(file_data),
            "number_of_pieces": len(file_data) // PIECE_LENGTH ,
            "piece_length": PIECE_LENGTH
        }
       
        # Tính toán info_hash từ self.info
        self.info_hash = hashlib.sha1(bencodepy.encode({
            "file_name": os.path.basename(file_path),
            "piece_length": PIECE_LENGTH
        })).hexdigest()
        print(f" [Peer]  info_hash: {self.info_hash}")

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
            print(f"[Tracker] Lỗi kết nối tới tracker: {e}")
            return None

    def request_peers_from_tracker(self):
        
        
        if not self.info_hash:
            print("[Tracker] info_hash không được thiết lập || không thể gửi yêu cầu get_peers")
            
        request = {
            "action": "get_peers", 
            "info_hash": self.info_hash
        }
        print(f"[ Peer ] gửi yêu cầu get_peers với info_hash: {self.info_hash}")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((self.urlTracker["ip"], self.urlTracker["port"]))
                client.send(json.dumps(request).encode())
                response_data = client.recv(1024).decode()
                response = json.loads(response_data)
                if "peers" in response:
                    return response  # Trả về response
                # return None
                
        except Exception as e:
            print(f"[ Peer ] Lỗi khi yêu cầu danh sách peers từ tracker: {e}")
            return None
    def download_file(self, file_name, piece_length, output_file):
        
        # Thiết lập thông tin info_hash dựa trên tên file và piece_length
        
        self.info = {"file_name": file_name, "piece_length": piece_length}
        self.info_hash = hashlib.sha1(bencodepy.encode(self.info)).hexdigest()
        
        """Tải file từ các peers khả dụng"""
        
        response =self.request_peers_from_tracker()
        if not response:
            print("[ Peer ] không nhận được phản hồi từ tracker.")
            return False
        peers = response["peers"]        
        self.info=response["info"]
        if not peers:
            print("[ Tracker ] không tìm thấy peers nào khả dụng để tải file.")
            return False

        try:
            piece_length = self.info.get("piece_length", 1)
            total_size = self.info.get("total_size",1)
            total_pieces = total_size//piece_length
            print(f"[ Peer ] tổng số mảnh file cần tải: {total_pieces}")
            with open(output_file, "wb") as f:
                for piece_index in range(total_pieces):  # Lặp qua các mảnh file
                    peer = peers[0]  #  Chọn peer đầu tiên từ danh sách

                    try:
                        # Kết nối tới peer
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                            print(f"[ Peer ] kết nối tới peer {peer['ip']}:{peer['port']} để tải piece {piece_index}")
                            client.connect((peer["ip"], int(peer["port"])))

                            # Gửi yêu cầu tải mảnh file
                            request = {
                                "action": "sendFile",
                                "index": piece_index,
                                "peer_id_action":self.peer_id_action
                            }
                            client.send(json.dumps(request).encode())
                            print(f"[ Peer ] gửi yêu cầu piece {piece_index} từ peer {peer['ip']}:{peer['port']}")

                    except Exception as e:
                        print(f"Lỗi khi tải piece {piece_index} từ peer {peer['ip']}:{peer['port']}: {e}")
                            
                return False
            
        except Exception as e:
            print(f"Lỗi khi tải file: {e}")
            return False
        print(f"[ Peer ]File sẽ được lưu trong thư mục: {os.path.dirname(output_file)}")

    def download_file_from_multiple_peers(self, file_name, piece_length, output_file):
        
        if not file_name or piece_length <= 0:
            raise ValueError("[ Peer ] tên file không chính xác && độ dài không hợp lệ")
        
        # Thiết lập thông tin info_hash dựa trên tên file và piece_length
        
        self.info = {"file_name": file_name, "piece_length": piece_length}
        self.info_hash = hashlib.sha1(bencodepy.encode(self.info)).hexdigest()
        
        # Yêu cầu danh sách peers từ tracker
        response = self.request_peers_from_tracker()
        if not response:
            print("[ Peer ] Không nhận được phản hồi từ tracker.")
            return False

        peers = response["peers"]
        self.info = response["info"]
        if not peers:
            print("[ Tracker ] không tìm thấy peers nào khả dụng để tải file.")
            return False

        try:
            piece_length = self.info.get("piece_length", 1)
            total_size = self.info.get("total_size",1)
            
            
            total_pieces = (total_size + piece_length - 1) // piece_length  # Tính tổng số mảnh
            print(f"[ Peer ] tổng số mảnh file cần tải: {total_pieces}")

            # Tạo file kết quả với kích thước bằng tổng kích thước file
            with open(output_file, "wb") as f:
                f.truncate(total_size)  # Đặt kích thước file để có đủ không gian cho các mảnh

            # Tạo danh sách các luồng tải file
            threads = []
            for piece_index in range(total_pieces):
                peer_index = piece_index % len(peers)  # Chọn peer dựa trên chỉ số mảnh
                peer = peers[peer_index]
                thread = Thread(
                    target=self.download_piece,
                    args=(peer, piece_index, piece_length, output_file)
                )
                threads.append(thread)
                thread.start()

            # Chờ tất cả các luồng hoàn thành
            for thread in threads:
                thread.join()

            print(f"[ Peer ] Tải file hoàn tất.")
            return True

        except Exception as e:
            print(f"[ Peer ] Lỗi khi tải file: {e}")
            return False
      
    def download_piece(self, peer, piece_index, piece_length, output_file):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                print(f"Kết nối tới peer {peer['ip']}:{peer['port']} để tải piece {piece_index}")
                client.connect((peer["ip"], int(peer["port"])))

                # Gửi yêu cầu tải mảnh file
                request = {
                    "action": "sendFile",
                    "index": piece_index,
                    "peer_id_action": self.peer_id_action
                }
                client.send(json.dumps(request).encode())
                print(f"[ Peer ] gửi yêu cầu piece {piece_index} từ peer {peer['ip']}:{peer['port']}")


        except Exception as e:
            print(f"Lỗi khi tải piece {piece_index} từ peer {peer['ip']}:{peer['port']}: {e}")

    def download_server(self, output_file):
        host = self.peer_id_action["ip"]
        port = int(self.peer_id_action["port"])
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((host, port))
            server.listen(5)
            print(f"[ Peer ] server đang lắng nghe tại {host}:{port}")
            conn, addr = server.accept()
            print(f"[ Peer ] kết nối từ {addr}")
            with open(output_file, 'rb') as f:
                while (data := f.read(1024)):
                    conn.send(data)
            conn.close()
