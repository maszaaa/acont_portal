// Konfigurasi API Backend
const API_BASE_URL = "http://localhost:8000";

// Icon definitions & UI logic (Toast, Sidebar, Password Toggle) tetap sama
const icons = {
  home:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  user:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  book:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
  clipboard:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M9 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-3"/></svg>',
  calendar:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  chart:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  trophy:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v6a5 5 0 0 1-10 0z"/><path d="M17 5h3a2 2 0 0 1-2 4h-1"/><path d="M7 5H4a2 2 0 0 0 2 4h1"/></svg>',
  shield:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  medal:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="15" r="6"/><path d="M9 10L6 2h4l2 5"/><path d="M15 10l3-8h-4l-2 5"/></svg>',
  check:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2"/><polyline points="9 12 11 14 16 9"/></svg>',
  logout:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
};
document.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML = icons[el.getAttribute('data-icon')] || ''; el.classList.add('shrink-0'); });

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  const bgClass = type === 'success' ? 'bg-navy-900' : type === 'error' ? 'bg-red-900' : 'bg-navy-800';
  const icon = type === 'success' ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>' : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
  toast.className = `flex items-center gap-3 px-5 py-4 rounded-xl shadow-float text-white text-[13px] font-semibold ${bgClass} toast-enter border border-white/10`;
  toast.innerHTML = `<div class="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center shrink-0">${icon}</div> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.classList.replace('toast-enter', 'toast-leave'); setTimeout(() => toast.remove(), 300); }, 3000);
}

function togglePassword() {
  const input = document.getElementById('password-input'), icon = document.getElementById('eye-icon');
  if (input.type === 'password') {
    input.type = 'text'; icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
  } else {
    input.type = 'password'; icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
  }
}

// LOGIC UTAMA: Integrasi Fetch API
document.getElementById('login-form').addEventListener('submit', async function(e) { 
  e.preventDefault(); 
  const btn = document.getElementById('btn-login');
  const npmVal = document.querySelector('input[type="text"]').value;
  const passVal = document.getElementById('password-input').value;

  btn.innerHTML = '<div class="spinner"></div><span class="ml-1 text-[13px] tracking-wide">MENARIK DATA CIVITAS...</span>';
  btn.classList.add('opacity-80', 'pointer-events-none');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ npm: npmVal, password: passVal })
    });

    if (!response.ok) throw new Error("Gagal login atau portal sedang sibuk.");
    const result = await response.json();
    
    // Inject Data API ke UI
    renderData(result.data);

    // Transisi UI
    document.getElementById('login-page').classList.add('hidden');
    document.getElementById('login-page').classList.remove('flex');
    document.getElementById('app-shell').classList.remove('hidden');
    document.getElementById('app-shell').classList.add('flex');
    showToast('Otentikasi & Sinkronisasi berhasil!');
    triggerProgressBars();

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.innerHTML = '<span>Masuk ke Portal</span>';
    btn.classList.remove('opacity-80', 'pointer-events-none');
  }
});

function renderData(data) {
  // 1. Identitas Global
  document.querySelectorAll('.font-extrabold.text-navy-900').forEach(el => {
    if(el.textContent.includes('Fatkhul')) el.textContent = data.identitas.nama || 'Mahasiswa PKN STAN';
  });
  document.querySelectorAll('.text-navy-400').forEach(el => {
    if(el.textContent.includes('413123')) el.textContent = data.identitas.npm || '-';
  });

  // 2. Data SIKU
  if(data.siku && data.siku.angka) {
    const sikuEls = document.querySelectorAll('.text-xl.font-extrabold.text-navy-900');
    if(sikuEls.length >= 4) {
      sikuEls[0].textContent = data.siku.sikap;
      sikuEls[1].textContent = data.siku.kehadiran;
      sikuEls[2].textContent = data.siku.tugas;
      sikuEls[3].textContent = data.siku.skp;
    }
    const akhirEl = document.querySelector('.text-xl.font-extrabold.text-gold-700');
    if(akhirEl) akhirEl.textContent = data.siku.angka;
    
    const dashSiku = document.querySelector('.text-2xl.md\\:text-3xl:nth-child(3)');
    if(dashSiku) dashSiku.textContent = data.siku.angka;
    
    const sikuBig = document.querySelector('.text-5xl.md\\:text-6xl');
    if(sikuBig) sikuBig.textContent = data.siku.angka;
    document.getElementById('siku-bar').style.width = `${data.siku.angka}%`;
  }

  // 3. Data Akademik
  if(data.akademik && data.akademik.mata_kuliah.length > 0) {
    document.getElementById('nilai-table-body').innerHTML = data.akademik.mata_kuliah.map((d,i) => `
      <tr class="hover:bg-navy-50/40 transition">
        <td class="py-3.5 pl-7 pr-3 text-[13px] text-navy-400 font-medium">${i+1}</td>
        <td class="py-3.5 px-3">
          <p class="text-[14px] font-bold text-navy-900">${d.mk}</p>
          <p class="text-[11px] font-semibold text-navy-400 mt-0.5">${d.kel} Kategori</p>
        </td>
        <td class="py-3.5 px-3 text-center text-[13px] font-medium text-navy-600">${d.sks}</td>
        <td class="py-3.5 px-3 text-center text-[13px] font-medium text-navy-600">${d.uts}</td>
        <td class="py-3.5 px-3 text-center text-[13px] font-medium text-navy-600">${d.uas}</td>
        <td class="py-3.5 px-3 text-center text-[13px] font-medium text-navy-600">${d.akt}</td>
        <td class="py-3.5 px-3 text-center text-[14px] font-extrabold text-navy-900">${d.angka}</td>
        <td class="py-3.5 px-3 text-center"><span class="px-2.5 py-1 rounded-md text-[11px] font-bold ${badgeClass(d.huruf)}">${d.huruf}</span></td>
        <td class="py-3.5 pr-7 pl-3 text-center text-[14px] font-extrabold text-navy-900">${d.indeks}</td>
      </tr>`).join('');
    
    document.querySelector('.text-2xl.font-extrabold.text-gold-400').textContent = data.akademik.ip_semester;
  }

  // 4. Data SKPM
  if(data.skpm_dash) {
    const totalPoin = data.skpm_dash.total_nilai || '0';
    document.querySelectorAll('.text-4xl.font-extrabold').forEach(el => {
      if(el.textContent.includes('205.5')) el.textContent = totalPoin;
      if(el.textContent.includes('20')) el.textContent = data.skpm_dash.total_kegiatan || '0';
    });

    const maxPoin = Math.max(...data.skpm_dash.rekap.map(d=>parseFloat(d.nilai) || 0));
    document.getElementById('skpm-chart').innerHTML = data.skpm_dash.rekap.map(d => `
      <div class="flex-1 flex flex-col items-center justify-end h-full gap-2 group cursor-pointer">
        <span class="text-[11px] font-bold text-navy-900 opacity-0 group-hover:opacity-100 transition-opacity -mb-1">${d.nilai}</span>
        <div class="w-full rounded-t-md bg-navy-200 chart-bar transition-all duration-1000 ease-out hover:bg-gold-400" 
             style="height: ${(parseFloat(d.nilai)/maxPoin*100)}%;"></div>
        <span class="text-[10px] font-semibold text-navy-400 mt-2 truncate w-full text-center">${d.periode}</span>
      </div>`).join('');

    document.getElementById('skpm-periode-list').innerHTML = data.skpm_dash.rekap.map(d => `
      <div class="flex items-center justify-between px-6 py-3.5 hover:bg-navy-50/40 transition">
        <span class="text-[13px] font-semibold text-navy-600">${d.periode}</span>
        <span class="text-[14px] font-extrabold text-navy-900">${d.nilai} <span class="text-[11px] font-medium text-navy-400 ml-0.5">pt</span></span>
      </div>`).join('');
  }

  if(data.skpm_detail && data.skpm_detail.length > 0) {
    document.getElementById('skpm-approved-list').innerHTML = data.skpm_detail.map(a => `
      <div class="px-7 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-navy-50/40 transition">
        <div>
          <p class="text-[10px] font-bold text-gold-600 uppercase tracking-widest">${a.lingkup}</p>
          <p class="text-[14px] font-bold text-navy-900 mt-1">${a.kegiatan}</p>
        </div>
        <div class="flex items-center gap-4 shrink-0">
          <span class="text-[15px] font-extrabold text-navy-900">${a.bobot}</span>
        </div>
      </div>`).join('');
  }
}

function badgeClass(h){
  if(h.startsWith('A')) return 'badge-A';
  if(h.startsWith('B')) return 'badge-B';
  if(h.startsWith('C')) return 'badge-C';
  return 'badge-D';
}

function doLogout(){
  document.getElementById('app-shell').classList.add('hidden');
  document.getElementById('app-shell').classList.remove('flex');
  document.getElementById('login-page').classList.remove('hidden');
  document.getElementById('login-page').classList.add('flex');
  document.getElementById('password-input').value = '';
}

// Sidebar logic & routing tabs dipertahankan seperti sebelumnya
let desktopCollapsed = false;
function toggleSidebar() {
  const sb = document.getElementById('sidebar'), overlay = document.getElementById('mobile-overlay');
  if (window.innerWidth < 768) { sb.classList.toggle('-translate-x-full'); overlay.classList.toggle('hidden');
  } else {
    desktopCollapsed = !desktopCollapsed;
    sb.classList.toggle('w-64'); sb.classList.toggle('w-[84px]');
    document.querySelectorAll('.nav-label, #sidebar-brand, .nav-group-title').forEach(el => el.classList.toggle('hidden', desktopCollapsed));
  }
}
const titles = {beranda: 'Beranda', profil: 'Profil Akademik', nilai: 'Hasil Studi', skpm: 'Sistem Kredit Poin', siku: 'Penilaian Karakter', ranking: 'Leaderboard', admin: 'Verifikasi BAAK', placeholder: 'Fitur'};
function showTab(id, el, placeholderName){
  if(window.innerWidth < 768) toggleSidebar();
  document.querySelectorAll('.tabpage').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  document.querySelectorAll('.sidebar-item').forEach(n => n.classList.remove('active'));
  if(el) el.classList.add('active');
  document.getElementById('topbar-title').textContent = id === 'placeholder' ? (placeholderName || 'Fitur') : titles[id];
  document.querySelector('main').scrollTo(0,0);
}
function triggerProgressBars() {} // Dummy function to replace old hardcoded UI triggers