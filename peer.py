import socket
import os
import json
from threading import Thread
from torrent import Torrent
import base64
import bencodepy
PIECE_LENGTH = 1 # Chỉnh lại chiều dài mảnh file
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
    print("Chọn chế độ (1: Upload, 2: Download): ", end="")
    mode = int(input())
    print("Nhập port cho peer server: ", end="")
    port = int(input())
    host = "127.0.0.1"
    peer = Torrent()
    peer.set_reacher_peer(host, port)
    peer.set_tracker({"ip": "127.0.0.1", "port": 8080})

    if mode == 1:
        print("Nhập đường dẫn file để upload: ", end="")
        file_path = input()
        # print("Nhập đường dẫn file info (metadata): ", end="")
        # file_info = input()
        output_file = "uploaded_" + os.path.basename(file_path)  # Tạo tên file output mặc định
        response = peer.upload_file(file_path)
        if response:
            print(f"File đã được upload: {response}")
        server_program(host, port, file_path,output_file)
        # Thread(target=server_program, args=(host, port, file_path,output_file)).start()
    elif mode == 2:
        # Đường dẫn thư mục Result
        result_folder = "Result"
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)  # Tạo thư mục nếu chưa tồn tại
        print("Nhập tên của file cần tải: ", end="")
        file_name = input()
        print("Nhập piece_length: ", end="")
        piece_length = int(input())
        print("Nhập tên file để lưu: ", end="")
        output_file_name = input()
        output_file = os.path.join(result_folder, output_file_name)  # Lưu file vào thư mục Result
        file_path = "uploaded_" + os.path.basename(output_file_name)  # Tạo  file_path mặc định
        # Chọn phương thức tải file 
        print("Chọn phương thức tải file:")
        print("1. Tải file từ một peer")
        print("2. Tải file từ nhiều peers")
        print("Nhập lựa chọn (1/2): ", end="")
        download_method = int(input())
        if download_method == 1 :
                    # Tải file từ 1 peer
                    if peer.download_file(file_name, piece_length, output_file):
                        print(f"File đã tải về thành công tại: {output_file}")
                    else:
                        print("Không thể tải file. Đảm bảo rằng các peers đã đăng ký file này.")
        elif download_method == 2:
                    # Tải từ nhiều peers
                    if peer.download_file_from_multiple_peers(file_name, piece_length, output_file):
                        print(f"File đã tải về thành công tại: {output_file}")
                    else:
                        print("Không thể tải file từ nhiều peers.")
        
            
            
    server_program(host, port, file_path,output_file)
        
        
        