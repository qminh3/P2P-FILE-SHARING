# tracker.py
import socket
import json
import threading
from typing import Dict, List, Set

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
        """Xử lý yêu cầu từ client"""
        try:
            data = client_socket.recv(1024).decode()
            request = json.loads(data)
            response = self.process_request(request)
            client_socket.send(json.dumps(response).encode())
        finally:
            client_socket.close()

    def process_request(self, request: dict) -> dict:
        """Xử lý các loại request từ client"""
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