import sys
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QSettings

_translations = {
    "vi": {
        "Connect mobile device (QR Code)": "Kết nối thiết bị di động (QR Code)",
        "TLGeo Toolbar": "Thanh công cụ TLGeo",
        "Version Info": "Thông tin phiên bản",
        "Logout": "Đăng xuất",
        "Login": "Đăng nhập",
        "You are logged in as:\n{}": "Bạn đã đăng nhập với tài khoản:\n{}",
        "Confirm Logout": "Xác nhận đăng xuất",
        "Are you sure you want to logout?\nSyncing with Agent will pause until you log in again.": "Bạn có chắc chắn muốn đăng xuất?\nTính năng đồng bộ với Agent sẽ tạm dừng cho đến khi bạn đăng nhập lại.",
        "Session Expired": "Phiên đăng nhập hết hạn",
        "Your session has expired.\nPlease log in again.": "Phiên đăng nhập của bạn đã hết hạn.\nVui lòng đăng nhập lại.",
        "Login successful! Welcome {}": "Đăng nhập thành công! Xin chào {}",
        "Logout successful": "Đăng xuất thành công.",
        "TLGeo QGIS is running at {}": "TLGeo QGIS đang chạy tại địa chỉ {}",
        "Fullname: {}": "Họ tên: {}",
        "Email: {}": "Email: {}",
        "Phone: {}": "SĐT: {}",
        "TLGeo2QGIS - Version Info": "TLGeo2QGIS - Thông tin phiên bản",
        "Export Capabilities:": "Khả năng xuất dữ liệu:",
        "Available": "Có sẵn",
        "Not available": "Không có",
        "Available (GDAL 3.8+)": "Có sẵn (GDAL 3.8+)",
        "Not available (GDAL 3.8+ required)": "Không có (cần GDAL 3.8+)",
        "Notes:": "Ghi chú:",
        "MBTiles requires QGIS 3.14+ or GDAL with MBTiles driver": "MBTiles cần QGIS 3.14+ hoặc GDAL có driver MBTiles",
        "PMTiles requires GDAL 3.8.0 or newer": "PMTiles cần GDAL 3.8.0 trở lên",
        "If MBTiles/PMTiles are unavailable, please upgrade QGIS to the newest version": "Nếu không có MBTiles/PMTiles, vui lòng nâng cấp QGIS lên phiên bản mới nhất",
        "Close": "Đóng",
        
        "Your QGIS environment does not support embedded web browser (WebEngine).": "Môi trường QGIS của bạn không hỗ trợ bộ duyệt web nhúng (WebEngine).",
        "Click the button below to open the tool in an external browser:": "Bấm nút dưới đây để mở công cụ trong trình duyệt ngoài:",
        "Open https://agent.tlgeo.net": "Mở https://agent.tlgeo.net",
        "Open https://agent.tlgeo.xyz": "Mở https://agent.tlgeo.xyz",
        "Open https://geocloud.tlgeo.xyz": "Mở https://geocloud.tlgeo.xyz",
        "GeoAI TLGeo Agent": "GeoAI TLGeo Agent",
        "Mobile Geocollect": "Mobile Geocollect",
        "Geocloud": "Geocloud",
        "là trợ lý hỗ trợ sử dụng QGIS bằng cách ra lệnh với ngôn ngữ tự nhiên": "là trợ lý hỗ trợ sử dụng QGIS bằng cách ra lệnh với ngôn ngữ tự nhiên",
        "Tính năng sử dụng kho dữ liệu Geocloud đang được phát triển.": "Tính năng sử dụng kho dữ liệu Geocloud đang được phát triển.",
        
        "TLGeo Content": "Nội dung TLGeo",
        "TLGeo Ribbon": "Thanh công cụ TLGeo Ribbon",
        "TLGeo Agent": "Agent TLGeo",
        "Projects": "Dự án",
        "Publish": "Xuất bản",
        "Profile": "Cá nhân",
        "Manage": "Quản lý",
        "Publish Layer": "Xuất bản lớp",
        "Info": "Thông tin",
        "Tools": "Công cụ",
        "System": "Hệ thống",
        "Utilities": "Tiện ích",
        
        "Login TLGeo2QGIS": "Đăng nhập TLGeo2QGIS",
        "Security Warning": "Cảnh báo bảo mật",
        "Login GEOADMIN": "Đăng nhập GEOADMIN",
        "Email or username": "Email hoặc tên đăng nhập",
        "Account:": "Tài khoản:",
        "Password": "Mật khẩu",
        "Password:": "Mật khẩu:",
        "Cancel": "Hủy",
        "Please enter email or username": "Vui lòng nhập email hoặc tên đăng nhập",
        "Please enter password": "Vui lòng nhập mật khẩu",
        "Logging in...": "Đang đăng nhập...",
        "Login failed": "Đăng nhập thất bại",
        
        "QR Code": "Mã QR",
        "QGIS and Geocollect mobile must be on the same LAN": "QGIS và Geocollect mobile phải cùng mạng LAN",
        "Scan this QR code to connect Geocollect mobile to QGIS": "Quét mã QR này để kết nối Geocollect mobile tới QGIS",
        "LAN IP Address:": "Địa chỉ IP LAN:",
        
        "Settings": "Cài đặt (Language)",
        "Language:": "Ngôn ngữ:",
        "Language changed. Please restart QGIS to apply changes completely.": "Ngôn ngữ đã được thay đổi. Vui lòng khởi động lại QGIS để áp dụng các thay đổi hoàn toàn.",
        "Save": "Lưu",
        
        "Status:": "Tình trạng:",
        "Connected": "Đã kết nối",
        "Disconnected": "Chưa kết nối"
    },
    "en": {
        "Connect mobile device (QR Code)": "Connect mobile device (QR Code)",
        "TLGeo Toolbar": "TLGeo Toolbar",
        "Version Info": "Version Info",
        "Logout": "Logout",
        "Login": "Login",
        "You are logged in as:\n{}": "You are logged in as:\n{}",
        "Confirm Logout": "Confirm Logout",
        "Are you sure you want to logout?\nSyncing with Agent will pause until you log in again.": "Are you sure you want to logout?\nSyncing with Agent will pause until you log in again.",
        "Session Expired": "Session Expired",
        "Your session has expired.\nPlease log in again.": "Your session has expired.\nPlease log in again.",
        "Login successful! Welcome {}": "Login successful! Welcome {}",
        "Logout successful": "Logout successful",
        "TLGeo QGIS is running at {}": "TLGeo QGIS is running at {}",
        "Fullname: {}": "Fullname: {}",
        "Email: {}": "Email: {}",
        "Phone: {}": "Phone: {}",
        "TLGeo2QGIS - Version Info": "TLGeo2QGIS - Version Info",
        "Export Capabilities:": "Export Capabilities:",
        "Available": "Available",
        "Not available": "Not available",
        "Available (GDAL 3.8+)": "Available (GDAL 3.8+)",
        "Not available (GDAL 3.8+ required)": "Not available (GDAL 3.8+ required)",
        "Notes:": "Notes:",
        "MBTiles requires QGIS 3.14+ or GDAL with MBTiles driver": "MBTiles requires QGIS 3.14+ or GDAL with MBTiles driver",
        "PMTiles requires GDAL 3.8.0 or newer": "PMTiles requires GDAL 3.8.0 or newer",
        "If MBTiles/PMTiles are unavailable, please upgrade QGIS to the newest version": "If MBTiles/PMTiles are unavailable, please upgrade QGIS to the newest version",
        "Close": "Close",
        
        "Your QGIS environment does not support embedded web browser (WebEngine).": "Your QGIS environment does not support embedded web browser (WebEngine).",
        "Click the button below to open the tool in an external browser:": "Click the button below to open the tool in an external browser:",
        "Open https://agent.tlgeo.net": "Open https://agent.tlgeo.net",
        "Open https://agent.tlgeo.xyz": "Open https://agent.tlgeo.xyz",
        "Open https://geocloud.tlgeo.xyz": "Open https://geocloud.tlgeo.xyz",
        "GeoAI TLGeo Agent": "GeoAI TLGeo Agent",
        "Mobile Geocollect": "Mobile Geocollect",
        "Geocloud": "Geocloud",
        "là trợ lý hỗ trợ sử dụng QGIS bằng cách ra lệnh với ngôn ngữ tự nhiên": "is an assistant supporting QGIS usage using natural language commands",
        "Tính năng sử dụng kho dữ liệu Geocloud đang được phát triển.": "The feature to use the Geocloud data repository is under development.",
        
        "TLGeo Content": "TLGeo Content",
        "TLGeo Ribbon": "TLGeo Ribbon",
        "TLGeo Agent": "TLGeo Agent",
        "Projects": "Projects",
        "Publish": "Publish",
        "Profile": "Profile",
        "Manage": "Manage",
        "Publish Layer": "Publish Layer",
        "Info": "Info",
        "Tools": "Tools",
        "System": "System",
        "Utilities": "Utilities",
        
        "Login TLGeo2QGIS": "Login TLGeo2QGIS",
        "Security Warning": "Security Warning",
        "Login GEOADMIN": "Login GEOADMIN",
        "Email or username": "Email or username",
        "Account:": "Account:",
        "Password": "Password",
        "Password:": "Password:",
        "Cancel": "Cancel",
        "Please enter email or username": "Please enter email or username",
        "Please enter password": "Please enter password",
        "Logging in...": "Logging in...",
        "Login failed": "Login failed",
        
        "QR Code": "QR Code",
        "QGIS and Geocollect mobile must be on the same LAN": "QGIS and Geocollect mobile must be on the same LAN",
        "Scan this QR code to connect Geocollect mobile to QGIS": "Scan this QR code to connect Geocollect mobile to QGIS",
        "LAN IP Address:": "LAN IP Address:",
        
        "Settings": "Settings (Language)",
        "Language:": "Language:",
        "Language changed. Please restart QGIS to apply changes completely.": "Language changed. Please restart QGIS to apply changes completely.",
        "Save": "Save",
        
        "Status:": "Status:",
        "Connected": "Connected",
        "Disconnected": "Disconnected"
    }
}

_current_locale = "en"

def init_i18n():
    global _current_locale
    try:
        # Check custom user language setting first
        settings = QSettings("TLGeo", "QGIS2Plugin")
        custom_lang = settings.value("i18n/language", None)
        if custom_lang in _translations:
            _current_locale = custom_lang
            return
            
        # Get QGIS locale
        locale = QgsApplication.locale()
        if not locale:
            locale = QSettings().value('locale/userLocale', 'en')
        
        if locale:
            locale = locale[0:2].lower()
            if locale in _translations:
                _current_locale = locale
            else:
                _current_locale = "en"
    except Exception:
        _current_locale = "en"

def tr(text):
    """Translate text to current locale."""
    lang_dict = _translations.get(_current_locale, _translations["en"])
    return lang_dict.get(text, text)
