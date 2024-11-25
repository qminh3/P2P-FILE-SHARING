import socket
import os
import json
from threading import Thread
from torrent import Torrent
import base64
import bencodepy
PIECE_LENGTH = 1 # Chỉnh lại chiều dài mảnh file
output_file = r'E:\p2p_file_sharing\received_file.txt'

def new_connection(conn, file_path,output_file):
    """Xử lý kết nối từ một peer mới"""
    try:
        request = conn.recv(1024).decode('utf-8')
        request = json.loads(request)

        # Xử lý yêu cầu tải file
        if request["action"] == "sendFile":
            index = int(request.get("index", 0))  # Lấy mảnh file cần tải
            with open(file_path, 'rb') as file:
                file.seek(index * PIECE_LENGTH)  # Đọc từ vị trí của mảnh
                data = file.read(PIECE_LENGTH)  # Đọc đúng kích thước mảnh
            if data:
                try:
                    encoded_data = base64.b64encode(data).decode('utf-8')  # Chuyển đổi dữ liệu nhị phân thành chuỗi base64
                    # Kết nối tới peer để gửi mảnh
                    peer_id_action = request.get("peer_id_action", {})
                    ip = peer_id_action["ip"]
                    port = peer_id_action["port"]
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                        print(f"Kết nối tới peer {ip}:{port} để gửi piece {index}")
                        client.connect((ip, int(port)))

                        # Gửi yêu cầu nhận mảnh file
                        request = {
                            "action": "download",
                            "index": index,
                            "data":encoded_data
                        }
                        client.send(json.dumps(request).encode())
                        

                except Exception as e:
                    print(f"Lỗi khi gửi piece {index}: {e}")

                print(f"Đã gửi mảnh {index} của file.")
            else:
                print("Không có dữ liệu để gửi.")
                # Không cần tạo client nếu không có dữ liệu
                conn.send(json.dumps({"error": "No data available"}).encode())

        elif request["action"] == "download":
            # Nhận dữ liệu mảnh
            encoded_data = request.get("data")
            decoded_data = base64.b64decode(encoded_data)
            if decoded_data:
                index = int(request.get("index", 0))
                offset = index * PIECE_LENGTH  # Mỗi mảnh có độ dài bằng piece_length

                # Mở file và ghi dữ liệu tại đúng vị trí
                with open(output_file, 'r+b') as file:  # Mở file ở chế độ đọc và ghi nhị phân
                    file.seek(offset)  # Di chuyển đến vị trí đúng của mảnh trong file
                    file.write(decoded_data)  # Ghi dữ liệu vào vị trí đó

                print(f"Đã ghi mảnh {index} vào vị trí {offset} trong file.")
            else:
                print("Không nhận được dữ liệu cho mảnh.")

        else:
            print("Yêu cầu không hợp lệ từ peer.")
            conn.send(json.dumps({"error": "Invalid action"}).encode())

    except Exception as e:
        print(f"Lỗi khi xử lý kết nối: {e}")
    finally:
        conn.close()


def server_program(host, port, file_path,output_file):
    """Khởi tạo server để lắng nghe kết nối"""
    try:
        serversocket = socket.socket()
        serversocket.bind((host, port))  # Lắng nghe trên host và port
        serversocket.listen(10)  # Tối đa 10 kết nối đồng thời
        print(f"Server listening on {host}:{port}")
        
        while True:
            conn, addr = serversocket.accept()  # Chấp nhận kết nối từ peers
            print(f"Connection from {addr}")  # In ra địa chỉ của peer kết nối
            thread = Thread(target=new_connection, args=(conn, file_path,output_file))  # Tạo luồng mới để xử lý kết nối
            thread.start()  # Bắt đầu luồng mới
    except Exception as e:
        print(f"Lỗi server: {e}")

if __name__ == "__main__":       
    host = "127.0.0.1"  
    port = 12345      
    hostip = "127.0.0.1" 

    # Thiết lập torrent cho peer1
    peer1 = Torrent()
    
    file_path = r"E:\p2p_file_sharing\port.txt"
    file_info = r"E:\p2p_file_sharing\info.txt"
    output_file = "E:/p2p_file_sharing/received_file.txt"

    # Option 1 -> peer1 tải file lên 
    peer1.set_reacher_peer(host, port)
    peer1.set_tracker({"ip": "127.0.0.1", "port": 8080})
    response = peer1.upload_file(file_path, file_info)
    print(f"Peer1 info_hash: {peer1.info_hash}")

    if response:
        print("Peer1 đã upload file lên tracker:")
        print(response)
        print("Peer1 sẵn sàng gửi file.")
        server_program(hostip, port, file_path,output_file)
    else:
        print("Không thể kết nối tới tracker hoặc đã xảy ra lỗi.")