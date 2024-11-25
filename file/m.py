# main.py
import sys
import time
from tracker import Tracker
from peer import Peer

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("1. Start tracker:")
        print("   python main.py tracker <port>")
        print("2. Create torrent:")
        print("   python main.py create-torrent <file_path> <torrent_path>")
        print("3. Share file:")
        print("   Without torrent: python main.py share <port> <file_path>")
        print("   With torrent: python main.py share <port> <file_path> <torrent_path>")
        print("4. Download file:")
        print("   Single peer: python main.py download <port> <filename> <output_path>")
        print("   Multiple peers: python main.py download <port> <filename> <output_path> --multi")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'tracker':
        if len(sys.argv) != 3:
            print("Usage: python main.py tracker <port>")
            sys.exit(1)
        tracker_port = int(sys.argv[2])
        tracker = Tracker('localhost', tracker_port)
        print(f"Starting tracker on port {tracker_port}...")
        tracker.start()
        
    elif command == 'create-torrent':
        if len(sys.argv) != 4:
            print("Usage: python main.py create-torrent <file_path> <torrent_path>")
            sys.exit(1)
        file_path = sys.argv[2]
        torrent_path = sys.argv[3]
        peer = Peer('localhost', 0, 'localhost', 8000)
        info_hash = peer.create_torrent(file_path, torrent_path)
        print(f"Created torrent with info hash: {info_hash}")
        print(f"Torrent file saved to: {torrent_path}")
        
    elif command == 'share':
        if len(sys.argv) not in [4, 5]:
            print("Usage: python main.py share <port> <file_path> [<torrent_path>]")
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
            print("Usage: python main.py download <port> <filename> <output_path> [--multi]")
            sys.exit(1)
            
        peer_port = int(sys.argv[2])
        filename = sys.argv[3]
        output_path = sys.argv[4]
        multi_peer = '--multi' in sys.argv
        
        peer = Peer('localhost', peer_port, 'localhost', 8000)
        peer.download_file(filename, output_path, multi_peer)

if __name__ == '__main__':
    main()