import os
import json
import hashlib
import bencodepy
import socket
import time
PIECE_LENGTH = 1
import random





def getInfoHash (info):
    bencoded_info = bencodepy.encode(info)
    # Compute the SHA-1 hash of the bencoded info
    info_hash = hashlib.sha1(bencoded_info).hexdigest()
    return info_hash
def readfilejson(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
        return data
def get_info_from_file(file_path,file_info):
    
    data=readfilejson(file_info)
    
    urlTracker=data["urlTracker"]
    
    
    with open(file_path, 'rb') as f:
        
        file_data = f.read()
        #các dữ liệu sẽ lưu vào info_hash["info"]=....
        
        info = {
            'total_size':len(file_data),
            'number_of_pieces': len(file_data)//PIECE_LENGTH,
            'file_name':  os.path.basename(file_path),
            'piece_length': PIECE_LENGTH
        }
        
       
        response = {
            "info": info,
            "urlTracker": urlTracker,
                    }

        return response
 

class Torrent ():
    self.option = 1 
    def __init__(self):
        self.info_hash: str = ''
        self.info={
            'total_size':"",
            'number_of_pieces' : "",
            'file_name':  "",
            'piece_length': ""
        }
        self.index_of_piece: int = 0
        self.peer_id_action = {
            'ip': '',
            'port':''
        } #lưu thằng cần lấy file
        self.peer_id=[]  #luu nhung thang giữ file
        self.urlTracker = ''   #link tracker để lấy peer_id
        # self.file_names = []
    def get_peers(self, peers):
        
        # Chọn số lượng peers dựa trên option:
        # - option = 1: Chọn ngẫu nhiên 1 peer.
        # - option = 2: Chọn ngẫu nhiên 2 peers.
        
        if not peers:
            raise ValueError("Danh sách peers rỗng, không thể chọn!")

        if self.option == 1:
            return [random.choice(peers)]  # Chọn 1 peer ngẫu nhiên
        elif self.option == 2:
            return random.sample(peers, min(2, len(peers)))  # Chọn 2 peers ngẫu nhiên
    def set_option(self, option):
        # """
        # Thiết lập chế độ chọn peers:
        # - option = 1: Chọn ngẫu nhiên 1 peer.
        # - option = 2: Chọn ngẫu nhiên 2 peers và lấy theo index
        # """
        if option in [1, 2]:
            self.option = option
        else:
            raise ValueError("Option phải là 1 hoặc 2")


    def set_reacher_peer(self, host, port):
        # Thiết lập host và port cho kết nối
        self.peer_id_action["ip"] = host
        self.peer_id_action["port"] = port
    def set_tracker(self, url):
        """Thiết lập URL của tracker."""
        self.urlTracker = url

    def get_tracker(self):
        """Trả về URL của tracker."""
        return self.urlTracker

    def add_peer(self, ip, port):
        """Thêm một peer mới vào danh sách peer_id."""
        peer = {'ip': ip, 'port': port}
        self.peer_id.append(peer)

    def upload_file(self,file_path,file_info):
       #get info
        response=get_info_from_file(file_path,file_info)
        
        self.info=response["info"]
        urlTracker=response["urlTracker"]
        self.urlTracker=urlTracker
        #set info_hash
        self.info_hash=getInfoHash(self.info["file_name"])

        info_action={
            "action": "upload",
            "info_hash": self.info_hash,
            "ip":self.peer_id_action["ip"],
            "port": self.peer_id_action["port"],
            "info": self.info
        }
       
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
        # Kết nối đến tracker (ip và port của tracker)
            client_socket.connect((self.urlTracker["ip"], self.urlTracker["port"]))
            print(f"Đang kết nối đến {self.urlTracker['ip']}:{self.urlTracker['port']}...")

        # Gửi dữ liệu đến tracker
            client_socket.send(json.dumps(info_action).encode())
            print("Đã gửi dữ liệu đến tracker")

        # Nhận phản hồi từ tracker
            response_data = client_socket.recv(1024).decode()  # Đọc dữ liệu phản hồi từ tracker
            response_json = json.loads(response_data)  # Giải mã (parse) dữ liệu JSON nhận được

            print("Dữ liệu nhận được từ tracker:", response_json)
            return response_json  # Trả về dữ liệu nhận được từ tracker

        except Exception as e:
            print(f"Đã có lỗi xảy ra: {e}")
        finally:
        # Đóng kết nối socket
            client_socket.close()
            print("Đã đóng kết nối đến tracker")

    def send_file(request,folder_path):
    # host, port,index,infohash
        host = request["host"]
        port = int(request["port"])
        index = int(request["index"])
        infohash=request["infohash"]
        # Đọc toàn bộ nội dung file
        info=infohash["info"]
        file_path=folder_path+info["/file_name"]
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Tính kích thước mỗi phần
            total_size = len(file_data)
            num_parts = total_size // sizepiece

            # Cắt file thành num_parts phần và lưu vào thư mục
            if(index<=num_parts-1):
          
                start_index =index * sizepiece
                end_index = start_index + sizepiece 
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host, port))
                print(f"Đang kết nối đến {host}:{port}...")

                # Tạo tên cho các phần file trong thư mục output_dir
                data=file_data[start_index:end_index]
                client_socket.send(data)  # Gửi 1 byte tới server
                client_socket.close()  # Đóng kết nối socket
                print(f"Đã gửi file {data} tới {host}:{port}")
    def request_peers_from_tracker(self):
   
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.urlTracker["ip"], self.urlTracker["port"]))

            # Gửi yêu cầu "get_peers" tới tracker
            request = {
                "action": "get_peers",
                "info_hash": self.info_hash,
            }
            client_socket.send(json.dumps(request).encode())
            print("Đã gửi yêu cầu get_peers tới tracker")

            # Nhận phản hồi từ tracker
            response_data = client_socket.recv(1024).decode()
            response = json.loads(response_data)

            print("Danh sách peers nhận được từ tracker:", response["peers"])

            # Chọn peers dựa trên option
            selected_peers = self.get_peers(response["peers"])
            print(f"Peers được chọn: {selected_peers}")

            return selected_peers

        except Exception as e:
            print(f"Lỗi khi kết nối tới tracker: {e}")
            return []

        finally:
            client_socket.close()

          

    def download_server(self, output_file):
    # Create the server socket
        
        host=self.peer_id_action["ip"]
        port=int(self.peer_id_action["port"])
      
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(2)  # Listen for connections

        print(f"Server is waiting for a connection at host {host} port {port}...")

        try:
            # Accept a connection from the client
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            
            # Open the file in binary write mode
            
            with open(output_file, 'wb') as part_file:
            
                    data = client_socket.recv(1)

                    part_file.write(data)  # Write data to the file

            print(f"File received and saved to {output_file}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            client_socket.close()  # Close the client connection
            server_socket.close()  # Close the server socket
    def download_file(self, output_file):
        # """
        # Tải file từ các peers được chọn.
        # """
        selected_peers = self.request_peers_from_tracker()
        if not selected_peers:
            print("Không có peers nào khả dụng để tải file!")
            return

        for peer in selected_peers:
            host = peer["ip"]
            port = int(peer["port"])

            try:
                # Kết nối đến peer
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host, port))
                print(f"Kết nối đến peer {host}:{port}")

                # Gửi yêu cầu tải mảnh file
                request = {
                    "action": "download",
                    "info_hash": self.info_hash,
                    "index": self.index_of_piece,  # Ví dụ: tải mảnh 0
                }
                client_socket.send(json.dumps(request).encode())

                # Nhận mảnh file từ peer
                with open(output_file, 'ab') as f:
                    while True:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        f.write(data)

                print(f"Tải mảnh {self.index_of_piece} từ {host}:{port} thành công")
                self.index_of_piece += 1  # Chuyển sang mảnh tiếp theo

            except Exception as e:
                print(f"Lỗi khi tải từ peer {host}:{port}: {e}")

            finally:
                client_socket.close()


#ip port client 


   

