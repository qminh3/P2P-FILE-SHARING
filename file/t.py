# torrent.py
import os
import hashlib
import bencodepy
import time

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
        """Lưu torrent file"""
        with open(output_path, 'wb') as f:
            f.write(bencodepy.encode(torrent_dict))
            
    def load_torrent(self, torrent_path: str) -> dict:
        """Load torrent file"""
        with open(torrent_path, 'rb') as f:
            torrent_dict = bencodepy.decode(f.read())
            self.info_hash = hashlib.sha1(bencodepy.encode(torrent_dict[b'info'])).hexdigest()
            return torrent_dict