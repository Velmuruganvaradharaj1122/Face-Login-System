let video = null;
let canvas = null;
let stream = null;
let capturedImage = null;

function setupCameraCommon(onReadyCallback = null) {
    video = document.getElementById('webcam');
    canvas = document.getElementById('canvas');
    const startCameraBtn = document.getElementById('startCamera');

    startCameraBtn.addEventListener('click', async () => {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
            video.srcObject = stream;
            
            // Mirror the video display so right hand appears on the right (natural selfie mirror)
            video.style.transform = 'scaleX(-1)';
            
            // Enable specific buttons depending on context
            const capBtn = document.getElementById('captureFace');
            const loginBtn = document.getElementById('loginBtn');
            if (capBtn) capBtn.disabled = false;
            if (loginBtn) loginBtn.disabled = false;
            
            startCameraBtn.classList.replace('btn-secondary', 'btn-success');
            startCameraBtn.innerHTML = '<i class="fas fa-camera"></i> Camera Active';
            startCameraBtn.disabled = true;
            
            if (onReadyCallback) onReadyCallback();
            
        } catch (err) {
            showMessage("Error accessing camera: " + err.message, "danger");
        }
    });
}

function captureSnapshot() {
    if (!stream) return null;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // Flip horizontally so the captured image matches what the user sees on screen.
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    
    // Reset transform so future draws on this canvas are not affected
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    
    return canvas.toDataURL('image/jpeg');
}

function showMessage(msg, type) {
    const box = document.getElementById('messageBox');
    
    // Determine Tailwind colors based on type
    let colorClasses = '';
    if (type === 'danger') {
        colorClasses = 'bg-red-500/20 text-red-400 border border-red-500/50';
    } else if (type === 'success') {
        colorClasses = 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50';
    } else if (type === 'warning') {
        colorClasses = 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50';
    } else {
        colorClasses = 'bg-blue-500/20 text-blue-400 border border-blue-500/50';
    }
    
    // Replace all classes on the box, but keep the base layout ones
    box.className = `mt-4 p-4 rounded-lg font-medium text-center ${colorClasses}`;
    box.textContent = msg;
    box.classList.remove('hidden');
}

function initRegistrationFlow() {
    setupCameraCommon();
    
    const captureFaceBtn = document.getElementById('captureFace');
    const submitBtn = document.getElementById('submitBtn');
    const form = document.getElementById('registrationForm');
    
    captureFaceBtn.addEventListener('click', () => {
        capturedImage = captureSnapshot();
        if (capturedImage) {
            // Hide video stream and show captured image preview
            const videoEl = document.getElementById('webcam');
            const previewEl = document.getElementById('previewImage');
            
            videoEl.classList.add('hidden');
            previewEl.src = capturedImage;
            previewEl.classList.remove('hidden');
            
            // Swap buttons
            captureFaceBtn.classList.add('hidden');
            const retakeBtn = document.getElementById('retakeFace');
            if (retakeBtn) retakeBtn.classList.remove('hidden');
            
            document.getElementById('captureStatus').classList.remove('hidden');
            submitBtn.disabled = false;
        }
    });
    
    const retakeBtn = document.getElementById('retakeFace');
    if (retakeBtn) {
        retakeBtn.addEventListener('click', () => {
            // Clear captured image
            capturedImage = null;
            
            // Swap preview back to video stream
            const videoEl = document.getElementById('webcam');
            const previewEl = document.getElementById('previewImage');
            
            previewEl.classList.add('hidden');
            previewEl.src = "";
            videoEl.classList.remove('hidden');
            
            // Swap buttons
            retakeBtn.classList.add('hidden');
            captureFaceBtn.classList.remove('hidden');
            
            document.getElementById('captureStatus').classList.add('hidden');
            submitBtn.disabled = true;
        });
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!capturedImage) {
            showMessage("Please capture your face first.", "warning");
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...';
        
        const payload = {
            employee_id: document.getElementById('employeeId').value,
            full_name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            image: capturedImage
        };
        
        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await res.json();
            
            if (res.ok && data.success) {
                showMessage(data.message, "success");
                setTimeout(() => window.location.href = '/login', 2000);
            } else {
                showMessage(data.message || "Registration failed", "danger");
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-user-check me-2"></i> Register Employee';
            }
        } catch (err) {
            showMessage("Network error.", "danger");
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-user-check me-2"></i> Register Employee';
        }
    });
}

let countdownTimer;

function startAutoCaptureCountdown() {
    const overlay = document.getElementById('countdownOverlay');
    const ring = document.getElementById('countdownRing');
    const text = document.getElementById('countdownText');
    
    overlay.classList.remove('hidden');
    let timeLeft = 3;
    
    // SVG circle has length 264
    ring.style.strokeDashoffset = '0';
    text.innerText = timeLeft;
    
    countdownTimer = setInterval(() => {
        timeLeft--;
        if (timeLeft > 0) {
            text.innerText = timeLeft;
            ring.style.strokeDashoffset = (264 / 3) * (3 - timeLeft);
        } else {
            clearInterval(countdownTimer);
            overlay.classList.add('hidden');
            ring.style.strokeDashoffset = '0'; // reset
            triggerLogin();
        }
    }, 1000);
}

async function triggerLogin() {
    const loginBtn = document.getElementById('loginBtn');
    const spinner = document.getElementById('loginSpinner');
    
    capturedImage = captureSnapshot();
    if (!capturedImage) return;
    
    spinner.classList.remove('hidden');
    document.getElementById('messageBox').classList.add('hidden');
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: capturedImage })
            });
            
            // Safely parse JSON — server may return empty body on some errors
            let data = {};
            try {
                data = await res.json();
            } catch (_) {
                data = { success: false, message: "Server error (no response body). Check Flask logs." };
            }
            
            if (data.success) {
                showMessage(data.message || "Login successful!", "success");
                // Use redirect field from server — admin → /admin/dashboard, user → /dashboard
                const dest = data.redirect || '/dashboard';
                setTimeout(() => window.location.href = dest, 1000);
            } else {
                showMessage(data.message || "Face not recognised. Please try again.", "danger");
                // Retry after 2 seconds
                setTimeout(() => {
                    document.getElementById('messageBox').classList.add('hidden');
                    startAutoCaptureCountdown();
                }, 2000);
            }
        } catch (err) {
            showMessage("Network error: " + err.message, "danger");
            setTimeout(() => {
                document.getElementById('messageBox').classList.add('hidden');
                startAutoCaptureCountdown();
            }, 2000);
        } finally {
        spinner.classList.add('hidden');
    }
}

function initLoginFlow() {
    setupCameraCommon(() => {
        // Hide the start camera button completely
        document.getElementById('startCamera').classList.add('hidden');
        // Start countdown
        startAutoCaptureCountdown();
    });
}
