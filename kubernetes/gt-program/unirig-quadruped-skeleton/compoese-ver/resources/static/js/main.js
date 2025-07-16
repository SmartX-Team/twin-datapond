// DOM 요소들
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const uploadArea = document.querySelector('.upload-area');
const progress = document.getElementById('progress');
const result = document.getElementById('result');

// 파일명 업데이트 함수
function updateFileName() {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        fileName.textContent = `선택된 파일: ${file.name} (${formatFileSize(file.size)})`;
        fileName.style.display = 'block';
    } else {
        fileName.textContent = '';
        fileName.style.display = 'none';
    }
}

// 파일 크기 포맷팅
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 드래그 앤 드롭 기능
let dragCounter = 0;

uploadArea.addEventListener('dragenter', function(e) {
    e.preventDefault();
    dragCounter++;
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
        uploadArea.classList.remove('dragover');
        dragCounter = 0;
    }
});

uploadArea.addEventListener('dragover', function(e) {
    e.preventDefault();
});

uploadArea.addEventListener('drop', function(e) {
    e.preventDefault();
    dragCounter = 0;
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        updateFileName();
    }
});

// 파일 입력 변경 이벤트
fileInput.addEventListener('change', updateFileName);

// 결과 표시 함수
function showResult(type, title, message) {
    result.className = `result ${type}`;
    result.innerHTML = `
        <h3>${title}</h3>
        <p>${message}</p>
    `;
    result.style.display = 'block';
    
    // 결과 영역으로 스크롤
    result.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// 진행 상태 표시/숨김
function showProgress(show) {
    progress.style.display = show ? 'block' : 'none';
    if (show) {
        progress.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// 폼 제출 이벤트
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // 파일 선택 확인
    if (!fileInput.files.length) {
        showResult('error', '오류', '파일을 선택해주세요.');
        return;
    }
    
    const file = fileInput.files[0];
    const outputFormat = document.querySelector('[name="output_format"]').value;
    const highQuality = document.querySelector('[name="high_quality"]').checked;
    
    // 파일 크기 확인 (100MB 제한)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
        showResult('error', '파일 크기 오류', `파일 크기가 너무 큽니다. 최대 ${formatFileSize(maxSize)}까지 지원됩니다.`);
        return;
    }
    
    // FormData 생성
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);
    if (highQuality) {
        formData.append('high_quality', 'true');
    }
    
    // UI 상태 업데이트
    showProgress(true);
    result.style.display = 'none';
    
    // 시작 시간 기록
    const startTime = Date.now();
    
    try {
        // API 요청
        const response = await fetch('/rig/', {
            method: 'POST',
            body: formData
        });
        
        const endTime = Date.now();
        const processingTime = Math.round((endTime - startTime) / 1000);
        
        if (response.ok) {
            // 성공 - 파일 다운로드
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            
            a.href = url;
            a.download = `rigged_${file.name.split('.')[0]}.${outputFormat}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showResult('success', '완료!', 
                `리깅된 모델이 성공적으로 다운로드되었습니다. (처리 시간: ${processingTime}초)`);
        } else {
            // 오류 처리
            let errorMessage = '처리 중 오류가 발생했습니다.';
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (e) {
                // JSON 파싱 실패 시 기본 메시지 사용
                if (response.status === 408) {
                    errorMessage = '처리 시간이 초과되었습니다. 더 작은 모델을 시도해보세요.';
                } else if (response.status === 413) {
                    errorMessage = '파일 크기가 너무 큽니다.';
                } else if (response.status >= 500) {
                    errorMessage = '서버 내부 오류가 발생했습니다.';
                }
            }
            
            showResult('error', '오류', errorMessage);
        }
        
    } catch (error) {
        console.error('Request failed:', error);
        
        // 네트워크 오류 처리
        let errorMessage = '네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.';
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.';
        } else if (error.name === 'AbortError') {
            errorMessage = '요청이 취소되었습니다.';
        }
        
        showResult('error', '연결 오류', errorMessage);
        
    } finally {
        // 진행 상태 숨김
        showProgress(false);
    }
});

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 서비스 상태 확인
    checkServiceHealth();
    
    // 파일 입력 초기화
    fileInput.value = '';
    updateFileName();
});

// 서비스 헬스 체크
async function checkServiceHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('Service is healthy');
            
            // 모델 파일 상태 확인
            if (!data.default_model_available) {
                showResult('error', '모델 파일 없음', 
                    '기본 UniRig 모델 파일이 없습니다. 관리자에게 문의하거나 커스텀 모델을 업로드해주세요.');
            }
        } else {
            showResult('error', '서비스 오류', '서비스가 정상적으로 작동하지 않습니다.');
        }
    } catch (error) {
        console.warn('Health check failed:', error);
        // 헬스 체크 실패는 무시 (선택적)
    }
}

// 키보드 단축키
document.addEventListener('keydown', function(e) {
    // Ctrl+O 또는 Cmd+O로 파일 선택
    if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        fileInput.click();
    }
    
    // ESC로 진행 상태 숨김 (실제 요청은 취소되지 않음)
    if (e.key === 'Escape') {
        if (progress.style.display === 'block') {
            showProgress(false);
        }
    }
});

// 유틸리티 함수들
const utils = {
    // 파일 확장자 검증
    validateFileExtension: function(filename, allowedExtensions) {
        const ext = '.' + filename.split('.').pop().toLowerCase();
        return allowedExtensions.includes(ext);
    },
    
    // 로컬 스토리지에 설정 저장
    saveSettings: function() {
        const settings = {
            outputFormat: document.querySelector('[name="output_format"]').value,
            highQuality: document.querySelector('[name="high_quality"]').checked
        };
        localStorage.setItem('unirig_settings', JSON.stringify(settings));
    },
    
    // 로컬 스토리지에서 설정 로드
    loadSettings: function() {
        try {
            const saved = localStorage.getItem('unirig_settings');
            if (saved) {
                const settings = JSON.parse(saved);
                
                const outputFormat = document.querySelector('[name="output_format"]');
                const highQuality = document.querySelector('[name="high_quality"]');
                
                if (settings.outputFormat) {
                    outputFormat.value = settings.outputFormat;
                }
                if (settings.highQuality !== undefined) {
                    highQuality.checked = settings.highQuality;
                }
            }
        } catch (error) {
            console.warn('Failed to load settings:', error);
        }
    }
};

// 설정 변경 시 자동 저장
document.querySelector('[name="output_format"]').addEventListener('change', utils.saveSettings);
document.querySelector('[name="high_quality"]').addEventListener('change', utils.saveSettings);

// 페이지 로드 시 설정 복원
utils.loadSettings();

// 전역 오류 처리
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});