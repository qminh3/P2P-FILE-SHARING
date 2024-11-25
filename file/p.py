# peer.py
import socket
import json
import threading
import time
import os
import math
from typing import List
from torrent import TorrentFile

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

    def download_file(self, filename: str, output_path: str, multi_peer: bool = False):
        """Download file with options for single/multi peer"""
        peers = self.search_file(filename)
        if not peers:
            print(f"File {filename} not found")
            return

        print(f"\nFound {len(peers)} peers sharing {filename}:")
        for i, (ip, port, size, hash) in enumerate(peers):
            print(f"Peer {i+1}: {ip}:{port}")
            if hash:
                print(f"Info hash: {hash}")

        file_size = peers[0][2] if peers[0][2] > 0 else None
        
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
        """Download từ một peer"""
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
        """Download chunks từ một peer"""
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
        """Phân phối chunks cho các peers"""
        base_chunks = num_chunks // num_peers
        extra_chunks = num_chunks % num_peers
        
        distribution = [base_chunks] * num_peers
        for i in range(extra_chunks):
            distribution[i] += 1
            
        return distribution

    def search_file(self, filename: str, info_hash: str = None) -> List[tuple]:
        """Search file from tracker"""
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

    def listen_for_peers(self):
        """Lắng nghe kết nối từ các peers khác"""
        while True:
            client, address = self.socket.accept()
            threading.Thread(target=self.handle_peer_request, args=(client,)).start()
    
    def read_chunk(self, file_path: str, chunk_index: int) -> bytes:
        """Đọc một chunk từ file"""
        with open(file_path, 'rb') as f:
            f.seek(chunk_index * self.chunk_size)
            return f.read(self.chunk_size)