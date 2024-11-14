import os

def merge_files(input_dir, output_file, num_parts=5):
    # Kiểm tra và tạo thư mục đầu ra nếu chưa có
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Mở file đầu ra để ghi dữ liệu
    with open(output_file, 'wb') as output:
        for i in range(num_parts):
            # Tạo đường dẫn cho mỗi phần
            part_file_name = os.path.join(input_dir, f"result_{i + 1}.txt")
            
            # Kiểm tra xem file có tồn tại không
            if os.path.exists(part_file_name):
                with open(part_file_name, 'rb') as part_file:
                    output.write(part_file.read())  # Ghi nội dung của mỗi phần vào file đầu ra
                print(f"Đã ghép phần {i + 1} vào {output_file}")
            else:
                print(f"Không tìm thấy file {part_file_name}.")
                
    print(f"Đã gộp tất cả các phần vào file {output_file}")

# Sử dụng hàm
input_dir = 'E:\p2p_file_sharing\store'  # Thư mục chứa các phần file
output_file = 'outputStore/result.txt'  # Đường dẫn file đầu ra sau khi gộp, với dấu gạch chéo xuôi
merge_files(input_dir, output_file, num_parts=5)