# Sử dụng hàm
import socket
import os
import json
from torrent import Torrent
import Thread


piece_length=1
output_file = r'E:\p2p_file_sharing\received_file.txt'
def new_connection(conn):
    """Xử lý kết nối từ một peer mới"""
    content=""
    with open(file_path, 'r') as file:
        content = file.read()
    with open(output_file, 'wb') as file_data:
        request = conn.recv(1024).decode('utf-8')
        request = json.loads(request)
        index=int(request["index"])
        data=request["data"]
        modified_content = content[:index] + data + content[index:]
        file_data.write(modified_content)
    
    conn.close()  # Close the client connection
      # Close the server socket

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
    host = "127.0.0.1"  # Use localhost; can be changed to server IP if running on multiple machines
    port = '12345'       # Port for the server to listen on
    hostip = "127.0.0.1" # Server IP

    
     #thiết lập torrent cho peer1
    peer1=Torrent()
    
     # File path to save received data
    file_path = 'E:\p2p_file_sharing\port.txt' # File path to
    file_info="E:\p2p_file_sharing\info.txt"
    # torrent = Torrent()
    #option 1 -> peer1 tải file lên 
    peer1.set_option(1)
    peer1.set_reacher_peer(host,port)
    
    
    # Đăng ký file với tracker
    response=peer1.upload_file(file_path, file_info)
    
    #kiểm tra phản hồi từ thằng tracker
    if response:
        print("Peer1 đã upload file lên tracker:")
        print(response)
    else:
        print("Không thể kết nối tới tracker hoặc đã xảy ra lỗi.")
        
    # khi đó ta chạy server của peer1 để gửi file khi peer2 trả về yêu cầu tải
    print("Peer1 sẵn sàng gửi file.")
    peer1.download_server(output_file="")  # Peer1 sẽ gửi dữ liệu khi có yêu cầu    
    # torrent.download_server(output_file=output_file)
    server_program(hostip, port)
    print("Server đang chạy.")
    print("Peer1 đã upload file lên tracker và sẵn sàng gửi dữ liệu")
    