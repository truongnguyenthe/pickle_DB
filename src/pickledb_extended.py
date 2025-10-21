import pickledb

def main():
    # Tạo database mới hoặc mở nếu đã có
    db = pickledb.load('test.db', auto_dump=True)
    
    # Thêm dữ liệu
    db.set('hello', 'world')
    print("hello ->", db.get('hello'))

    # Xóa dữ liệu
    db.rem('hello')
    print("after removal:", db.get('hello'))

if __name__ == '__main__':
    main()
