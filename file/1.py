import sys
import socket
import json
import threading
import time
import os
import math
from typing import List, Dict, Set

# ... (các class Tracker và Peer giữ nguyên) ...

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("Start tracker: python script.py tracker <port>")
        print("Share file: python script.py share <port> <file_path>")
        print("Download: python script.py download <port> <filename> <output_path>")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'tracker':
        if len(sys.argv) != 3:
            print("Usage: python script.py tracker <port>")
            sys.exit(1)
        tracker_port = int(sys.argv[2])
        tracker = Tracker('localhost', tracker_port)
        tracker.start()
        
    elif command == 'share':
        if len(sys.argv) != 4:
            print("Usage: python script.py share <port> <file_path>")
            sys.exit(1)
        peer_port = int(sys.argv[2])
        file_path = sys.argv[3]
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        
        if peer.share_file(file_path):
            print(f"Sharing {os.path.basename(file_path)} on port {peer_port}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping peer...")
            
    elif command == 'download':
        if len(sys.argv) != 5:
            print("Usage: python script.py download <port> <filename> <output_path>")
            sys.exit(1)
            
        peer_port = int(sys.argv[2])
        filename = sys.argv[3]
        output_path = sys.argv[4]
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        peer.download_file(filename, output_path)
        
        
        # p2p_system.py
import os
import json
import socket
import threading
import time
import math
from typing import List, Dict, Set

class Tracker:
    def __init__(self, host: str = 'localhost', port: int = 8000):
        self.host = host
        self.port = port
        self.shared_files = {}  # {filename: [(peer_ip, peer_port, file_size)]}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

    def start(self):
        print(f"Tracker running on {self.host}:{self.port}")
        while True:
            client, address = self.socket.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            response = self.process_request(request)
            client_socket.send(json.dumps(response).encode())
        finally:
            client_socket.close()

    def process_request(self, request: dict) -> dict:
        action = request.get('action')
        
        if action == 'share':
            filename = request['filename']
            file_size = request['file_size']
            peer_info = (request['ip'], request['port'], file_size)
            
            if filename not in self.shared_files:
                self.shared_files[filename] = []
            if peer_info not in self.shared_files[filename]:
                self.shared_files[filename].append(peer_info)
            
            print(f"\nNew peer sharing {filename}:")
            print(f"- {peer_info[0]}:{peer_info[1]}, size: {file_size} bytes")
            return {'status': 'success'}
            
        elif action == 'search':
            filename = request['filename']
            if filename in self.shared_files:
                print(f"\nPeers sharing {filename}:")
                for ip, port, size in self.shared_files[filename]:
                    print(f"- {ip}:{port}, size: {size} bytes")
                return {
                    'status': 'success',
                    'peers': self.shared_files[filename]
                }
            return {'status': 'error', 'message': 'File not found'}

class Peer:
    def __init__(self, host: str, port: int, tracker_host: str, tracker_port: int):
        self.host = host
        self.port = port
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.shared_files = {}  # {filename: file_path}
        self.chunk_size = 1024 * 1024  # 1MB chunks
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        threading.Thread(target=self.listen_for_peers).start()

    def share_file(self, file_path: str):
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        self.shared_files[filename] = file_path
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.tracker_host, self.tracker_port))
            request = {
                'action': 'share',
                'filename': filename,
                'file_size': file_size,
                'ip': self.host,
                'port': self.port
            }
            s.send(json.dumps(request).encode())
            response = json.loads(s.recv(1024).decode())
            return response['status'] == 'success'

    def download_file(self, filename: str, output_path: str, multi_peer: bool = False):
        """Download file with option for single or multi-peer download"""
        peers = self.search_file(filename)
        if not peers:
            print(f"File {filename} not found")
            return

        print(f"\nFound {len(peers)} peers sharing {filename}:")
        for i, (ip, port, size) in enumerate(peers):
            print(f"Peer {i+1}: {ip}:{port}")

        file_size = peers[0][2]
        # Create output file
        with open(output_path, 'wb') as f:
            f.seek(file_size - 1)
            f.write(b'\0')

        if not multi_peer or len(peers) == 1:
            # Single peer download
            print("\nDownloading from single peer...")
            peer_ip, peer_port, _ = peers[0]
            self.download_from_single_peer(peer_ip, peer_port, filename, output_path, file_size)
        else:
            # Multi-peer download
            print("\nDownloading from multiple peers...")
            num_chunks = math.ceil(file_size / self.chunk_size)
            peer_chunks = self.distribute_chunks(num_chunks, len(peers))
            
            threads = []
            for i, (peer_ip, peer_port, _) in enumerate(peers):
                start_chunk = sum(peer_chunks[:i])
                num_peer_chunks = peer_chunks[i]
                thread = threading.Thread(
                    target=self.download_chunks,
                    args=(peer_ip, peer_port, filename, output_path, start_chunk, num_peer_chunks)
                )
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
                
        print(f"\nDownloaded {filename} to {output_path}")

    def download_from_single_peer(self, peer_ip: str, peer_port: int, filename: str, output_path: str, file_size: int):
        """Download entire file from a single peer"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))
                request = {
                    'action': 'get_file',
                    'filename': filename
                }
                s.send(json.dumps(request).encode())
                
                with open(output_path, 'wb') as f:
                    received = 0
                    while received < file_size:
                        data = s.recv(8192)
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                        progress = (received / file_size) * 100
                        print(f"Progress: {progress:.1f}%", end='\r')
                print()
        except Exception as e:
            print(f"Error downloading from {peer_ip}:{peer_port}: {e}")

    def download_chunks(self, peer_ip: str, peer_port: int, filename: str, 
                       output_path: str, start_chunk: int, num_chunks: int):
        """Download specific chunks from a peer"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))
                
                for chunk_index in range(start_chunk, start_chunk + num_chunks):
                    request = {
                        'action': 'get_chunk',
                        'filename': filename,
                        'chunk_index': chunk_index
                    }
                    s.send(json.dumps(request).encode())
                    
                    chunk = b''
                    while len(chunk) < self.chunk_size:
                        data = s.recv(min(8192, self.chunk_size - len(chunk)))
                        if not data:
                            break
                        chunk += data
                    
                    with open(output_path, 'r+b') as f:
                        f.seek(chunk_index * self.chunk_size)
                        f.write(chunk)
                    
                    progress = ((chunk_index - start_chunk + 1) / num_chunks) * 100
                    print(f"Peer {peer_ip}:{peer_port} progress: {progress:.1f}%", end='\r')
                print()
                        
        except Exception as e:
            print(f"Error downloading from {peer_ip}:{peer_port}: {e}")

    def distribute_chunks(self, num_chunks: int, num_peers: int) -> List[int]:
        """Distribute chunks evenly among peers"""
        base_chunks = num_chunks // num_peers
        extra_chunks = num_chunks % num_peers
        
        distribution = [base_chunks] * num_peers
        for i in range(extra_chunks):
            distribution[i] += 1
            
        return distribution

    def search_file(self, filename: str) -> List[tuple]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.tracker_host, self.tracker_port))
            request = {
                'action': 'search',
                'filename': filename
            }
            s.send(json.dumps(request).encode())
            response = json.loads(s.recv(1024).decode())
            return response.get('peers', []) if response['status'] == 'success' else []

    def listen_for_peers(self):
        while True:
            client, address = self.socket.accept()
            threading.Thread(target=self.handle_peer_request, args=(client,)).start()

    def handle_peer_request(self, client_socket: socket.socket):
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            
            if request['action'] == 'get_file':
                filename = request['filename']
                if filename in self.shared_files:
                    with open(self.shared_files[filename], 'rb') as f:
                        while True:
                            data = f.read(8192)
                            if not data:
                                break
                            client_socket.send(data)
                            
            elif request['action'] == 'get_chunk':
                filename = request['filename']
                chunk_index = request['chunk_index']
                
                if filename in self.shared_files:
                    chunk = self.read_chunk(self.shared_files[filename], chunk_index)
                    client_socket.send(chunk)
        finally:
            client_socket.close()

    def read_chunk(self, file_path: str, chunk_index: int) -> bytes:
        with open(file_path, 'rb') as f:
            f.seek(chunk_index * self.chunk_size)
            return f.read(self.chunk_size)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("Start tracker: python script.py tracker <port>")
        print("Share file: python script.py share <port> <file_path>")
        print("Download file: python script.py download <port> <filename> <output_path> [--multi]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'tracker':
        if len(sys.argv) != 3:
            print("Usage: python script.py tracker <port>")
            sys.exit(1)
        tracker_port = int(sys.argv[2])
        tracker = Tracker('localhost', tracker_port)
        tracker.start()
        
    elif command == 'share':
        if len(sys.argv) != 4:
            print("Usage: python script.py share <port> <file_path>")
            sys.exit(1)
        peer_port = int(sys.argv[2])
        file_path = sys.argv[3]
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        
        if peer.share_file(file_path):
            print(f"Sharing {os.path.basename(file_path)} on port {peer_port}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping peer...")
            
    elif command == 'download':
        if len(sys.argv) < 5:
            print("Usage: python script.py download <port> <filename> <output_path> [--multi]")
            sys.exit(1)
            
        peer_port = int(sys.argv[2])
        filename = sys.argv[3]
        output_path = sys.argv[4]
        multi_peer = '--multi' in sys.argv
        
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        peer.download_file(filename, output_path, multi_peer)
        
        
        
        
        
        
        # Thêm vào đầu file
import hashlib
import bencodepy
import math
import json
import os

class TorrentFile:
    def __init__(self, piece_length: int = 1024 * 1024):  # 1MB pieces
        self.piece_length = piece_length
        self.pieces = []
        self.total_size = 0
        self.info_hash = None
        
    def create_from_file(self, file_path: str) -> dict:
        """Tạo torrent metadata từ file"""
        file_size = os.path.getsize(file_path)
        self.total_size = file_size
        num_pieces = math.ceil(file_size / self.piece_length)
        
        # Tính hash cho từng piece
        with open(file_path, 'rb') as f:
            for _ in range(num_pieces):
                piece = f.read(self.piece_length)
                piece_hash = hashlib.sha1(piece).digest()
                self.pieces.append(piece_hash)
        
        # Tạo torrent dict
        torrent_dict = {
            'created_by': 'Simple P2P',
            'creation_date': int(time.time()),
            'info': {
                'name': os.path.basename(file_path),
                'piece_length': self.piece_length,
                'pieces': b''.join(self.pieces),
                'length': file_size
            }
        }
        
        # Tính info hash
        self.info_hash = hashlib.sha1(bencodepy.encode(torrent_dict['info'])).hexdigest()
        return torrent_dict
    
    def save_torrent(self, torrent_dict: dict, output_path: str):
        """Lưu torrent file"""
        with open(output_path, 'wb') as f:
            f.write(bencodepy.encode(torrent_dict))
            
    def load_torrent(self, torrent_path: str) -> dict:
        """Đọc torrent file"""
        with open(torrent_path, 'rb') as f:
            torrent_dict = bencodepy.decode(f.read())
            self.info_hash = hashlib.sha1(bencodepy.encode(torrent_dict[b'info'])).hexdigest()
            return torrent_dict

class Peer:
    def create_torrent(self, file_path: str, output_path: str):
        """Tạo torrent file"""
        torrent = TorrentFile(piece_length=self.chunk_size)
        torrent_dict = torrent.create_from_file(file_path)
        torrent.save_torrent(torrent_dict, output_path)
        return torrent.info_hash

    def share_with_torrent(self, file_path: str, torrent_path: str):
        """Share file với torrent"""
        torrent = TorrentFile()
        torrent_dict = torrent.load_torrent(torrent_path)
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        self.shared_files[filename] = {
            'path': file_path,
            'torrent': torrent_dict,
            'info_hash': torrent.info_hash
        }
        
        # Announce to tracker
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.tracker_host, self.tracker_port))
            request = {
                'action': 'share',
                'filename': filename,
                'file_size': file_size,
                'info_hash': torrent.info_hash,
                'ip': self.host,
                'port': self.port
            }
            s.send(json.dumps(request).encode())
            response = json.loads(s.recv(1024).decode())
            return response['status'] == 'success'

# Sửa lại main để thêm các lệnh torrent
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("Start tracker: python script.py tracker <port>")
        print("Create torrent: python script.py create-torrent <file_path> <torrent_path>") 
        print("Share with torrent: python script.py share <port> <file_path> <torrent_path>")
        print("Share without torrent: python script.py share <port> <file_path>")
        print("Download: python script.py download <port> <filename> <output_path> [--multi]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'create-torrent':
        if len(sys.argv) != 4:
            print("Usage: python script.py create-torrent <file_path> <torrent_path>")
            sys.exit(1)
        file_path = sys.argv[2]
        torrent_path = sys.argv[3]
        peer = Peer('localhost', 0, 'localhost', 8000)
        info_hash = peer.create_torrent(file_path, torrent_path)
        print(f"Created torrent with info hash: {info_hash}")
        
    elif command == 'share':
        if len(sys.argv) not in [4, 5]:
            print("Usage: python script.py share <port> <file_path> [<torrent_path>]")
            sys.exit(1)
            
        peer_port = int(sys.argv[2])
        file_path = sys.argv[3]
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        
        if len(sys.argv) == 5:
            # Share with torrent
            torrent_path = sys.argv[4]
            if peer.share_with_torrent(file_path, torrent_path):
                print(f"Sharing {os.path.basename(file_path)} with torrent on port {peer_port}")
        else:
            # Share without torrent
            if peer.share_file(file_path):
                print(f"Sharing {os.path.basename(file_path)} on port {peer_port}")
                
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping peer...")
            
            
            
            
            
            
            333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333
            
            
            import os
import hashlib
import bencodepy
import json
import socket
import threading
import time
import math
from typing import List, Dict, Set

class TorrentFile:
    def __init__(self, piece_length: int = 1024 * 1024):  # 1MB pieces
        self.piece_length = piece_length
        self.pieces = []
        self.total_size = 0
        self.info_hash = None
        
    def create_from_file(self, file_path: str) -> dict:
        file_size = os.path.getsize(file_path)
        self.total_size = file_size
        num_pieces = math.ceil(file_size / self.piece_length)
        
        with open(file_path, 'rb') as f:
            for _ in range(num_pieces):
                piece = f.read(self.piece_length)
                piece_hash = hashlib.sha1(piece).digest()
                self.pieces.append(piece_hash)
        
        torrent_dict = {
            'created_by': 'Simple P2P',
            'creation_date': int(time.time()),
            'info': {
                'name': os.path.basename(file_path),
                'piece_length': self.piece_length,
                'pieces': b''.join(self.pieces),
                'length': file_size
            }
        }
        
        self.info_hash = hashlib.sha1(bencodepy.encode(torrent_dict['info'])).hexdigest()
        return torrent_dict
    
    def save_torrent(self, torrent_dict: dict, output_path: str):
        with open(output_path, 'wb') as f:
            f.write(bencodepy.encode(torrent_dict))
            
    def load_torrent(self, torrent_path: str) -> dict:
        with open(torrent_path, 'rb') as f:
            torrent_dict = bencodepy.decode(f.read())
            self.info_hash = hashlib.sha1(bencodepy.encode(torrent_dict[b'info'])).hexdigest()
            return torrent_dict

class Tracker:
    def __init__(self, host: str = 'localhost', port: int = 8000):
        self.host = host
        self.port = port
        self.shared_files = {}  # {filename: [(peer_ip, peer_port, file_size, info_hash)]}
        self.peers_by_hash = {}  # {info_hash: [(peer_ip, peer_port)]}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

    def start(self):
        print(f"Tracker running on {self.host}:{self.port}")
        while True:
            client, address = self.socket.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            response = self.process_request(request)
            client_socket.send(json.dumps(response).encode())
        finally:
            client_socket.close()

    def process_request(self, request: dict) -> dict:
        action = request.get('action')
        
        if action == 'share':
            filename = request['filename']
            file_size = request['file_size']
            info_hash = request.get('info_hash')
            peer_info = (request['ip'], request['port'], file_size, info_hash)
            
            if filename not in self.shared_files:
                self.shared_files[filename] = []
            if peer_info not in self.shared_files[filename]:
                self.shared_files[filename].append(peer_info)
                
            if info_hash:
                if info_hash not in self.peers_by_hash:
                    self.peers_by_hash[info_hash] = []
                peer_tuple = (request['ip'], request['port'])
                if peer_tuple not in self.peers_by_hash[info_hash]:
                    self.peers_by_hash[info_hash].append(peer_tuple)
            
            print(f"\nNew peer sharing {filename}:")
            print(f"- {peer_info[0]}:{peer_info[1]}, size: {file_size} bytes")
            if info_hash:
                print(f"- Info hash: {info_hash}")
            return {'status': 'success'}
            
        elif action == 'search':
            filename = request['filename']
            info_hash = request.get('info_hash')
            
            if info_hash and info_hash in self.peers_by_hash:
                peers = [(ip, port, 0, info_hash) for ip, port in self.peers_by_hash[info_hash]]
                print(f"\nPeers sharing torrent {info_hash}:")
                for ip, port, _, _ in peers:
                    print(f"- {ip}:{port}")
                return {
                    'status': 'success',
                    'peers': peers
                }
            elif filename in self.shared_files:
                print(f"\nPeers sharing {filename}:")
                for ip, port, size, hash in self.shared_files[filename]:
                    print(f"- {ip}:{port}, size: {size} bytes")
                    if hash:
                        print(f"  Info hash: {hash}")
                return {
                    'status': 'success',
                    'peers': self.shared_files[filename]
                }
            return {'status': 'error', 'message': 'File not found'}

class Peer:
    def __init__(self, host: str, port: int, tracker_host: str, tracker_port: int):
        self.host = host
        self.port = port
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.shared_files = {}  # {filename: {path, torrent, info_hash}}
        self.chunk_size = 1024 * 1024  # 1MB chunks
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        
        threading.Thread(target=self.listen_for_peers).start()

    def create_torrent(self, file_path: str, output_path: str):
        """Create a torrent file"""
        torrent = TorrentFile(piece_length=self.chunk_size)
        torrent_dict = torrent.create_from_file(file_path)
        torrent.save_torrent(torrent_dict, output_path)
        return torrent.info_hash

    def share_file(self, file_path: str, torrent_path: str = None):
        """Share file with optional torrent"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        info_hash = None
        
        if torrent_path:
            torrent = TorrentFile()
            torrent_dict = torrent.load_torrent(torrent_path)
            info_hash = torrent.info_hash
            self.shared_files[filename] = {
                'path': file_path,
                'torrent': torrent_dict,
                'info_hash': info_hash
            }
        else:
            self.shared_files[filename] = {
                'path': file_path,
                'torrent': None,
                'info_hash': None
            }
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.tracker_host, self.tracker_port))
            request = {
                'action': 'share',
                'filename': filename,
                'file_size': file_size,
                'info_hash': info_hash,
                'ip': self.host,
                'port': self.port
            }
            s.send(json.dumps(request).encode())
            response = json.loads(s.recv(1024).decode())
            return response['status'] == 'success'

    def download_file(self, filename: str, output_path: str, multi_peer: bool = False, info_hash: str = None):
        """Download file with options for single/multi peer and torrent"""
        # Search by info_hash if provided, otherwise by filename
        peers = self.search_file(filename, info_hash)
        if not peers:
            print(f"File {filename} not found")
            return

        print(f"\nFound {len(peers)} peers sharing {filename}:")
        for i, (ip, port, size, hash) in enumerate(peers):
            print(f"Peer {i+1}: {ip}:{port}")
            if hash:
                print(f"Info hash: {hash}")

        file_size = peers[0][2] if peers[0][2] > 0 else None  # Size might be 0 for torrent peers
        
        # Create output file
        if file_size:
            with open(output_path, 'wb') as f:
                f.seek(file_size - 1)
                f.write(b'\0')

        if not multi_peer or len(peers) == 1:
            # Single peer download
            print("\nDownloading from single peer...")
            peer_ip, peer_port, _, _ = peers[0]
            self.download_from_single_peer(peer_ip, peer_port, filename, output_path, file_size)
        else:
            # Multi-peer download
            print("\nDownloading from multiple peers...")
            if not file_size:
                print("Error: File size unknown for multi-peer download")
                return
                
            num_chunks = math.ceil(file_size / self.chunk_size)
            peer_chunks = self.distribute_chunks(num_chunks, len(peers))
            
            threads = []
            for i, (peer_ip, peer_port, _, _) in enumerate(peers):
                start_chunk = sum(peer_chunks[:i])
                num_peer_chunks = peer_chunks[i]
                thread = threading.Thread(
                    target=self.download_chunks,
                    args=(peer_ip, peer_port, filename, output_path, start_chunk, num_peer_chunks)
                )
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
                
        print(f"\nDownloaded {filename} to {output_path}")

    def download_from_single_peer(self, peer_ip: str, peer_port: int, filename: str, output_path: str, file_size: int = None):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))
                request = {
                    'action': 'get_file',
                    'filename': filename
                }
                s.send(json.dumps(request).encode())
                
                with open(output_path, 'wb') as f:
                    received = 0
                    while True:
                        data = s.recv(8192)
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                        if file_size:
                            progress = (received / file_size) * 100
                            print(f"Progress: {progress:.1f}%", end='\r')
                print()
        except Exception as e:
            print(f"Error downloading from {peer_ip}:{peer_port}: {e}")

    def download_chunks(self, peer_ip: str, peer_port: int, filename: str, 
                       output_path: str, start_chunk: int, num_chunks: int):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((peer_ip, peer_port))
                
                for chunk_index in range(start_chunk, start_chunk + num_chunks):
                    request = {
                        'action': 'get_chunk',
                        'filename': filename,
                        'chunk_index': chunk_index
                    }
                    s.send(json.dumps(request).encode())
                    
                    chunk = b''
                    while len(chunk) < self.chunk_size:
                        data = s.recv(min(8192, self.chunk_size - len(chunk)))
                        if not data:
                            break
                        chunk += data
                    
                    with open(output_path, 'r+b') as f:
                        f.seek(chunk_index * self.chunk_size)
                        f.write(chunk)
                    
                    progress = ((chunk_index - start_chunk + 1) / num_chunks) * 100
                    print(f"Peer {peer_ip}:{peer_port} progress: {progress:.1f}%", end='\r')
                print()
                        
        except Exception as e:
            print(f"Error downloading from {peer_ip}:{peer_port}: {e}")

    def distribute_chunks(self, num_chunks: int, num_peers: int) -> List[int]:
        base_chunks = num_chunks // num_peers
        extra_chunks = num_chunks % num_peers
        
        distribution = [base_chunks] * num_peers
        for i in range(extra_chunks):
            distribution[i] += 1
            
        return distribution

    def search_file(self, filename: str, info_hash: str = None) -> List[tuple]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.tracker_host, self.tracker_port))
            request = {
                'action': 'search',
                'filename': filename,
                'info_hash': info_hash
            }
            s.send(json.dumps(request).encode())
            response = json.loads(s.recv(1024).decode())
            return response.get('peers', []) if response['status'] == 'success' else []

    def listen_for_peers(self):
        while True:
            client, address = self.socket.accept()
            threading.Thread(target=self.handle_peer_request, args=(client,)).start()

    def handle_peer_request(self, client_socket: socket.socket):
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            
            if request['action'] == 'get_file':
                filename = request['filename']
                if filename in self.shared_files:
                    file_path = self.shared_files[filename]['path']
                    with open(file_path, 'rb') as f:
                        while True:
                            data = f.read(8192)
                            if not data:
                                break
                            client_socket.send(data)
                            
            elif request['action'] == 'get_chunk':
                filename = request['filename']
                chunk_index = request['chunk_index']
                
                if filename in self.shared_files:
                    file_path = self.shared_files[filename]['path']
                    chunk = self.read_chunk(file_path, chunk_index)
                    client_socket.send(chunk)
        finally:
            client_socket.close()

    def read_chunk(self, file_path: str, chunk_index: int) -> bytes:
        with open(file_path
                  
                  
                  
                  def handle_peer_request(self, client_socket: socket.socket):
        """Xử lý requests từ peers khác"""
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            
            if request['action'] == 'get_file':
                filename = request['filename']
                if filename in self.shared_files:
                    file_path = self.shared_files[filename]['path']
                    with open(file_path, 'rb') as f:
                        while True:
                            data = f.read(8192)
                            if not data:
                                break
                            client_socket.send(data)
                            
            elif request['action'] == 'get_chunk':
                filename = request['filename']
                chunk_index = request['chunk_index']
                
                if filename in self.shared_files:
                    file_path = self.shared_files[filename]['path']
                    chunk = self.read_chunk(file_path, chunk_index)
                    client_socket.send(chunk)
        finally:
            client_socket.close()

    def read_chunk(self, file_path: str, chunk_index: int) -> bytes:
        """Đọc một chunk từ file"""
        with open(file_path, 'rb') as f:
            f.seek(chunk_index * self.chunk_size)
            return f.read(self.chunk_size)

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("1. Start tracker:")
        print("   python script.py tracker <port>")
        print("2. Create torrent:")
        print("   python script.py create-torrent <file_path> <torrent_path>")
        print("3. Share file:")
        print("   Without torrent: python script.py share <port> <file_path>")
        print("   With torrent: python script.py share <port> <file_path> <torrent_path>")
        print("4. Download file:")
        print("   Single peer: python script.py download <port> <filename> <output_path>")
        print("   Multiple peers: python script.py download <port> <filename> <output_path> --multi")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'tracker':
        if len(sys.argv) != 3:
            print("Usage: python script.py tracker <port>")
            sys.exit(1)
        tracker_port = int(sys.argv[2])
        tracker = Tracker('localhost', tracker_port)
        print(f"Starting tracker on port {tracker_port}...")
        tracker.start()
        
    elif command == 'create-torrent':
        if len(sys.argv) != 4:
            print("Usage: python script.py create-torrent <file_path> <torrent_path>")
            sys.exit(1)
        file_path = sys.argv[2]
        torrent_path = sys.argv[3]
        peer = Peer('localhost', 0, 'localhost', 8000)
        info_hash = peer.create_torrent(file_path, torrent_path)
        print(f"Created torrent with info hash: {info_hash}")
        print(f"Torrent file saved to: {torrent_path}")
        
    elif command == 'share':
        if len(sys.argv) not in [4, 5]:
            print("Usage: python script.py share <port> <file_path> [<torrent_path>]")
            sys.exit(1)
            
        peer_port = int(sys.argv[2])
        file_path = sys.argv[3]
        torrent_path = sys.argv[4] if len(sys.argv) == 5 else None
        
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        filename = os.path.basename(file_path)
        
        if peer.share_file(file_path, torrent_path):
            print(f"Sharing {filename} on port {peer_port}")
            if torrent_path:
                print(f"Using torrent: {torrent_path}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping peer...")
            
    elif command == 'download':
        if len(sys.argv) < 5:
            print("Usage: python script.py download <port> <filename> <output_path> [--multi]")
            sys.exit(1)
            
        peer_port = int(sys.argv[2])
        filename = sys.argv[3]
        output_path = sys.argv[4]
        multi_peer = '--multi' in sys.argv
        
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        peer.download_file(filename, output_path, multi_peer)

if __name__ == '__main__':
    main()