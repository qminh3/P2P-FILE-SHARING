import socket
import os
import json
from torrent import Torrent
from threading import Thread

    # Kiểm tra nếu thư mục đầu ra không tồn tại thì tạo mới
file_folder = 'E:\p2p_file_sharing'   
def new_connection(conn):
    """Xử lý kết nối từ một peer mới"""
    
        # Ch�� nhận file từ client
    data = conn.recv(1024).decode()
    request = json.loads(data)
    torrent = Torrent()
    torrent.send_file(request, file_folder)

        

def server_program(host, port):
    """Khởi tạo server để lắng nghe kết nối"""
    serversocket = socket.socket()
    serversocket.bind((host, port))  # Lắng nghe trên host và port
    serversocket.listen(10)  # Tối đa 10 kết nối đồng thời

    print(f"Server listening on {host}:{port}")
    while True:
        conn, addr = serversocket.accept()  # Chấp nhận kết nối từ client
        print(f"Connection from {addr}")  # In ra địa chỉ của peer kết nối
        nconn = Thread(target=new_connection, args=(conn,))  # Tạo luồng mới để xử lý kết nối
        nconn.start()  # Bắt đầu luồng mới




if __name__ == "__main__":
    hostip = "127.0.0.1"  # Địa chỉ localhost
    port = 8080  # Port để server lắng nghe
    server_program(hostip, port)  # Khởi tạo server
      # Đặt đường dẫn tới file cần chia





send_file(host, port, output_dir,sizepiece=1)