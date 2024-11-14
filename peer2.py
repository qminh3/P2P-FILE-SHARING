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
    # thiết lập thông tin cho thằng peer2
    hostip = "127.0.0.1"  # Địa chỉ localhost
    port = 8082  # Port để server lắng nghe
    
    #tạo file torrent
    peer2=Torrent()
    
    #set up các thiết lập cơ bản cho peer2
    
    peer2.set_reacher_peer(hostip, port)  # IP và Port của Peer2
    peer2.set_option(1)  # Option 1: Peer2 chỉ nhận dữ liệu
    
    #thiết lập thông tin đến tracker để lấy file
    
    file_info='info.txt'
    file_data = peer2.get_tracker()
    peer2.info_hash = peer2.get_tracker()  # Lấy thông tin tracker từ file info
    
    
    try:
        # gửi request đến tracker để lấy thông tin về các peers
        selected_peers = peer2.request_peers_from_tracker()
        if not selected_peers:
            print("Không có peers khả dụng để tải file!")
            exit()
         # Hiển thị danh sách các peers nhận được
        print(f"Danh sách các peers từ tracker: {selected_peers}")
        # Bắt đầu tải file
        output_file = "E:\p2p_file_sharing\received_file.txt"  # Tên file lưu sau khi tải về
        peer2.download_file(output_file)
        print(f"File đã tải về thành công và lưu tại: {output_file}")

    except Exception as e:
        print(f"Lỗi: {e}")
        print("Không tìm thấy file!")
    
    
    # Chạy server để sẵn sàng gửi file cho peers khác
    print(f"Server Peer2 đang lắng nghe trên 127.0.0.1:8082...")
    peer2.download_server(output_file="")  # Peer2 chạy server để hỗ trợ peers khác





# send_file(host, port, output_dir,sizepiece=1)