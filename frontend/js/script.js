/**
 * DentalAI - Main JavaScript File
 * Handles all interactive functionality
 */

// ===========================
// Mobile Menu Toggle
// ===========================
const menuToggle = document.getElementById('menuToggle');
const mainNav = document.getElementById('mainNav');

if (menuToggle && mainNav) {
    menuToggle.addEventListener('click', function() {
        mainNav.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        const isClickInside = menuToggle.contains(event.target) || mainNav.contains(event.target);
        if (!isClickInside && mainNav.classList.contains('active')) {
            mainNav.classList.remove('active');
        }
    });
}

// ===========================
// Smooth Scroll for Anchor Links
// ===========================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        
        // Don't prevent default for empty hash
        if (href === '#') return;
        
        e.preventDefault();
        const target = document.querySelector(href);
        
        if (target) {
            // Close mobile menu if open
            if (mainNav.classList.contains('active')) {
                mainNav.classList.remove('active');
            }
            
            // Smooth scroll to target
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===========================
// File Upload & Diagnosis Functionality
// ===========================
const uploadArea = document.getElementById('uploadArea');
const tabSelectFile = document.getElementById('tabSelectFile');
const tabCaptureImage = document.getElementById('tabCaptureImage');
const selectFileBtn = document.getElementById('selectFileBtn');
const fileInput = document.getElementById('fileInput');
const previewImage = document.getElementById('previewImage');
const placeholder = document.getElementById('placeholder');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
const analyzeBtn = document.getElementById('analyzeBtn');
const resetBtn = document.getElementById('resetBtn');
const cameraView = document.getElementById('cameraView');
const cameraStreamEl = document.getElementById('cameraStream');
const cameraCanvas = document.getElementById('cameraCanvas');
const captureBtn = document.getElementById('captureBtn');
const cancelCameraBtn = document.getElementById('cancelCameraBtn');

// Tab switching logic
if (tabSelectFile && tabCaptureImage && uploadArea && cameraView) {
    tabSelectFile.addEventListener('click', () => {
        tabSelectFile.classList.add('active');
        tabCaptureImage.classList.remove('active');
        uploadArea.classList.remove('hidden');
        cameraView.classList.add('hidden');
        stopCamera();
    });

    tabCaptureImage.addEventListener('click', () => {
        tabCaptureImage.classList.add('active');
        tabSelectFile.classList.remove('active');
        uploadArea.classList.add('hidden');
        cameraView.classList.remove('hidden');
        startCamera();
    });
}

// Click "Chọn từ thiết bị" button
if (selectFileBtn && fileInput) {
    selectFileBtn.addEventListener('click', function() {
        fileInput.click();
    });
}
if (uploadArea) {
    uploadArea.addEventListener('click', function(e) {
        if (e.target === uploadArea || e.target.tagName === 'H3' || e.target.tagName === 'P' || e.target.classList.contains('upload-icon')) {
            fileInput.click();
        }
    });
}

// Drag and drop functionality
if (uploadArea) {
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary-color)';
        uploadArea.style.background = 'var(--bg-light)';
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        uploadArea.style.background = '';
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.style.borderColor = '';
        uploadArea.style.background = '';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// File input change
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });
}

let currentFile = null;

// Handle file upload
function handleFile(file) {
    // Check if file is an image
    if (!file.type.startsWith('image/')) {
        alert('Vui lòng chọn file hình ảnh!');
        return;
    }

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('File quá lớn! Vui lòng chọn file nhỏ hơn 5MB.');
        return;
    }

    currentFile = file;

    // Read and display image
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        previewImage.classList.remove('hidden');
        uploadArea.classList.add('hidden');
        document.querySelector('.upload-tabs').classList.add('hidden');
        cameraView.classList.add('hidden');
        analyzeBtn.classList.remove('hidden');
        resetBtn.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}

// Add event listener for Analyze button
if (analyzeBtn) {
    analyzeBtn.addEventListener('click', () => performAnalysis(currentFile));
}

// Perform AI analysis by calling the backend API
function performAnalysis(file) {
    // Hide placeholder, show loading
    if (placeholder) placeholder.classList.add('hidden');
    if (loading) loading.classList.remove('hidden');
    if (result) result.classList.add('hidden');
    // Hide buttons during analysis
    if (analyzeBtn) analyzeBtn.classList.add('hidden');
    if (resetBtn) resetBtn.classList.add('hidden');

    const formData = new FormData();
    formData.append('image', file);
    
    // Store filename for later use
    const uploadedFileName = file.name;

    // API endpoint from your Flask server
    const apiUrl = 'http://127.0.0.1:5001/analyze';

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    fetch(apiUrl, {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeout);
        if (!response.ok) {
            if (response.status === 0) {
                throw new Error('Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng của bạn.');
            }
            // Handle server-side errors (like 500)
            throw new Error(`Lỗi server: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('=== API Response START ===');
            console.log('Full data:', JSON.stringify(data, null, 2));
            console.log('annotated_image:', data.annotated_image);
            console.log('cv_detections:', data.cv_detections);
            console.log('yolo_detections:', data.yolo_detections);
            console.log('=== API Response END ===');
            
            // Show Gemini analysis
            showResults(data.gemini_analysis || '');
            
            // Show image with CV or YOLO bounding boxes drawn on canvas
            const detectionsData = data.cv_detections || data.yolo_detections;
            
            console.log('Using detections:', detectionsData ? 'cv_detections or yolo_detections' : 'none');
            
            if (detectionsData && detectionsData.detections && detectionsData.detections.length > 0) {
                const annotatedSection = document.getElementById('annotated-image-section');
                const annotatedPreview = document.getElementById('annotated-preview');
                const canvas = document.getElementById('detection-canvas');
                
                if (!annotatedSection || !annotatedPreview || !canvas) {
                    console.error('❌ Missing DOM elements:', {annotatedSection, annotatedPreview, canvas});
                    return;
                }
                
                // Load original image and draw boxes on canvas
                const originalImageUrl = `http://127.0.0.1:5001/uploads/${uploadedFileName}?t=${Date.now()}`;
                
                console.log('📸 Loading image:', originalImageUrl);
                console.log('📊 Detections:', detectionsData.detections);
                
                const drawBoundingBoxes = () => {
                    // Setup canvas to match image display size
                    const rect = annotatedPreview.getBoundingClientRect();
                    canvas.width = rect.width;
                    canvas.height = rect.height;
                    canvas.style.width = rect.width + 'px';
                    canvas.style.height = rect.height + 'px';
                    
                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // Get image natural size
                    const naturalWidth = annotatedPreview.naturalWidth;
                    const naturalHeight = annotatedPreview.naturalHeight;
                    const scaleX = canvas.width / naturalWidth;
                    const scaleY = canvas.height / naturalHeight;
                    
                    console.log('🎨 Canvas setup:', {
                        canvasSize: [canvas.width, canvas.height],
                        imageNaturalSize: [naturalWidth, naturalHeight],
                        imageDisplaySize: [rect.width, rect.height],
                        scale: [scaleX, scaleY]
                    });
                    
                    // Color map for 7 classes - BRIGHT COLORS
                    const colors = {
                        'Data caries': '#FF0000',           // Bright Red
                        'Mouth Ulcer': '#FF00FF',           // Magenta
                        'Tooth Discoloration': '#00FFFF',   // Cyan
                        'hypodontia': '#FFA500',            // Orange
                        'Gingivitis': '#FF4500',            // Red-Orange
                        'Calculus': '#FFFF00',              // Yellow
                        'Caries_Gingivitus_ToothDiscoloration_Ulcer': '#FF00FF',  // Magenta
                        // CV detector classes
                        'Sâu răng': '#FF0000',              // Red
                        'Cao răng': '#FFFF00',              // Yellow
                        'Răng đổi màu': '#FFA500',          // Orange
                        'Viêm lợi': '#FF00FF',              // Magenta
                        'Răng khỏe mạnh': '#00FF00'         // Green
                    };
                    
                    // Draw each detection
                    detectionsData.detections.forEach((det, idx) => {
                        const bbox = det.bbox;
                        const x1 = Math.round(bbox.x1 * scaleX);
                        const y1 = Math.round(bbox.y1 * scaleY);
                        const x2 = Math.round(bbox.x2 * scaleX);
                        const y2 = Math.round(bbox.y2 * scaleY);
                        const width = x2 - x1;
                        const height = y2 - y1;
                        
                        console.log(`📦 Box ${idx + 1}: ${det.class_name}`, {
                            original: [bbox.x1, bbox.y1, bbox.x2, bbox.y2],
                            scaled: [x1, y1, x2, y2],
                            size: [width, height]
                        });
                        
                        const color = colors[det.class_name] || '#FF0000';
                        
                        // Draw VERY THICK RED RECTANGLE - 10px thick!
                        ctx.strokeStyle = '#FF0000';  // Pure red
                        ctx.lineWidth = 10;
                        ctx.strokeRect(x1, y1, width, height);
                        
                        // Draw another inner red rectangle for emphasis
                        ctx.strokeStyle = '#FF0000';
                        ctx.lineWidth = 6;
                        ctx.strokeRect(x1 + 5, y1 + 5, width - 10, height - 10);
                        
                        // Draw semi-transparent red fill
                        ctx.fillStyle = 'rgba(255, 0, 0, 0.15)';
                        ctx.fillRect(x1, y1, width, height);
                        
                        // Draw label with bright red background
                        const label = `${det.class_name} ${(det.confidence * 100).toFixed(1)}%`;
                        ctx.font = 'bold 20px Arial';
                        const textMetrics = ctx.measureText(label);
                        const textWidth = textMetrics.width;
                        const textHeight = 28;
                        
                        // Red background for label
                        ctx.fillStyle = '#FF0000';
                        ctx.fillRect(x1, Math.max(0, y1 - textHeight - 5), textWidth + 20, textHeight + 5);
                        
                        // White text with black outline
                        ctx.strokeStyle = '#000000';
                        ctx.lineWidth = 4;
                        ctx.strokeText(label, x1 + 10, Math.max(textHeight - 10, y1 - 10));
                        ctx.fillStyle = '#FFFFFF';
                        ctx.fillText(label, x1 + 10, Math.max(textHeight - 10, y1 - 10));
                    });
                    
                    console.log('✅ Bounding boxes drawn successfully!');
                };
                
                annotatedPreview.onload = function() {
                    console.log('✅ Image loaded');
                    // Wait a bit for layout to settle
                    setTimeout(drawBoundingBoxes, 100);
                };
                
                annotatedPreview.onerror = function() {
                    console.error('❌ Failed to load image:', originalImageUrl);
                };
                
                annotatedPreview.src = originalImageUrl;
                annotatedSection.classList.remove('hidden');
                
                // Redraw on window resize
                window.addEventListener('resize', drawBoundingBoxes);
                
                // Show detections summary (CV or YOLO)
                if (data.cv_detections) {
                    displayYOLODetections(data.cv_detections); // Reuse same display function
                } else if (data.yolo_detections) {
                    displayYOLODetections(data.yolo_detections);
                }
            } else {
                console.warn('⚠️ No detections to display');
            }
            
            // Show CNN prediction if available
            if (data.cnn_prediction) {
                displayCNNPrediction(data.cnn_prediction);
            }
            
            resetBtn.classList.remove('hidden'); // Show reset button after success
        } else {
            // Handle API-specific errors (e.g., invalid API key)
            throw new Error(data.error || 'Đã xảy ra lỗi không xác định.');
        }
    })
    .catch(error => {
        console.error('Error during analysis:', error);
        clearTimeout(timeout);
        
        // Display error to the user
        if (loading) loading.classList.add('hidden');
        if (placeholder) {
            placeholder.classList.remove('hidden');
            let errorMessage = error.message;
            
            if (error.name === 'AbortError') {
                errorMessage = 'Quá thời gian chờ phản hồi từ máy chủ. Vui lòng thử lại.';
            } else if (!navigator.onLine) {
                errorMessage = 'Không có kết nối mạng. Vui lòng kiểm tra kết nối internet của bạn.';
            }
            
            placeholder.innerHTML = `
                <div style="font-size: 4rem; margin-bottom: 1rem; color: var(--danger);">⚠️</div>
                <h4>Lỗi Phân Tích</h4>
                <p style="color: var(--text-gray);">${errorMessage}</p>
            `;
            resetBtn.classList.remove('hidden'); // Show reset button on error
        }
        
        // Show analyze button again to allow retry
        if (analyzeBtn) analyzeBtn.classList.remove('hidden');
        // Keep preview image visible to allow retry
        if (previewImage) previewImage.classList.remove('hidden');
    });
}

// Reset functionality
function resetDiagnosis() {
    currentFile = null;
    
    // Reset UI to initial state
    uploadArea.classList.remove('hidden');
    previewImage.classList.add('hidden');
    previewImage.src = '';
    
    // Hide annotated image section
    const annotatedSection = document.getElementById('annotated-image-section');
    const canvas = document.getElementById('detection-canvas');
    if (annotatedSection) {
        annotatedSection.classList.add('hidden');
    }
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    
    // Hide model summary cards
    const yoloSummary = document.getElementById('yolo-summary');
    const cnnSummary = document.getElementById('cnn-summary');
    if (yoloSummary) yoloSummary.classList.add('hidden');
    if (cnnSummary) cnnSummary.classList.add('hidden');
    
    placeholder.classList.remove('hidden');
    placeholder.innerHTML = `
        <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
        <p>Kết quả sẽ hiển thị tại đây</p>
    `;
    loading.classList.add('hidden');
    result.classList.add('hidden');
    
    analyzeBtn.classList.add('hidden');
    resetBtn.classList.add('hidden');
    
    // Stop camera if it's running
    stopCamera();

    // Restore tab UI
    document.querySelector('.upload-tabs').classList.remove('hidden');
    tabSelectFile.click(); // Go back to the file select tab
    cameraView.classList.add('hidden');

    // Reset file input to allow re-uploading the same file
    fileInput.value = '';
}

if (resetBtn) {
    resetBtn.addEventListener('click', resetDiagnosis);
}

// ===========================
// Camera Functionality
// ===========================
let stream = null;

async function startCamera() {
    try {
        // Kiểm tra hỗ trợ camera
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Trình duyệt của bạn không hỗ trợ truy cập camera.");
        }

        // Kiểm tra stream hiện tại
        if (stream) {
            stopCamera();
        }

        // Khởi tạo stream mới
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });

        // Gán stream cho video element
        cameraStreamEl.srcObject = stream;
        cameraStreamEl.play();
        
        // Hiển thị camera view
        if (cameraView) {
            cameraView.classList.remove('hidden');
            uploadArea.classList.add('hidden');
        }

    } catch (error) {
        console.error("Lỗi truy cập camera:", error);
        alert("Không thể truy cập camera. Vui lòng cấp quyền và thử lại.");
        // Quay lại tab upload file
        if (tabSelectFile) {
            tabSelectFile.click();
        }
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
        cameraStreamEl.srcObject = null;
    }
    cameraView.classList.add('hidden');
}

function captureImage() {
    const context = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraStreamEl.videoWidth;
    cameraCanvas.height = cameraStreamEl.videoHeight;
    // Flip the image back to normal before drawing
    context.translate(cameraCanvas.width, 0);
    context.scale(-1, 1);
    context.drawImage(cameraStreamEl, 0, 0, cameraCanvas.width, cameraCanvas.height);
    
    // Convert canvas to file
    cameraCanvas.toBlob(function(blob) {
        const imageFile = new File([blob], "capture.jpg", { type: "image/jpeg" });
        handleFile(imageFile);
        stopCamera();
    }, 'image/jpeg');
}

if (captureBtn) {
    captureBtn.addEventListener('click', captureImage);
}
if (cancelCameraBtn) {
    cancelCameraBtn.addEventListener('click', () => {
        stopCamera();
        // Switch back to the file upload tab
        tabSelectFile.click();
    });
}

// Show analysis results
function showResults(analysisText) {
    if (loading) loading.classList.add('hidden');
    if (result) result.classList.remove('hidden');
    
    // Parse the analysis text from the API
    const parsedResult = parseAnalysisText(analysisText);

    // Get elements to update
    const diagnosisTextEl = document.getElementById('diagnosis-text');
    const recommendationsListEl = document.getElementById('recommendations');
    const overviewStatusIconEl = document.getElementById('overview-status-icon');
    const findingsListEl = document.getElementById('findings-list');
    const confidenceSection = document.getElementById('confidence-section');
    const confidencePercentEl = document.getElementById('confidence-percent');
    const progressFillEl = document.getElementById('progress-fill');

    // Reset result area if parsing failed
    if (!parsedResult.overview && !parsedResult.findings.length && !parsedResult.recommendations.length) {
        diagnosisTextEl.textContent = "Không thể phân tích ảnh. Vui lòng thử lại với ảnh khác.";
        return;
    }

    // Update status icon and text based on overview content
    if (overviewStatusIconEl && parsedResult.overview) {
        const overviewText = parsedResult.overview.toLowerCase();
        const overviewTextEl = document.getElementById('overview-text');

        const isHealthy = /không có|không phát hiện|không thấy|bình thường|khỏe mạnh|ổn định/i.test(overviewText);
        const isAlarming = /nghiêm trọng|nặng|nhiều vấn đề|cần điều trị ngay/i.test(overviewText);
        const hasIssues = /viêm|sâu|cao răng|lệch|thưa|chen chúc|bất thường|cần chú ý/i.test(overviewText);
        const isMinor = /nhẹ|ít mảng bám|hơi ố vàng/i.test(overviewText);
        
        if (isAlarming) {
            overviewStatusIconEl.textContent = '🚨';
            overviewStatusIconEl.style.color = 'var(--danger)';
            overviewTextEl.textContent = 'Răng đang báo động';
        } else if (hasIssues && !isHealthy) {
            overviewStatusIconEl.textContent = '⚠️';
            overviewStatusIconEl.style.color = 'var(--warning)';
            overviewTextEl.textContent = 'Cần chú ý chăm sóc';
        } else if (isMinor && !isHealthy) {
            overviewStatusIconEl.textContent = '👍';
            overviewStatusIconEl.style.color = 'var(--primary-color)';
            overviewTextEl.textContent = 'Răng khá ổn';
        } else { // Default to healthy
            overviewStatusIconEl.textContent = '✅';
            overviewStatusIconEl.style.color = 'var(--success)';
            overviewTextEl.textContent = 'Tình trạng răng miệng tốt';
        }
    }

    // Update detailed overview text
    if (diagnosisTextEl && parsedResult.overview) {
        diagnosisTextEl.textContent = parsedResult.overview;
    }

    // Update Confidence Score
    if (confidenceSection && confidencePercentEl && progressFillEl && parsedResult.confidence) {
        const confidenceValue = parsedResult.confidence;
        confidencePercentEl.textContent = `${confidenceValue}%`;
        progressFillEl.style.width = `${confidenceValue}%`;
        confidenceSection.classList.remove('hidden');
    } else {
        if (confidenceSection) {
            confidenceSection.classList.add('hidden');
        }
    }

    // Update Findings with proper formatting
    if (findingsListEl) {
        if (parsedResult.findings.length > 0) {
            findingsListEl.innerHTML = parsedResult.findings
                .map(item => {
                    // Clean and format each finding item
                    const formattedItem = item
                        .replace(/^-\s*/, '')
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .trim();
                    
                    return formattedItem ? `<li>${formattedItem}</li>` : '';
                })
                .join('');
        } else {
            findingsListEl.innerHTML = `<li>Không có phát hiện đặc biệt.</li>`;
        }
    }

    // Update Recommendations with proper formatting
    if (recommendationsListEl) {
        if (parsedResult.recommendations.length > 0) {
            recommendationsListEl.innerHTML = parsedResult.recommendations
                .map(rec => {
                    const formattedRec = rec
                        .replace(/^-\s*/, '')
                        .replace(/\*\*(.*?)\*\*/g, '$1')
                        .trim();
                    
                    return formattedRec ? `
                        <li class="recommendation-item">
                            <span>${formattedRec}</span>
                        </li>
                    ` : '';
                })
                .join('');
        } else {
            recommendationsListEl.innerHTML = `
                <li class="recommendation-item">
                    <span>Duy trì vệ sinh răng miệng tốt và khám nha sĩ định kỳ.</span>
                </li>
            `;
        }
    }
}

/**
 * Parses the markdown-like text from Gemini into a structured object.
 * @param {string} text The raw text from the API.
 * @returns {object} An object with overview, findings, and recommendations.
 */
function parseAnalysisText(text) {
    const result = {
        confidence: null,
        overview: '',
        findings: [],
        recommendations: []
    };

    // Improved regex patterns for better parsing
    const confidenceMatch = text.match(/\*\*Độ tin cậy:\*\*\s*(\d+)/i);
    const overviewMatch = text.match(/\*\*Tổng quan:\*\*\s*\n*-?\s*([\s\S]*?)(?=\n\*\*Regions:\*\*|\n\*\*Phát hiện:\*\*|$)/i);
    const regionsMatch = text.match(/\*\*Regions:\*\*\s*\[([\s\S]*?)\]/i);
    const findingsMatch = text.match(/\*\*Phát hiện:\*\*\s*([\s\S]*?)(?=\*\*Khuyến nghị|$)/i);
    const recommendationsMatch = text.match(/\*\*Khuyến nghị:\*\*\s*([\s\S]*?)(?=\*\*Lưu ý|$)/i);

    if (confidenceMatch) result.confidence = parseInt(confidenceMatch[1], 10);
    
    if (overviewMatch && overviewMatch[1] && !overviewMatch[1].includes('**Độ tin cậy:**')) {
        result.overview = overviewMatch[1]
            .trim()
            .replace(/^-\s*/, '')
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .trim();
    }
    
    if (findingsMatch) {
        result.findings = findingsMatch[1]
            .trim()
            .split('\n')
            .map(line => line
                .trim()
                .replace(/^- /, '')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            )
            .filter(line => line && !line.includes('**Phát Hiện Chi Tiết**'));
    }
    
    if (recommendationsMatch) {
        result.recommendations = recommendationsMatch[1]
            .trim()
            .split('\n')
            .map(line => line
                .trim()
                .replace(/^- /, '')
                .replace(/\*\*(.*?)\*\*/g, '$1')
            )
            .filter(line => line && line.length > 5);
    }

    // Fallback if no structured data found
    if (!result.overview && text) {
        result.overview = text.split('\n')[0] || 'Không có thông tin tổng quan.';
    }

    return result;
}

// ===========================
// Display YOLO Detections
// ===========================
function displayYOLODetections(yoloData) {
    const findingsListEl = document.getElementById('findings-list');
    const yoloSummaryCard = document.getElementById('yolo-summary');
    const yoloResultEl = document.getElementById('yolo-result');
    
    const { num_detections, detections } = yoloData;
    
    if (num_detections === 0) return;
    
    // Show YOLO summary card
    if (yoloSummaryCard && yoloResultEl) {
        yoloSummaryCard.classList.remove('hidden');
        yoloResultEl.textContent = `${num_detections} vùng phát hiện`;
    }
    
    if (!findingsListEl) return;
    
    // Add YOLO detection summary at the top
    const yoloSummary = document.createElement('li');
    yoloSummary.innerHTML = `<strong>🎯 Phát hiện ${num_detections} vùng bệnh lý:</strong>`;
    yoloSummary.style.color = 'var(--primary-color)';
    yoloSummary.style.fontWeight = 'bold';
    yoloSummary.style.marginBottom = '10px';
    findingsListEl.insertBefore(yoloSummary, findingsListEl.firstChild);
    
    // Add each detection
    detections.forEach((det, idx) => {
        const detItem = document.createElement('li');
        const confidence = (det.confidence * 100).toFixed(1);
        
        // Shorten long class names for display
        let displayName = det.class_name;
        if (displayName === 'Caries_Gingivitus_ToothDiscoloration_Ulcer') {
            displayName = 'Nhiều bệnh lý';
        }
        
        detItem.innerHTML = `
            <strong>Vùng ${idx + 1}:</strong> ${displayName} 
            <span style="color: var(--success); font-weight: bold;">(${confidence}%)</span>
        `;
        detItem.style.marginLeft = '20px';
        findingsListEl.insertBefore(detItem, findingsListEl.children[idx + 1]);
    });
}

// ===========================
// Display CNN Prediction
// ===========================
function displayCNNPrediction(cnnData) {
    const confidenceSection = document.getElementById('confidence-section');
    const confidencePercentEl = document.getElementById('confidence-percent');
    const progressFillEl = document.getElementById('progress-fill');
    const cnnSummaryCard = document.getElementById('cnn-summary');
    const cnnResultEl = document.getElementById('cnn-result');
    
    if (!cnnData.predictions || cnnData.predictions.length === 0) return;
    
    // Get top prediction
    const topPred = cnnData.predictions[0];
    if (!topPred) return;
    
    const confidence = (topPred.confidence * 100).toFixed(1);
    
    // Show CNN summary card
    if (cnnSummaryCard && cnnResultEl) {
        cnnSummaryCard.classList.remove('hidden');
        cnnResultEl.textContent = topPred.class_name;
    }
    
    // Update confidence display
    if (confidenceSection && confidencePercentEl && progressFillEl) {
        confidencePercentEl.textContent = `${confidence}%`;
        progressFillEl.style.width = `${confidence}%`;
        confidenceSection.classList.remove('hidden');
    }
    
    // Add CNN prediction to findings
    const findingsListEl = document.getElementById('findings-list');
    if (findingsListEl) {
        const cnnItem = document.createElement('li');
        cnnItem.innerHTML = `
            <strong>🧠 Phân loại CNN:</strong> ${topPred.class_name} 
            <span style="color: var(--success); font-weight: bold;">(${confidence}%)</span>
        `;
        cnnItem.style.borderLeft = '3px solid var(--primary-color)';
        cnnItem.style.paddingLeft = '10px';
        cnnItem.style.marginTop = '15px';
        findingsListEl.appendChild(cnnItem);
    }
}

// ===========================
// Scroll animations
// ===========================
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

function handleScroll() {
    // Animate feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        if (isElementInViewport(card) && !card.classList.contains('animated')) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(function() {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.classList.add('animated');
            }, 100 * index);
        }
    });

    // Animate testimonial cards
    const testimonialCards = document.querySelectorAll('.testimonial-card');
    testimonialCards.forEach((card, index) => {
        if (isElementInViewport(card) && !card.classList.contains('animated')) {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(function() {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.classList.add('animated');
            }, 100 * index);
        }
    });
}

// Listen to scroll events
window.addEventListener('scroll', handleScroll);
window.addEventListener('load', handleScroll);

// ===========================
// Header scroll effect
// ===========================
let lastScroll = 0;
const header = document.getElementById('header');

window.addEventListener('scroll', function() {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 100) {
        header.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    } else {
        header.style.boxShadow = 'none';
    }
    
    lastScroll = currentScroll;
});

// ===========================
// Counter animation for stats
// ===========================
function animateCounter(element, target, suffix = '') {
    let current = 0;
    const increment = target / 50; // 50 steps
    const timer = setInterval(function() {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString() + suffix;
    }, 30);
}

// Trigger counter animation when stats section is visible
const statsSection = document.querySelector('.stats');
let statsAnimated = false;

function checkStatsInView() {
    if (statsSection && !statsAnimated && isElementInViewport(statsSection)) {
        statsAnimated = true;
        
        // Animate each stat
        const statNumbers = statsSection.querySelectorAll('.stat-number-large');
        statNumbers.forEach(stat => {
            const text = stat.textContent;
            const number = parseInt(text.replace(/[^0-9]/g, ''));
            const suffix = text.replace(/[0-9]/g, '');
            
            if (!isNaN(number)) {
                stat.textContent = '0' + suffix;
                setTimeout(function() {
                    animateCounter(stat, number, suffix);
                }, 200);
            }
        });
    }
}

window.addEventListener('scroll', checkStatsInView);
window.addEventListener('load', checkStatsInView);

// ===========================
// Console greeting
// ===========================
console.log('%c🦷 DentalAI ', 'font-size: 20px; font-weight: bold; color: #2563eb;');
console.log('%cChuẩn đoán sức khỏe răng miệng với AI', 'font-size: 12px; color: #6b7280;'); 
console.log('%cPhát triển bởi DentalAI Team', 'font-size: 10px; color: #9ca3af;');

// ===========================
// Prevent form submissions (demo purposes)
// ===========================
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        alert('Đây là demo. Chức năng này sẽ được kích hoạt sau khi tích hợp backend.');
    });
});

// ===========================
// Button click animations
// ===========================
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function(e) {
        // Create ripple effect
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255, 255, 255, 0.5)';
        ripple.style.transform = 'scale(0)';
        ripple.style.animation = 'ripple 0.6s ease-out';
        ripple.style.pointerEvents = 'none';
        
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        
        setTimeout(function() {
            ripple.remove();
        }, 600);
    });
});

// Add ripple animation to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===========================
// Lazy loading images
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(function(img) {
        imageObserver.observe(img);
    });
});

// ===========================
// Accessibility improvements
// ===========================
// Add skip to main content link
const skipLink = document.createElement('a');
skipLink.href = '#diagnosis';
skipLink.textContent = 'Bỏ qua đến nội dung chính';
skipLink.className = 'skip-link';
skipLink.style.cssText = `
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--primary-color);
    color: white;
    padding: 8px;
    text-decoration: none;
    z-index: 100;
`;
skipLink.addEventListener('focus', function() {
    this.style.top = '0';
});
skipLink.addEventListener('blur', function() {
    this.style.top = '-40px';
});
document.body.insertBefore(skipLink, document.body.firstChild);

console.log('✅ DentalAI initialized successfully!');