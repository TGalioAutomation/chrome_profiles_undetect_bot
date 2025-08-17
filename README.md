# Chrome Profiles Manager - Bot Bypass Tool

🚀 **Công cụ quản lý multi-profile Chrome với khả năng bypass bot detection tiên tiến**

## ✨ Tính năng chính

### 🛡️ Bot Detection Bypass
- **Stealth Mode**: Loại bỏ các dấu hiệu automation
- **Canvas Fingerprinting Bypass**: Randomize canvas fingerprinting
- **WebGL Fingerprinting Bypass**: Fake WebGL renderer info
- **Audio Fingerprinting Bypass**: Randomize audio context
- **Navigator Properties Override**: Fake plugins, languages, permissions
- **Timezone & Geolocation Spoofing**: Fake location và timezone
- **User Agent Rotation**: Tự động thay đổi user agent

### 👥 Multi-Profile Management
- **Unlimited Profiles**: Tạo và quản lý không giới hạn profiles
- **Profile Isolation**: Mỗi profile hoàn toàn độc lập
- **Persistent Data**: Lưu trữ cookies, localStorage, session
- **Custom Settings**: Cấu hình riêng cho từng profile

### 🌐 Proxy Support
- **HTTP/HTTPS Proxy**: Hỗ trợ proxy HTTP và HTTPS
- **SOCKS4/SOCKS5**: Hỗ trợ SOCKS proxy
- **Per-Profile Proxy**: Mỗi profile có thể dùng proxy khác nhau
- **Proxy Rotation**: Tự động thay đổi proxy

### 🎛️ Web Management Interface
- **Dashboard**: Theo dõi trạng thái tổng quan
- **Profile Manager**: Tạo, sửa, xóa profiles
- **Real-time Control**: Điều khiển browser real-time
- **Session Monitoring**: Theo dõi phiên làm việc

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone https://github.com/TGalioAutomation/chrome_profiles_undetect_bot.git
cd chrome_profiles_undetect_bot
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng
```bash
python main.py
```

### 4. Truy cập Web Interface
Mở trình duyệt và truy cập: `http://localhost:5000`

## 📖 Hướng dẫn sử dụng

### Tạo Profile mới

1. **Truy cập trang Profiles**: `http://localhost:5000/profiles`
2. **Click "Create New Profile"**
3. **Điền thông tin**:
   - **Profile Name**: Tên unique cho profile
   - **Display Name**: Tên hiển thị
   - **User Agent**: Chọn hoặc nhập custom user agent
   - **Proxy**: (Tùy chọn) Nhập proxy theo format `protocol://host:port`
   - **Window Size**: Kích thước cửa sổ browser
   - **Headless**: Chạy ẩn hoặc hiển thị
   - **Custom Options**: Các tùy chọn Chrome bổ sung

### Quản lý Browsers

#### Khởi động Browser
```python
# Sử dụng API
POST /api/profiles/{profile_name}/start

# Hoặc click nút "Start" trong Web UI
```

#### Điều hướng Browser
```python
# Sử dụng API
POST /api/profiles/{profile_name}/navigate
{
    "url": "https://example.com"
}

# Hoặc click nút "Navigate" trong Web UI
```

#### Dừng Browser
```python
# Sử dụng API
POST /api/profiles/{profile_name}/stop

# Hoặc click nút "Stop" trong Web UI
```

### Sử dụng trong Code

```python
from core.chrome_driver import ChromeDriverManager
from core.bot_bypass import BotBypassManager

# Tạo driver manager
driver_manager = ChromeDriverManager("my_profile")

# Khởi động browser với bot bypass
driver = driver_manager.start_driver(
    headless=False,
    proxy="http://proxy:8080",
    user_agent="custom_user_agent"
)

# Áp dụng bot bypass techniques
bypass_manager = BotBypassManager(driver)
bypass_manager.apply_all_bypasses()

# Sử dụng browser
driver_manager.navigate_to("https://example.com")

# Đóng browser
driver_manager.quit_driver()
```

## 🔧 Cấu hình

### File config.py
```python
# Chrome settings
CHROME_BINARY_PATH = None  # Auto-detect
CHROMEDRIVER_PATH = None   # Auto-detect

# Flask settings
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Database
DATABASE_URL = "sqlite:///profiles.db"
```

### Environment Variables
```bash
# Tùy chọn: Đặt đường dẫn Chrome binary
export CHROME_BINARY_PATH="/path/to/chrome"

# Tùy chọn: Đặt đường dẫn ChromeDriver
export CHROMEDRIVER_PATH="/path/to/chromedriver"
```

## 📁 Cấu trúc thư mục

```
chrome_profiles_undetect_bot/
├── main.py                 # Entry point
├── config.py              # Cấu hình
├── requirements.txt       # Dependencies
├── README.md             # Tài liệu
├── core/                 # Core modules
│   ├── chrome_driver.py  # Chrome driver manager
│   ├── profile_manager.py # Profile management
│   └── bot_bypass.py     # Bot bypass techniques
├── api/                  # REST API
│   └── routes.py         # API endpoints
├── ui/                   # Web interface
│   ├── templates/        # HTML templates
│   └── static/          # CSS, JS, images
├── profiles/            # Profile data storage
├── logs/               # Log files
└── temp/              # Temporary files
```

## 🔌 API Endpoints

### Profiles
- `GET /api/profiles` - Lấy danh sách profiles
- `POST /api/profiles` - Tạo profile mới
- `GET /api/profiles/{name}` - Lấy thông tin profile
- `PUT /api/profiles/{name}` - Cập nhật profile
- `DELETE /api/profiles/{name}` - Xóa profile

### Browser Control
- `POST /api/profiles/{name}/start` - Khởi động browser
- `POST /api/profiles/{name}/stop` - Dừng browser
- `POST /api/profiles/{name}/navigate` - Điều hướng đến URL

### System
- `GET /api/status` - Trạng thái hệ thống

## 🛠️ Troubleshooting

### Lỗi ChromeDriver
```bash
# Cài đặt ChromeDriver tự động
pip install webdriver-manager
```

### Lỗi Permission
```bash
# Linux/macOS: Cấp quyền thực thi
chmod +x chromedriver
```

### Lỗi Port đã sử dụng
```python
# Thay đổi port trong config.py
FLASK_PORT = 5001
```

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Hỗ trợ

- **Issues**: [GitHub Issues](https://github.com/TGalioAutomation/chrome_profiles_undetect_bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/TGalioAutomation/chrome_profiles_undetect_bot/discussions)

## ⚠️ Lưu ý pháp lý

Công cụ này được tạo ra cho mục đích giáo dục và testing. Người dùng có trách nhiệm tuân thủ các điều khoản dịch vụ của các website và luật pháp địa phương khi sử dụng.

---

**Made with ❤️ by Chrome Profiles Manager Team**
