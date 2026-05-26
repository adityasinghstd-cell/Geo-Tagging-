// ==========================================
// 1. SETUP THE "SELL" MAP
// ==========================================
const sellMap = L.map('sellMap').setView([28.4744, 77.5040], 13);
L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
    maxZoom: 20, attribution: '&copy; OpenStreetMap'
}).addTo(sellMap);

const sellMarker = L.marker([28.4744, 77.5040], { draggable: true }).addTo(sellMap);

sellMarker.on('dragend', function(e) {
    const position = sellMarker.getLatLng();
    document.getElementById('sell_lat').value = position.lat;
    document.getElementById('sell_lng').value = position.lng;
    sellMap.panTo(position);
});

// ==========================================
// 2. SETUP THE "BUY" MAP & DYNAMIC MARKETPLACE
// ==========================================
const buyMap = L.map('buyMap').setView([28.4744, 77.5040], 12);
L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
    maxZoom: 20, attribution: '&copy; OpenStreetMap'
}).addTo(buyMap);

// Fix Leaflet sizing bug when a map starts inside a hidden Bootstrap tab
document.getElementById('buy-tab').addEventListener('shown.bs.tab', function () {
    buyMap.invalidateSize();
});

// Layer group to manage map pins so we can clear them when refreshing
const markersLayer = new L.LayerGroup().addTo(buyMap);

// NEW: Fetch data dynamically from the CSV database!
async function renderMarketplace() {
    try {
        const response = await fetch('http://127.0.0.1:5000/get-all-listings');
        const result = await response.json();
        
        const listContainer = document.getElementById('marketplaceList');
        listContainer.innerHTML = ''; // Clear current list
        markersLayer.clearLayers(); // Clear old map pins

        if (result.status === 'success') {
            const lands = result.data;
            
            if (lands.length === 0) {
                listContainer.innerHTML = '<p class="text-muted mt-3 text-center">No lands available in the marketplace currently.</p>';
                return;
            }

            lands.forEach(land => {
                // 1. Add a pin to the Buy Map
                L.marker([land.Lat, land.Lng])
                    .addTo(markersLayer)
                    .bindPopup(`<b>${land.Acres} Acres</b><br>Asking: ₹${land.Expected_Price_Cr} Cr`);

                // 2. Create the HTML card
                const card = `
                    <div class="listing-card">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h5 class="mb-0 text-dark">${land.Acres} Acres Plot</h5>
                            <span class="badge bg-success">₹ ${land.Expected_Price_Cr} Cr</span>
                        </div>
                        <p class="small text-muted mb-2">📍 GeoTagged Verified Location</p>
                        
                        <button class="btn btn-outline-success btn-sm w-100" onclick="alert('Contacting Farmer: ${land.Mobile}')">Contact Farmer</button>
                    </div>
                `;
                listContainer.innerHTML += card;
            });
        }
    } catch (error) {
        console.error("Failed to load marketplace data:", error);
    }
}

// Render the marketplace immediately when the page loads
renderMarketplace();


// ==========================================
// 3. HANDLE NEW LISTING SUBMISSION (AI EVALUATION + CSV SAVE)
// ==========================================
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault(); 
    
    const farmerMobile = document.getElementById('mobile').value; 
    const acres = parseFloat(document.getElementById('acres').value);
    const expectedPrice = parseFloat(document.getElementById('price_cr').value);
    const lat = parseFloat(document.getElementById('sell_lat').value);
    const lng = parseFloat(document.getElementById('sell_lng').value);
    
    try {
        // STEP A: Get AI Prediction
        const predictRes = await fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ Acres: acres, Expected_Price_Cr: expectedPrice, Lat: lat, Lng: lng })
        });
        const predictData = await predictRes.json();
        
        if (predictData.status === 'success') {
            const aiValue = predictData.predicted_price;
            
            // Show UI updates
            document.getElementById('resultBox').style.display = 'block';
            document.getElementById('priceText').innerText = '₹ ' + aiValue + ' Cr';
            let analysis = expectedPrice < aiValue ? "🚨 Your asking price is below market value." : (expectedPrice > aiValue * 1.2 ? "⚠️ Your asking price is high." : "✅ Your asking price aligns perfectly with current trends.");
            document.getElementById('marketAnalysis').innerText = analysis;

            // STEP B: Automatically save this new listing to the CSV!
            await fetch('http://127.0.0.1:5000/add-listing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    Mobile: farmerMobile,
                    Acres: acres,
                    Expected_Price_Cr: expectedPrice,
                    AI_Value_Cr: aiValue,
                    Lat: lat,
                    Lng: lng
                })
            });

            // Re-render the marketplace so the new land appears in the Buy Tab instantly
            renderMarketplace();
        } else {
            alert('Error from AI server: ' + predictData.message);
        }
    } catch (error) {
        alert('Failed to connect to the server. Is Flask running?');
        console.error(error);
    }
});


// ==========================================
// 4. OTP LOGIN FORM LOGIC & DASHBOARD REDIRECT
// ==========================================
const btnSendOtp = document.getElementById('btnSendOtp');
const otpForm = document.getElementById('otpForm');

btnSendOtp.addEventListener('click', async function() {
    const mobile = document.getElementById('loginMobile').value;
    if(!mobile || mobile.length < 10) return alert("Please enter a valid mobile number.");

    btnSendOtp.innerText = "Sending..."; btnSendOtp.disabled = true;

    try {
        const response = await fetch('http://127.0.0.1:5000/send-otp', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mobile: mobile })
        });
        const data = await response.json();
        if(data.status === 'success') {
            document.getElementById('step1').style.display = 'none';
            document.getElementById('step2').style.display = 'block';
        } else {
            alert(data.message); btnSendOtp.innerText = "Get OTP"; btnSendOtp.disabled = false;
        }
    } catch(err) {
        alert("Server error."); btnSendOtp.innerText = "Get OTP"; btnSendOtp.disabled = false;
    }
});

otpForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const mobile = document.getElementById('loginMobile').value;
    const otp = document.getElementById('loginOtp').value;
    const role = document.querySelector('input[name="userRole"]:checked').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mobile: mobile, otp: otp, role: role })
        });
        const data = await response.json();
        
        if(data.status === 'success') {
            // WE MUST USE THESE STANDARD KEYS
            localStorage.setItem('agri_user_mobile', mobile);
            localStorage.setItem('agri_user_role', role);
            window.location.href = data.redirect_url;
        } else {
            alert(data.message);
        }
    } catch(err) {
        alert("Login failed. Is the Flask server running?");
    }
});

function resetOtpForm() {
    document.getElementById('step1').style.display = 'block';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('loginMobile').value = '';
    document.getElementById('loginOtp').value = '';
    document.getElementById('btnSendOtp').innerText = "Get OTP";
    document.getElementById('btnSendOtp').disabled = false;
    document.getElementById('btnVerifyOtp').innerText = "Verify & Login";
    document.getElementById('btnVerifyOtp').disabled = false;
}