// UI Components và Utilities

// Tạo login modal HTML
function createLoginModal() {
  return `
    <div id="login-modal" style="display: none;">
      <div class="login-box">
        <h2>Đăng nhập</h2>
        <div class="login-form-group">
          <label for="login-username">Tên đăng nhập:</label>
          <input 
            type="text" 
            id="login-username" 
            placeholder="nguoidung1" 
            autocomplete="username"
          />
        </div>
        <div class="login-form-group">
          <label for="login-password">Mật khẩu:</label>
          <input 
            type="password" 
            id="login-password" 
            placeholder="1234" 
            autocomplete="current-password"
          />
        </div>
        <button id="login-submit" class="primary login-submit">
          Đăng nhập
        </button>
        <div id="login-error" class="err" style="margin-top: 16px; display: none;"></div>
      </div>
    </div>
  `;
}

// Format số tiền VND
function toVND(x) {
  return (x || 0).toLocaleString("vi-VN") + "₫";
}

// Tạo HTML cho itinerary
function itineraryToHTML(data) {
  if (!data || !Array.isArray(data.itinerary)) {
    return `<div class="err">Kết quả không hợp lệ.</div>`;
  }
  
  let head = `
    <div class="kv">
      <span>Tổng chi phí: <b>${toVND(data.total_cost_estimate)}</b></span>
      <span>~ ${toVND(data.per_day_budget)}/ngày</span>
      <span>Số ngày: ${data.days}</span>
    </div>
  `;
  
  let daysHTML = data.itinerary
    .map((d, idx) => `
      <details class="day" ${data.itinerary.length <= 3 ? "open" : ""} style="animation-delay: ${idx * 0.1}s">
        <summary>
          Ngày ${d.day} — Tổng: <b>${toVND(d.day_cost_estimate)}</b> ${
            d.over_budget ? '<span class="err" style="display: inline; padding: 2px 8px; border-radius: 8px; font-size: 12px;">(vượt ngân sách)</span>' : ""
          }
        </summary>
        <table>
          <tr>
            <th>Buổi</th>
            <th>Địa điểm</th>
            <th>Chi phí</th>
            <th>Giờ mở</th>
            <th>Đánh giá</th>
          </tr>
          ${row("Sáng", d.morning)}
          ${row("Trưa", d.lunch)}
          ${row("Chiều", d.afternoon)}
          ${row("Khách sạn", d.hotel)}
        </table>
      </details>
    `)
    .join("");
  
  return head + daysHTML;
}

function row(label, p) {
  if (!p) {
    return `<tr><td>${label}</td><td colspan="4"><span class="err" style="display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 12px;">Không có gợi ý phù hợp</span></td></tr>`;
  }
  return `<tr>
    <td><strong>${label}</strong></td>
    <td>
      <b>${p.name}</b>
      <div class="meta">${p.city} · ${p.category}</div>
    </td>
    <td>${toVND(p.avg_cost)}</td>
    <td>${p.open_time || "-"}–${p.close_time || "-"}</td>
    <td>${(p.rating || 0).toFixed(2)} ⭐</td>
  </tr>`;
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    createLoginModal,
    toVND,
    itineraryToHTML,
    row
  };
}

