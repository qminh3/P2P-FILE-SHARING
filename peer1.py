# Sử dụng hàm
import socket
import os
import json
from torrent import Torrent
from threading import Thread

PIECE_LENGTH = 1024
# piece_length=1
output_file = r'E:\p2p_file_sharing\received_file.txt'
def new_connection(conn, file_path):
    """Xử lý kết nối từ một peer mới"""
    try:
        request = conn.recv(1024).decode('utf-8')
        request = json.loads(request)

        # Xử lý yêu cầu tải file
        if request["action"] == "download":
            index = int(request["index"])  # Lấy mảnh file cần tải
            with open(file_path, 'rb') as file:
                file.seek(index * PIECE_LENGTH)  # Đọc từ vị trí của mảnh
                data = file.read(PIECE_LENGTH)  # Đọc đúng kích thước mảnh

            conn.send(data)  # Gửi dữ liệu mảnh file
            print(f"Đã gửi mảnh {index} của file.")
        else:
            print("Yêu cầu không hợp lệ từ peer.")
            conn.send(json.dumps({"error": "Invalid action"}).encode())

    except Exception as e:
        print(f"Lỗi khi xử lý kết nối: {e}")

    finally:
        conn.close()

def server_program(host, port,file_path):
    """Khởi tạo server để lắng nghe kết nối"""
    serversocket = socket.socket()
    serversocket.bind((host, port))  # Lắng nghe trên host và port
    serversocket.listen(10)  # Tối đa 10 kết nối đồng thời
    print(f"Server listening on {host}:{port}")\
        
    while True:
        conn, addr = serversocket.accept()  # Chấp nhận kết nối từ peers
        print(f"Connection from {addr}")  # In ra địa chỉ của peer kết nối
        nconn = Thread(target=new_connection, args=(conn,))  # Tạo luồng mới để xử lý kết nối
        nconn.start()  # Bắt đầu luồng mới


if __name__ == "__main__":       
    host = "127.0.0.1"  # Use localhost; can be changed to server IP if running on multiple machines
    port = 12345      # Port for the server to listen on
    hostip = "127.0.0.1" # Server IP

    
     #thiết lập torrent cho peer1
    peer1=Torrent()
    
     # File path to save received data
    file_path = r"E:/p2p_file_sharing/port.txt" # File path to
    file_info=r"E:\p2p_file_sharing\info.txt"
    #option 1 -> peer1 tải file lên 
     # Đăng ký file với tracker
    peer1.set_reacher_peer(host,port)
    response = peer1.upload_file(file_path, file_info)
    
    #kiểm tra phản hồi từ thằng tracker
    if response:
        print("Peer1 đã upload file lên tracker:")
        print(response)
    else:
        print("Không thể kết nối tới tracker hoặc đã xảy ra lỗi.")
        
    # khi đó ta chạy server của peer1 để gửi file khi peer2 trả về yêu cầu tải
    print("Peer1 sẵn sàng gửi file.")
    server_program(hostip, port,file_path)
    # peer1.download_server(output_file="")  # Peer1 sẽ gửi dữ liệu khi có yêu cầu    
    # torrent.download_server(output_file=output_file)
    print("Server đang chạy.")
    print("Peer1 đã upload file lên tracker và sẵn sàng gửi dữ liệu")
    