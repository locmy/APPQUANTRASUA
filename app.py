import os
import json
import hmac
import sqlite3
import secrets
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
st.image("Screenshot_20261017_170859_Hypic.jpg")

# =========================================================
# CẤU HÌNH TRANG
# =========================================================
st.set_page_config(
    page_title="Tiệm trà ZZZ",
    page_icon="🧋",
    layout="wide",
)

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("ZZZ_DB_PATH", str(APP_DIR / "zzz_orders.db")))

# =========================================================
# THÔNG TIN THANH TOÁN
# QR VietQR là QR chuyển khoản tĩnh theo số tiền/nội dung đơn.
# Không tự xác minh tiền vào tài khoản ngân hàng.
# =========================================================
BANK_CODE = "VCB"
BANK_NAME = "Vietcombank"
ACCOUNT_NUMBER = "1037087682"
ACCOUNT_NAME = "PHAM THI MY LOC"

# Đổi mật khẩu Admin bằng biến môi trường ZZZ_ADMIN_PASSWORD.
# Ví dụ: ZZZ_ADMIN_PASSWORD="mat-khau-rieng-cua-ban"
ADMIN_PASSWORD = os.getenv("ZZZ_ADMIN_PASSWORD", "admin123")

# =========================================================
# HÌNH ẢNH MENU
# Đặt các ảnh cùng thư mục với app.py hoặc chỉnh đường dẫn ở đây.
# =========================================================
IMAGE_URLS = {
    "Trà Sữa Truyền Thống": "IMG_be364db8-ba92-4de2-94b3-e19fabc24223~2.jpg",
    "Trà Sữa Trân Châu Đường Đen": "Screenshot_20261019_173653_Hypic.jpg",
    "Trà Sữa Thái Xanh": "retouch_2026101917475806.jpg",
    "Trà Sữa Ô Long": "IMG_188e1380-3bc7-465b-bd10-5705d2e84719.jpg",
    "Matcha Latte": "IMG_9ea76e06-da48-4efb-8b28-972ef95d5262.jpg",
    "Trà Đào Cam Sả": "IMG_7bd03c4e-527a-48b3-8a47-703262a6a50b.jpg",
    "Trà Atiso Hạt Chia": "retouch_2026101918013212.jpg",
    "Lục Trà Lựu Nha Đam": "Screenshot_20261019_180339_Google.jpg",
    "Trà Dâu Tằm": "IMG_90800819-5085-4b40-b37b-4c4a278068d7.jpg",
}

# =========================================================
# MENU VÀ GIÁ
# =========================================================
MENU = {
    "Trà Sữa Truyền Thống": 30000,
    "Trà Sữa Trân Châu Đường Đen": 35000,
    "Trà Sữa Thái Xanh": 32000,
    "Trà Sữa Ô Long": 35000,
    "Matcha Latte": 38000,
    "Trà Đào Cam Sả": 35000,
    "Trà Dâu Tằm": 32000,
    "Trà Atiso Hạt Chia": 35000,
    "Lục Trà Lựu Nha Đam": 35000,
}

BEST_SELLERS = [
    "Trà Sữa Trân Châu Đường Đen",
    "Matcha Latte",
    "Lục Trà Lựu Nha Đam",
]

SIZE_PRICES = {
    "S - Vừa": 0,
    "M - Lớn": 5000,
    "L - Đặc biệt": 10000,
}

TOPPINGS = {
    "Trân châu đen": 5000,
    "Trân châu trắng": 5000,
    "Thạch trái cây": 5000,
    "Pudding trứng": 10000,
    "Kem Cheese": 10000,
}

SUGAR_LEVELS = [
    "100% (Bình thường)",
    "70%",
    "50%",
    "30%",
    "0% (Không đường)",
]
ICE_LEVELS = [
    "100% (Bình thường)",
    "70%",
    "50%",
    "30%",
    "0% (Không đá)",
]

VOUCHERS = {
    "BOBA3": {
        "name": "Giảm 3%",
        "type": "percent",
        "value": 3,
        "min_quantity": 1,
    },
    "BOBA5": {
        "name": "Giảm 5% bill từ 2 ly",
        "type": "percent",
        "value": 5,
        "min_quantity": 2,
    },
    "BOGO": {
        "name": "Mua 1 tặng 1",
        "type": "bogo",
        "value": 0,
        "min_quantity": 2,
    },
}
LUCKY_PRIZES = [
    "Giảm 3%",
    "may mắn",
    "Giảm 5% bill từ 2 ly",
    "may mắn",
    "Mua 1 tặng 1",
    "may mắn",
]

# =========================================================
# DATABASE
# =========================================================
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(""" CREATE TABLE IF NOT EXISTS orders ( id INTEGER PRIMARY KEY AUTOINCREMENT, order_code TEXT UNIQUE NOT NULL, customer TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', items_json TEXT NOT NULL, subtotal INTEGER NOT NULL, bogo_discount INTEGER NOT NULL, percent_discount REAL NOT NULL, percent_amount INTEGER NOT NULL, final_total INTEGER NOT NULL, voucher_code TEXT, voucher_message TEXT, payment_note TEXT, paid_at TEXT, admin_note TEXT ) """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")


init_db()

# =========================================================
# SESSION STATE
# =========================================================
DEFAULTS = {
    "cart": [],
    "selected_drink": list(MENU.keys())[0],
    "lucky_prize": "",
    "lucky_index": None,
    "wheel_just_spun": False,
    "voucher_code": "",
    "discount_input": 0,
    "last_order_code": "",
    "admin_logged_in": False,
    "admin_login_error": False,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# HÀM HỖ TRỢ
# =========================================================
def format_money(amount):
    return f"{int(round(amount)):,} đ".replace(",", ".")


def get_image_path(product_name):
    relative_path = IMAGE_URLS.get(product_name, "")
    path = APP_DIR / relative_path
    return str(path) if relative_path and path.is_file() else None


def cart_quantity(cart):
    return sum(int(item["quantity"]) for item in cart)


def calculate_subtotal(cart):
    return sum(int(item["unit_price"]) * int(item["quantity"]) for item in cart)


def calculate_bogo_discount(cart):
    # Mỗi cặp cùng món: tặng 1 ly, phần giảm bằng giá cơ bản của món.
    discount = 0
    for item in cart:
        free_cups = int(item["quantity"]) // 2
        discount += free_cups * int(item["base_price"])
    return discount


def calculate_totals(cart, discount_percent=0, voucher_code=""):
    subtotal = calculate_subtotal(cart)
    total_quantity = cart_quantity(cart)
    bogo_discount = 0
    percent_discount = 0.0
    voucher_message = "Không áp dụng voucher"

    code = (voucher_code or "").strip().upper()
    voucher = VOUCHERS.get(code)

    if voucher:
        if total_quantity < voucher["min_quantity"]:
            voucher_message = (
                f"Voucher {code} yêu cầu tối thiểu {voucher['min_quantity']} ly."
            )
        elif voucher["type"] == "bogo":
            bogo_discount = calculate_bogo_discount(cart)
            voucher_message = "Đã áp dụng voucher Mua 1 tặng 1."
        elif voucher["type"] == "percent":
            percent_discount += float(voucher["value"])
            voucher_message = f"Đã áp dụng voucher {voucher['name']}."
    elif code:
        voucher_message = "Mã voucher không hợp lệ."

    manual_discount = max(0.0, min(float(discount_percent or 0), 100.0))
    percent_discount = min(percent_discount + manual_discount, 100.0)

    amount_after_bogo = max(0, subtotal - bogo_discount)
    percent_amount = round(amount_after_bogo * percent_discount / 100)
    final_total = max(0, amount_after_bogo - percent_amount)

    return {
        "subtotal": subtotal,
        "bogo_discount": bogo_discount,
        "percent_discount": percent_discount,
        "percent_amount": percent_amount,
        "final_total": final_total,
        "voucher_message": voucher_message,
    }


def make_order_code():
    return "ZZZ" + datetime.now().strftime("%y%m%d%H%M%S") + secrets.token_hex(2).upper()


def create_order(customer, cart, totals, voucher_code):
    order_code = make_order_code()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items_json = json.dumps(cart, ensure_ascii=False)
    payment_note = f"ZZZ {order_code}"
    with get_connection() as conn:
        conn.execute(""" INSERT INTO orders ( order_code, customer, created_at, status, items_json, subtotal, bogo_discount, percent_discount, percent_amount, final_total, voucher_code, voucher_message, payment_note ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?) """, (
            order_code, customer, created_at, items_json,
            int(totals["subtotal"]), int(totals["bogo_discount"]),
            float(totals["percent_discount"]), int(totals["percent_amount"]),
            int(totals["final_total"]), (voucher_code or "").strip().upper(),
            totals["voucher_message"], payment_note,
        ))
    return order_code


def fetch_order(order_code):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE order_code = ?", (order_code,)
        ).fetchone()
    return dict(row) if row else None


def parse_items(order):
    try:
        return json.loads(order["items_json"])
    except (ValueError, TypeError, KeyError):
        return []


def make_vietqr_url(amount, order_code):
    # VietQR image URL. QR chỉ tạo nội dung chuyển khoản, không xác nhận tiền đã vào.
    params = {
        "amount": int(amount),
        "addInfo": f"ZZZ {order_code}",
        "accountName": ACCOUNT_NAME,
    }
    return (
        f"https://img.vietqr.io/image/{BANK_CODE}-{ACCOUNT_NUMBER}-compact2.png?"
        + urlencode(params)
    )


def update_order_status(order_code, status, admin_note=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        if status == "paid":
            conn.execute(""" UPDATE orders SET status = 'paid', paid_at = ?, admin_note = ? WHERE order_code = ? """, (now, admin_note, order_code))
        else:
            conn.execute(""" UPDATE orders SET status = ?, admin_note = ? WHERE order_code = ? """, (status, admin_note, order_code))


def reset_current_order():
    st.session_state.cart = []
    st.session_state.lucky_prize = ""
    st.session_state.voucher_code = ""
    st.session_state.discount_input = 0
    st.session_state.last_order_code = ""


def status_label(status):
    return {
        "pending": "Chờ xác nhận",
        "paid": "Đã thanh toán",
        "cancelled": "Đã hủy",
    }.get(status, status)


def money_column(series):
    return series.fillna(0).astype(int)


def render_lucky_wheel(selected_index=None, animate=False):
    """Hiển thị vòng quay 6 ô; kết quả được chọn phía Python để đồng bộ voucher."""
    labels = [
        "Giảm 3%",
        "Chúc may mắn",
        "Giảm 5%\nbill từ 2 ly",
        "Chúc may mắn",
        "Mua 1\ntặng 1",
        "Chúc may mắn",
    ]
    label_html = "".join(
        f'<div class="wheel-label" style="transform: rotate({i * 60 + 30}deg) translateY(-88px) rotate(-{i * 60 + 30}deg);">{label.replace(chr(10), "<br>")}</div>'
        for i, label in enumerate(labels)
    )
    rotation = 0
    if selected_index is not None:
        rotation = 1800 + ((330 - selected_index * 60) % 360)
    initial_rotation = 0 if animate and selected_index is not None else rotation
    target_rotation = rotation
    html = f''' <div class="wheel-wrap"> <div class="pointer"></div> <div id="prize-wheel" class="wheel" style="transform: rotate({initial_rotation}deg);"> {label_html} <div class="wheel-center">ZZZ</div> </div> </div> <style> * {{ box-sizing: border-box; }} body {{ margin: 0; font-family: Arial, sans-serif; background: transparent; }} .wheel-wrap {{ width: 330px; height: 330px; margin: 8px auto 0; position: relative; padding-top: 14px; }} .wheel {{ width: 300px; height: 300px; margin: 14px auto 0; border-radius: 50%; position: relative; border: 6px solid #fff; outline: 3px solid #8f416b; background: conic-gradient(from 0deg, #ff8eb3 0deg 60deg, #ffe5a3 60deg 120deg, #b7e7d1 120deg 180deg, #ffd0df 180deg 240deg, #d9c5ff 240deg 300deg, #fff0bd 300deg 360deg); box-shadow: 0 5px 18px rgba(80,30,60,.22); transition: transform 4.8s cubic-bezier(.12,.72,.12,1); }} .wheel-label {{ position: absolute; top: 50%; left: 50%; margin-left: -48px; margin-top: -16px; width: 96px; text-align: center; font-weight: 800; font-size: 11px; line-height: 1.2; color: #4b2540; text-shadow: 0 1px 0 rgba(255,255,255,.45); }} .wheel-center {{ position: absolute; width: 62px; height: 62px; left: 50%; top: 50%; transform: translate(-50%,-50%); border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #fff; border: 4px solid #8f416b; color: #8f416b; font-size: 17px; font-weight: 900; box-shadow: 0 2px 8px rgba(0,0,0,.18); }} .pointer {{ position: absolute; z-index: 5; top: 0; left: 50%; transform: translateX(-50%); width: 0; height: 0; /* Mũi tên tam giác hướng xuống, chĩa vào bên trong vòng quay */ border-left: 17px solid transparent; border-right: 17px solid transparent; border-top: 31px solid #a51f55; border-bottom: 0; filter: drop-shadow(0 2px 2px rgba(0,0,0,.25)); }} @media (max-width: 380px) {{ .wheel-wrap {{ transform: scale(.9); transform-origin: top center; margin-bottom: -28px; }} }} </style> <script> const wheel = document.getElementById('prize-wheel'); const shouldAnimate = {str(bool(animate)).lower()}; const target = {target_rotation}; if (shouldAnimate) {{ setTimeout(() => {{ wheel.style.transform = `rotate(${{target}}deg)`; }}, 120); }} </script> </div> '''
    components.html(html, height=350, scrolling=False)


def render_order_details(order, show_status=True):
    if not order:
        return
    st.markdown(f"### Hóa đơn {order['order_code']}")
    st.write(f"**Khách hàng:** {order['customer']}")
    st.write(f"**Thời gian tạo:** {order['created_at']}")
    if show_status:
        st.write(f"**Trạng thái:** {status_label(order['status'])}")
    for idx, item in enumerate(parse_items(order), start=1):
        toppings = ", ".join(item.get("toppings", [])) or "Không"
        st.write(
            f"{idx}. **{item['name']}** — {item['size']} — "
            f"{item['quantity']} ly — {format_money(item['unit_price'])}/ly"
        )
        st.caption(
            f"Topping: {toppings} | Đường: {item.get('sugar', '')} | "
            f"Đá: {item.get('ice', '')}"
        )
        st.write(f"Thành tiền: {format_money(item['unit_price'] * item['quantity'])}")
    st.divider()
    st.write(f"Tạm tính: {format_money(order['subtotal'])}")
    st.write(f"Giảm Mua 1 tặng 1: {format_money(order['bogo_discount'])}")
    st.write(f"Tỷ lệ giảm giá: {float(order['percent_discount']):g}%")
    st.write(f"Tiền giảm theo phần trăm: {format_money(order['percent_amount'])}")
    st.write(f"Mã voucher: {order['voucher_code'] or 'Không sử dụng'}")
    st.caption(order["voucher_message"] or "")
    st.markdown(f"## Tổng thanh toán: {format_money(order['final_total'])}")


# =========================================================
# GIAO DIỆN CHÍNH
# =========================================================
st.title("🧋 TIỆM TRÀ ZZZ")
st.subheader("Hệ thống gọi món, thanh toán và quản lý bán hàng")
st.caption("Chọn loại nước trước, sau đó tùy chỉnh size, đường, đá và topping.")

menu_tab, cart_tab, payment_tab, lookup_tab, admin_tab = st.tabs(
    ["🥤 Chọn món", "🛒 Giỏ hàng", "💳 Thanh toán", "🔎 Tra cứu đơn", "🔐 Admin"]
)

# =========================================================
# TAB 1: CHỌN NƯỚC TRƯỚC, TÙY CHỈNH SAU
# =========================================================
with menu_tab:
    st.header("1. Chọn loại nước")
    columns = st.columns(3)
    for index, (name, price) in enumerate(MENU.items()):
        with columns[index % 3]:
            with st.container(border=True):
                image_path = get_image_path(name)
                if image_path:
                    st.image(image_path, use_container_width=True)
                else:
                    st.info(f"Chưa tìm thấy ảnh của {name}.")
                st.markdown(f"**{name}**")
                if name in BEST_SELLERS:
                    st.caption("❤️‍🔥 Best seller")
                st.write(f"Giá từ **{format_money(price)}**")
                if st.button(
                    "Chọn món này" if st.session_state.selected_drink != name else "✓ Đang chọn",
                    key=f"select_drink_{index}",
                    use_container_width=True,
                    type="primary" if st.session_state.selected_drink == name else "secondary",
                ):
                    st.session_state.selected_drink = name
                    st.rerun()

    selected_name = st.session_state.selected_drink
    selected_price = MENU[selected_name]
    st.divider()
    st.header("2. Tùy chỉnh món đã chọn")
    st.info(f"Bạn đang chọn: **{selected_name}** — giá cơ bản {format_money(selected_price)}")

    with st.form("customize_drink_form"):
        size = st.selectbox(
            "Chọn size",
            list(SIZE_PRICES.keys()),
            key="custom_size",
        )
        sugar = st.selectbox("Chọn mức đường", SUGAR_LEVELS, index=0, key="custom_sugar")
        ice = st.selectbox("Chọn mức đá", ICE_LEVELS, index=0, key="custom_ice")
        toppings = st.multiselect(
            "Chọn topping (có thể chọn nhiều)",
            list(TOPPINGS.keys()),
            key="custom_toppings",
            format_func=lambda x: f"{x} (+{format_money(TOPPINGS[x])})",
        )
        quantity = st.number_input(
            "Số lượng ly", min_value=1, max_value=50, value=1, step=1, key="custom_quantity"
        )
        unit_price = selected_price + SIZE_PRICES[size] + sum(TOPPINGS[t] for t in toppings)
        st.markdown(f"**Đơn giá:** {format_money(unit_price)}")
        st.markdown(f"**Thành tiền:** {format_money(unit_price * int(quantity))}")
        submitted = st.form_submit_button("➕ Thêm vào giỏ hàng", use_container_width=True)
        if submitted:
            st.session_state.cart.append({
                "name": selected_name,
                "base_price": selected_price,
                "size": size,
                "toppings": list(toppings),
                "sugar": sugar,
                "ice": ice,
                "quantity": int(quantity),
                "unit_price": int(unit_price),
            })
            st.success(f"Đã thêm {selected_name} vào giỏ hàng!")

# =========================================================
# TAB 2: GIỎ HÀNG
# =========================================================
with cart_tab:
    st.header("🛒 Giỏ hàng")
    if not st.session_state.cart:
        st.info("Giỏ hàng đang trống. Hãy chọn món ở tab Chọn món.")
    else:
        remove_index = None
        for index, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{item['name']}**")
                    st.write(f"Size: {item['size']} | Số lượng: {item['quantity']}")
                    st.write("Topping: " + (", ".join(item["toppings"]) or "Không"))
                    st.write(f"Đường: {item['sugar']} | Đá: {item['ice']}")
                    st.write(
                        f"Thành tiền: **{format_money(item['unit_price'] * item['quantity'])}**"
                    )
                with col2:
                    if st.button("🗑️ Xóa", key=f"remove_cart_{index}"):
                        remove_index = index
        if remove_index is not None:
            st.session_state.cart.pop(remove_index)
            st.rerun()

        st.divider()
        st.metric("Tạm tính", format_money(calculate_subtotal(st.session_state.cart)))
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🧹 Xóa toàn bộ giỏ hàng", use_container_width=True):
                st.session_state.cart = []
                st.rerun()
        with col_b:
            st.info("Mở tab Thanh toán để áp dụng voucher và tạo QR.")

# =========================================================
# TAB 3: THANH TOÁN + QR
# =========================================================
with payment_tab:
    st.header("💳 Thanh toán")
    if not st.session_state.cart:
        st.info("Bạn chưa có món nào trong giỏ hàng.")
    else:
        customer_name = st.text_input(
            "Tên khách hàng", key="checkout_customer", placeholder="Nhập tên khách hàng"
        )

        st.subheader("🎡 Vòng quay may mắn")
        st.write("Vòng quay gồm 3 ô ưu đãi xen kẽ 3 ô chúc may mắn. Nhấn nút bên dưới để thử vận may!")
        wheel_animate = bool(st.session_state.get("wheel_just_spun", False))
        render_lucky_wheel(st.session_state.get("lucky_index"), animate=wheel_animate)
        # Chỉ phát hoạt ảnh ở lần rerun ngay sau khi khách bấm quay.
        if wheel_animate:
            st.session_state.wheel_just_spun = False

        if st.button("🎲 QUAY THƯỞNG", use_container_width=True, type="primary"):
            prize_index = secrets.randbelow(len(LUCKY_PRIZES))
            prize = LUCKY_PRIZES[prize_index]
            st.session_state.lucky_index = prize_index
            st.session_state.lucky_prize = prize
            st.session_state.wheel_just_spun = True
            st.session_state.voucher_code = {
                "Giảm 3%": "BOBA3",
                "Giảm 5% bill từ 2 ly": "BOBA5",
                "Mua 1 tặng 1": "BOGO",
            }.get(prize, "")
            # Đồng bộ ô nhập voucher để kết quả vòng quay được áp dụng ngay.
            st.session_state.checkout_voucher = st.session_state.voucher_code
            st.rerun()

        if st.session_state.lucky_prize:
            if st.session_state.lucky_prize == "may mắn":
                st.info("🍀 Kết quả: Chúc may mắn lần sau! Bạn có thể tiếp tục đặt món.")
            else:
                st.success(f"🎉 Kết quả vòng quay: {st.session_state.lucky_prize}!")
                if st.session_state.voucher_code:
                    st.caption(f"Mã ưu đãi đã điền vào ô voucher: {st.session_state.voucher_code}")

        voucher_code = st.text_input(
            "Mã voucher", key="checkout_voucher", value=st.session_state.voucher_code,
            placeholder="Ví dụ: BOBA3, BOBA5, BOGO"
        )
        discount_input = st.number_input(
            "Giảm giá thêm (%)", min_value=0, max_value=100, value=0, step=1,
            key="checkout_discount"
        )
        totals = calculate_totals(
            st.session_state.cart, discount_percent=discount_input, voucher_code=voucher_code
        )

        st.divider()
        st.subheader("🧾 Tạm tính hóa đơn")
        st.write(f"**Tạm tính:** {format_money(totals['subtotal'])}")
        st.write(f"**Giảm giá Mua 1 tặng 1:** {format_money(totals['bogo_discount'])}")
        st.write(f"**Tổng tỷ lệ giảm giá:** {totals['percent_discount']:g}%")
        st.write(f"**Tiền giảm theo phần trăm:** {format_money(totals['percent_amount'])}")
        st.caption(totals["voucher_message"])
        st.markdown(f"### Tổng thanh toán: {format_money(totals['final_total'])}")

        if st.button("📲 Tạo đơn hàng và hiện mã QR", type="primary", use_container_width=True):
            if not customer_name.strip():
                st.warning("Vui lòng nhập tên khách hàng.")
            elif not st.session_state.cart:
                st.warning("Giỏ hàng đang trống.")
            else:
                order_code = create_order(
                    customer_name.strip(),
                    [item.copy() for item in st.session_state.cart],
                    totals,
                    voucher_code,
                )
                st.session_state.last_order_code = order_code
                st.session_state.cart = []
                st.session_state.lucky_prize = ""
                st.session_state.voucher_code = ""
                st.session_state.discount_input = 0
                st.rerun()

        # Hiện lại QR của đơn vừa tạo, kể cả sau khi Streamlit rerun.
        if st.session_state.last_order_code:
            order = fetch_order(st.session_state.last_order_code)
            if order:
                st.divider()
                render_order_details(order)
                if order["status"] == "pending":
                    st.subheader("📷 Quét mã QR để chuyển khoản")
                    st.image(make_vietqr_url(order["final_total"], order["order_code"]),
                             caption="QR Vietcombank — kiểm tra đúng tên người nhận và số tiền trước khi chuyển.")
                    st.write(f"**Ngân hàng:** {BANK_NAME}")
                    st.write(f"**Số tài khoản:** {ACCOUNT_NUMBER}")
                    st.write(f"**Chủ tài khoản:** {ACCOUNT_NAME}")
                    st.write(f"**Số tiền:** {format_money(order['final_total'])}")
                    st.write(f"**Nội dung chuyển khoản:** ZZZ {order['order_code']}")
                    st.warning(
                        "Đơn đang chờ xác nhận. Sau khi chuyển khoản, vui lòng báo nhân viên. "
                        "QR không tự xác minh tiền đã vào tài khoản."
                    )
                    if st.button("🔄 Kiểm tra trạng thái đơn", use_container_width=True):
                        st.rerun()
                elif order["status"] == "paid":
                    st.success("Đơn hàng đã được Admin xác nhận thanh toán.")
                else:
                    st.error("Đơn hàng này đã bị hủy.")

# =========================================================
# TAB 4: TRA CỨU ĐƠN CỦA KHÁCH
# =========================================================
with lookup_tab:
    st.header("🔎 Tra cứu đơn hàng")
    st.write("Nhập mã đơn hàng được hiển thị sau khi tạo QR.")
    lookup_code = st.text_input("Mã đơn hàng", key="customer_lookup_code",
                                value=st.session_state.last_order_code)
    if st.button("Tra cứu", key="customer_lookup_button"):
        order = fetch_order(lookup_code.strip().upper())
        if not order:
            st.error("Không tìm thấy đơn hàng. Vui lòng kiểm tra lại mã đơn.")
        else:
            render_order_details(order)
            if order["status"] == "pending":
                st.image(make_vietqr_url(order["final_total"], order["order_code"]),
                         caption="QR chuyển khoản Vietcombank")
                st.info("Đơn hàng đang chờ Admin xác nhận thanh toán.")
            elif order["status"] == "paid":
                st.success(f"Đã thanh toán lúc: {order['paid_at'] or 'Đã xác nhận'}")
            else:
                st.warning("Đơn hàng đã bị hủy.")

# =========================================================
# TAB 5: ADMIN
# =========================================================
with admin_tab:
    st.header("🔐 Trang quản trị Tiệm trà ZZZ")
    if not st.session_state.admin_logged_in:
        st.write("Đăng nhập để xem doanh thu, tra cứu đơn và xác nhận thanh toán.")
        with st.form("admin_login_form"):
            admin_password = st.text_input("Mật khẩu Admin", type="password")
            login_submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
        if login_submitted:
            if hmac.compare_digest(admin_password, ADMIN_PASSWORD):
                st.session_state.admin_logged_in = True
                st.session_state.admin_login_error = False
                st.rerun()
            else:
                st.session_state.admin_login_error = True
        if st.session_state.admin_login_error:
            st.error("Mật khẩu không đúng.")
        st.caption("Mật khẩu mặc định lần đầu: admin123. Hãy đổi bằng biến môi trường ZZZ_ADMIN_PASSWORD trước khi triển khai công khai.")
    else:
        top1, top2 = st.columns([4, 1])
        with top1:
            st.success("Đã đăng nhập Admin.")
        with top2:
            if st.button("Đăng xuất", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()

        with get_connection() as conn:
            all_orders_df = pd.read_sql_query(
                "SELECT * FROM orders ORDER BY created_at DESC", conn
            )

        if all_orders_df.empty:
            st.info("Chưa có đơn hàng nào trong hệ thống.")
        else:
            paid_df = all_orders_df[all_orders_df["status"] == "paid"].copy()
            total_revenue = int(paid_df["final_total"].fillna(0).sum())
            paid_count = len(paid_df)
            pending_count = int((all_orders_df["status"] == "pending").sum())
            cups_sold = sum(
                sum(int(it.get("quantity", 0)) for it in json.loads(items))
                for items in paid_df["items_json"].tolist()
            ) if not paid_df.empty else 0
            average_order = int(round(total_revenue / paid_count)) if paid_count else 0

            st.subheader("📊 Tổng quan kinh doanh")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Doanh thu đã thu", format_money(total_revenue))
            c2.metric("Đơn đã thanh toán", f"{paid_count}")
            c3.metric("Đơn chờ xác nhận", f"{pending_count}")
            c4.metric("Số ly đã bán", f"{cups_sold}")
            st.metric("Giá trị trung bình mỗi đơn đã thanh toán", format_money(average_order))

            st.divider()
            st.subheader("📈 Biểu đồ doanh thu")
            if not paid_df.empty:
                paid_df["paid_date"] = pd.to_datetime(
                    paid_df["paid_at"], errors="coerce"
                ).dt.date
                daily = (
                    paid_df.dropna(subset=["paid_date"])
                    .groupby("paid_date", as_index=False)["final_total"].sum()
                    .sort_values("paid_date")
                )
                if not daily.empty:
                    daily["Ngày"] = daily["paid_date"].astype(str)
                    st.bar_chart(daily.set_index("Ngày")["final_total"])
                else:
                    st.info("Chưa có dữ liệu ngày thanh toán để vẽ biểu đồ.")

                monthly_df = paid_df.dropna(subset=["paid_at"]).copy()
                if not monthly_df.empty:
                    monthly_df["Tháng"] = pd.to_datetime(
                        monthly_df["paid_at"], errors="coerce"
                    ).dt.to_period("M").astype(str)
                    monthly = monthly_df.groupby("Tháng")["final_total"].sum().sort_index()
                    st.write("Doanh thu theo tháng")
                    st.bar_chart(monthly)
            else:
                st.info("Chưa có đơn thanh toán thành công để thống kê doanh thu.")

            st.divider()
            st.subheader("🏆 Món bán chạy")
            product_sales = {}
            for _, row in paid_df.iterrows():
                for item in json.loads(row["items_json"]):
                    product_sales[item["name"]] = product_sales.get(item["name"], 0) + int(item["quantity"])
            if product_sales:
                best_df = pd.DataFrame(
                    [{"Tên món": name, "Số ly": qty} for name, qty in product_sales.items()]
                ).sort_values("Số ly", ascending=False)
                st.bar_chart(best_df.set_index("Tên món")["Số ly"])
                st.dataframe(best_df, use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có món nào được ghi nhận đã bán.")

            st.divider()
            st.subheader("🔍 Truy vấn và quản lý đơn hàng")
            f1, f2, f3 = st.columns(3)
            with f1:
                query_text = st.text_input("Tìm mã đơn hoặc tên khách")
            with f2:
                status_filter = st.selectbox(
                    "Trạng thái",
                    ["Tất cả", "Chờ xác nhận", "Đã thanh toán", "Đã hủy"]
                )
            with f3:
                start_date = st.date_input("Từ ngày", value=date.today() - timedelta(days=30))
            end_date = st.date_input("Đến ngày", value=date.today())

            filtered = all_orders_df.copy()
            if query_text.strip():
                q = query_text.strip().lower()
                filtered = filtered[
                    filtered["order_code"].str.lower().str.contains(q, na=False)
                    | filtered["customer"].str.lower().str.contains(q, na=False)
                ]
            status_map = {
                "Chờ xác nhận": "pending",
                "Đã thanh toán": "paid",
                "Đã hủy": "cancelled",
            }
            if status_filter != "Tất cả":
                filtered = filtered[filtered["status"] == status_map[status_filter]]
            filtered["created_date"] = pd.to_datetime(
                filtered["created_at"], errors="coerce"
            ).dt.date
            if start_date <= end_date:
                filtered = filtered[
                    (filtered["created_date"] >= start_date)
                    & (filtered["created_date"] <= end_date)
                ]
            else:
                st.warning("Ngày bắt đầu không được sau ngày kết thúc.")

            display_df = filtered[[
                "order_code", "customer", "created_at", "status",
                "subtotal", "final_total", "voucher_code", "paid_at"
            ]].copy()
            display_df = display_df.rename(columns={
                "order_code": "Mã đơn",
                "customer": "Khách hàng",
                "created_at": "Thời gian tạo",
                "status": "Trạng thái",
                "subtotal": "Tạm tính (đ)",
                "final_total": "Thanh toán (đ)",
                "voucher_code": "Voucher",
                "paid_at": "Thời gian thanh toán",
            })
            display_df["Trạng thái"] = display_df["Trạng thái"].map(status_label)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 Xuất kết quả truy vấn CSV",
                data=csv_bytes,
                file_name=f"zzz_orders_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            st.divider()
            st.subheader("🧾 Chi tiết đơn / xác nhận thanh toán")
            order_codes = filtered["order_code"].tolist()
            if order_codes:
                selected_order_code = st.selectbox("Chọn mã đơn", order_codes)
                selected_order = fetch_order(selected_order_code)
                if selected_order:
                    render_order_details(selected_order)
                    if selected_order["status"] == "pending":
                        st.image(
                            make_vietqr_url(selected_order["final_total"], selected_order["order_code"]),
                            caption="QR của đơn hàng được chọn"
                        )
                        admin_note = st.text_input(
                            "Ghi chú xác nhận (không bắt buộc)",
                            key=f"admin_note_{selected_order_code}"
                        )
                        a1, a2 = st.columns(2)
                        with a1:
                            if st.button("✅ Xác nhận đã nhận tiền", type="primary",
                                         key=f"mark_paid_{selected_order_code}",
                                         use_container_width=True):
                                update_order_status(selected_order_code, "paid", admin_note)
                                st.success("Đã xác nhận thanh toán. Doanh thu đã được cập nhật.")
                                st.rerun()
                        with a2:
                            if st.button("❌ Hủy đơn", key=f"cancel_{selected_order_code}",
                                         use_container_width=True):
                                update_order_status(selected_order_code, "cancelled", admin_note)
                                st.warning("Đã hủy đơn hàng.")
                                st.rerun()
                    elif selected_order["status"] == "paid":
                        st.success(f"Đã thanh toán lúc {selected_order['paid_at'] or '—'}.")
                        st.caption(f"Ghi chú Admin: {selected_order['admin_note'] or 'Không có'}")
                    else:
                        st.warning("Đơn này đã bị hủy.")
            else:
                st.info("Không có đơn hàng phù hợp bộ lọc hiện tại.")

            st.divider()
            st.subheader("📤 Xuất toàn bộ dữ liệu đơn hàng")
            all_export = all_orders_df.drop(columns=["items_json"], errors="ignore").copy()
            st.download_button(
                "Tải toàn bộ dữ liệu đơn hàng CSV",
                data=all_export.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"zzz_all_orders_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

# =========================================================
# CHÂN TRANG
# =========================================================
st.divider()
st.caption(
    "Tiệm trà ZZZ • QR Vietcombank là QR chuyển khoản. "
    "Doanh thu chỉ được ghi nhận sau khi Admin xác nhận thủ công."
    )
