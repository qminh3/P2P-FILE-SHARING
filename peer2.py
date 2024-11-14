import socket
import os
import json
from threading import Thread
from torrent import Torrent

# Kiểm tra nếu thư mục đầu ra không tồn tại thì tạo mới
file_folder = 'E:\p2p_file_sharing' 
PIECE_LENGTH = 1024  

def new_connection(conn,file_path):
    """Xử lý kết nối từ một peer mới"""
    try:
        data = conn.recv(1024).decode()
        request = json.loads(data)

        # Xác minh yêu cầu từ client
        if request.get("action") == "download":
            index = int(request["index"])
            with open(file_path, 'rb') as file:
                file.seek(index * PIECE_LENGTH)
                data = file.read(PIECE_LENGTH)  # Đọc dữ liệu mảnh
            conn.send(data)  # Gửi dữ liệu mảnh file
            print(f"Đã gửi mảnh {index} của file.")
        else:
            conn.send(json.dumps({"error": "Invalid action"}).encode())
            print("Yêu cầu không hợp lệ từ client.")

    except Exception as e:
        print(f"Lỗi khi xử lý kết nối: {e}")

    finally:
        conn.close()
def download_file(peer, info_hash, output_file):
    """Tải file từ Peer1"""
    host = peer["ip"]
    port = int(peer["port"])
    with open(output_file, 'wb') as file:
        for index in range(12):  # Giả sử file có 10 mảnh
            try:
                client_socket = socket.socket()
                client_socket.connect((host, port))
                request = {
                    "action": "download", 
                    "info_hash": info_hash, "index": index}
                client_socket.send(json.dumps(request).encode())
                data = client_socket.recv(1024)
                file.write(data)
                print(f"Tải mảnh {index} từ {host}:{port}")
                client_socket.close()
            except Exception as e:
                print(f"Lỗi khi tải mảnh {index}: {e}")
   


        

def server_program(host, port, file_path):
    """Khởi tạo server để lắng nghe kết nối"""
    serversocket = socket.socket()
    serversocket.bind((host, port))  # Lắng nghe trên host và port
    serversocket.listen(10)  # Tối đa 10 kết nối đồng thời

    print(f"Server peer2 listening on {host}:{port}")
    while True:
        conn, addr = serversocket.accept()  # Chấp nhận kết nối từ peers
        print(f"Connection from {addr}")  # In ra địa chỉ của peer kết nối
        nconn = Thread(target=new_connection, args=(conn,))  # Tạo luồng mới để xử lý kết nối
        nconn.start()  # Bắt đầu luồng mới

def get_tracker_info(file_info):
    """Lấy thông tin tracker từ file info.txt"""
    with open(file_info, 'r') as file:
        data = json.load(file)
        return data["urlTracker"]  # Đảm bảo trường urlTracker tồn tại


if __name__ == "__main__":
     #tạo file torrent
    peer2=Torrent()
    # thiết lập thông tin cho thằng peer2
    hostip = "127.0.0.1"  # Địa chỉ localhost
    port = 8082  # Port để server lắng nghe
    
    #set up các thiết lập cơ bản cho peer
    peer2.set_reacher_peer(hostip, port) 
    #thiết lập thông tin đến tracker để lấy file
    file_info = r"E:/p2p_file_sharing/info.txt"
    
    output_file = r"E:\p2p_file_sharing\received_file.txt"  # Tên file lưu sau khi tải về
   
    
    try:
        tracker_info = get_tracker_info(file_info)
        peer2.set_tracker(tracker_info)  # Thiết lập thông tin tracker
    except Exception as e:
        print(f"Lỗi khi đọc thông tin tracker: {e}")
        exit()
    # file_data = peer2.get_tracker()
    # if not file_data:
    #     print("Không thể lấy thông tin từ tracker.")
    #     exit()
    
    try:
        # gửi request đến tracker để lấy thông tin về các peers
        selected_peers = peer2.request_peers_from_tracker()
        if not selected_peers:
            print("Không có peers khả dụng để tải file!")
            exit()
         # Hiển thị danh sách các peers nhận được
        print(f"Danh sách các peers từ tracker: {selected_peers}")
        # Bắt đầu tải file
        
        peer2.download_file(output_file)
        print(f"File đã tải về thành công và lưu tại: {output_file}")

    except Exception as e:
        print(f"Lỗi: {e}")
        print("Không tìm thấy file!")
    # Chạy server để sẵn sàng gửi file cho peers khác
    print(f"Server Peer2 đang lắng nghe trên 127.0.0.1:8082...")
    server_program(hostip, port, output_file)
    
    
    # peer2.download_server(output_file="")  # Peer2 chạy server để hỗ trợ peers khác





# send_file(host, port, output_dir,sizepiece=1)