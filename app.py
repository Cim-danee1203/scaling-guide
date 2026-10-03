import streamlit as st
import pandas as pd
st.image("logo.jpg")
# 1. Cấu hình trang
st.set_page_config(
    page_title="Công Cụ Tính Lãi Tiết Kiệm Kiêm Đa Ni",
    page_icon="💰",
    layout="centered"
)

# Custom CSS cho giao diện
st.markdown("""
    <style>
    .stApp { background-color: #FAFAFA; }
    h1 { color: #1E3A8A; text-align: center; font-weight: 700; }
    .subtitle { text-align: center; color: #4B5563; margin-bottom: 25px; }
    .metric-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.title("💰 CÔNG CỤ TÍNH LÃI TIẾT KIỆM")
st.markdown("<p class='subtitle'>Tính toán chính xác tiền lãi nhận được theo từng hình thức gửi</p>", unsafe_allow_html=True)

# 2. Giao diện nhập thông tin
st.subheader("📌 Nhập thông tin khoản gửi")

col1, col2 = st.columns(2)

with col1:
    principal = st.number_input(
        "Số tiền gửi ban đầu (VNĐ):",
        min_value=1_000_000,
        value=100_000_000,
        step=1_000_000,
        format="%d"
    )
    
    interest_rate = st.number_input(
        "Lãi suất (%/năm):",
        min_value=0.1,
        max_value=30.0,
        value=6.0,
        step=0.1,
        format="%.1f"
    )

    months = st.number_input(
        "Kỳ hạn gửi (tháng):",
        min_value=1,
        max_value=120,
        value=12,
        step=1
    )

with col2:
    payout_method = st.selectbox(
        "Hình thức nhận lãi:",
        ["Cuối kỳ", "Hàng tháng", "Hàng quý"]
    )

    interest_type = st.radio(
        "Loại lãi suất:",
        ["Lãi đơn", "Lãi kép (Lãi nhập gốc)"],
        help="Lãi kép chỉ áp dụng khi nhận lãi định kỳ (hàng tháng/hàng quý) và chọn tái nhập gốc vào kỳ tiếp theo."
    )

# 3. Thuật toán tính toán
def calculate_savings(principal, rate_year, months, payout_method, interest_type):
    rate_month = (rate_year / 100) / 12
    
    # Xác định số kỳ tính/nhận lãi
    if payout_method == "Hàng tháng":
        periods = months
        rate_per_period = rate_month
        period_name = "Tháng"
    elif payout_method == "Hàng quý":
        periods = months // 3
        rate_per_period = rate_month * 3
        period_name = "Quý"
    else:  # Cuối kỳ
        periods = 1
        rate_per_period = rate_month * months
        period_name = "Cuối kỳ"

    schedule = []
    current_balance = principal
    total_interest = 0

    if payout_method == "Cuối kỳ":
        # Với gửi cuối kỳ, Lãi đơn và Lãi kép thu về kết quả như nhau trong 1 kỳ hạn
        total_interest = principal * rate_per_period
        periodic_interest = total_interest
        schedule.append({
            "Kỳ": "Cuối kỳ",
            "Gốc đầu kỳ (VNĐ)": round(principal),
            "Tiền lãi (VNĐ)": round(total_interest),
            "Gốc + Lãi lũy kế (VNĐ)": round(principal + total_interest)
        })
    else:
        if periods == 0:
            st.error("⚠️ Kỳ hạn gửi phải lớn hơn hoặc bằng 3 tháng đối với hình thức nhận lãi 'Hàng quý'!")
            return 0, 0, 0, None, ""

        if interest_type == "Lãi đơn":
            # Lãi đơn: Lãi nhận định kỳ không nhập gốc
            periodic_interest = principal * rate_per_period
            total_interest = periodic_interest * periods
            for i in range(1, periods + 1):
                schedule.append({
                    f"Kỳ ({period_name})": i,
                    "Gốc cố định (VNĐ)": round(principal),
                    "Tiền lãi kỳ này (VNĐ)": round(periodic_interest),
                    "Tổng lãi tích lũy (VNĐ)": round(periodic_interest * i)
                })
        else:
            # Lãi kép: Lãi mỗi kỳ tự động nhập vào gốc để tính cho kỳ sau
            periodic_interest = 0  # Biến đổi theo từng kỳ
            for i in range(1, periods + 1):
                interest_this_period = current_balance * rate_per_period
                current_balance += interest_this_period
                total_interest += interest_this_period
                schedule.append({
                    f"Kỳ ({period_name})": i,
                    "Gốc đầu kỳ (VNĐ)": round(current_balance - interest_this_period),
                    "Tiền lãi kỳ này (VNĐ)": round(interest_this_period),
                    "Số dư cuối kỳ (VNĐ)": round(current_balance)
                })
            periodic_interest = total_interest / periods  # Trung bình mỗi kỳ

    total_amount = principal + total_interest
    df_schedule = pd.DataFrame(schedule)
    
    return periodic_interest, total_interest, total_amount, df_schedule, period_name

# 4. Hiển thị kết quả
st.divider()

periodic_interest, total_interest, total_amount, df_schedule, period_name = calculate_savings(
    principal, interest_rate, months, payout_method, interest_type
)

if df_schedule is not None:
    st.subheader("📊 Kết Quả Dự Tính Lãi")

    c1, c2, c3 = st.columns(3)
    
    with c1:
        if payout_method == "Cuối kỳ":
            st.metric("Lãi nhận cuối kỳ", f"{total_interest:,.0f} VNĐ")
        elif interest_type == "Lãi đơn":
            st.metric(f"Lãi nhận mỗi {period_name.lower()}", f"{periodic_interest:,.0f} VNĐ")
        else:
            st.metric(f"Lãi trung bình/{period_name.lower()}", f"{periodic_interest:,.0f} VNĐ")
            
    with c2:
        st.metric("Tổng tiền lãi", f"{total_interest:,.0f} VNĐ")
        
    with c3:
        st.metric("Tổng gốc + lãi nhận được", f"{total_amount:,.0f} VNĐ")

    # Hiển thị bảng chi tiết
    st.markdown("---")
    st.subheader("📅 Bảng chi tiết dòng tiền theo thời gian")
    st.dataframe(df_schedule, use_container_width=True)
