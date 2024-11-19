import socket
import hashlib
import bencodepy
from torrent import Torrent
import time

# Đường dẫn để lưu file tải về
output_file = "E:/p2p_file_sharing/received_file.txt"

# Thông tin địa chỉ Peer2
hostip = "127.0.0.1"
port = 8082

if __name__ == "__main__":
    try:
        # Khởi tạo đối tượng Torrent cho Peer2
        peer2 = Torrent()
    
        # Thiết lập địa chỉ và tracker
        peer2.set_reacher_peer(hostip, port)
        peer2.set_tracker({"ip": "127.0.0.1", "port": 8080})
        
        # Yêu cầu danh sách các Peer từ tracker
        # print("Peer2 gửi yêu cầu danh sách peers...")
        info = {
            "file_name": "port.txt",
            "piece_length": 1
        }
        peer2.info = info
        peer2.info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()
        # print(f"Peer2 info_hash thiết lập: {peer2.info_hash}")

       

        # print("Bắt đầu tải file...")
        peer2.download_file(output_file)
        # print(f"File đã tải về thành công tại: {output_file}")
        
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {str(e)}")