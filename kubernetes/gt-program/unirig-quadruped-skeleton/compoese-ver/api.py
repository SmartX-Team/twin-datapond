import os
import subprocess
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# FastAPI 앱 초기화
app = FastAPI(
    title="UniRig Automatic Rigging Service",
    description="AI-powered automatic rigging for 3D models using UniRig",
    version="1.0.0"
)

# 경로 설정
BASE_DIR = Path("/app")
MODEL_DIR = BASE_DIR / "models"
UNIRIG_DIR = BASE_DIR / "unirig"
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "static"

# UniRig 관련 경로
INFERENCE_SCRIPT = UNIRIG_DIR / "inference.py"
DEFAULT_MODEL_PATH = MODEL_DIR / "unirig.pth"

# 서버 시작 시 필요한 폴더들 생성
for directory in [TEMP_DIR, STATIC_DIR, MODEL_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 지원되는 파일 확장자
SUPPORTED_INPUT_FORMATS = {".obj", ".ply", ".off"}
SUPPORTED_OUTPUT_FORMATS = {".glb", ".fbx", ".obj"}

@app.get("/", response_class=HTMLResponse)
async def main_page():
    """메인 페이지 - 웹 인터페이스 제공"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>UniRig Automatic Rigging Service</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }
            .upload-area:hover { border-color: #007bff; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .progress { display: none; margin: 20px 0; }
            .result { margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>UniRig Automatic Rigging Service</h1>
        <p>AI를 활용한 3D 모델 자동 리깅 서비스입니다. 정적 3D 모델을 업로드하면 자동으로 스켈레톤과 스키닝 웨이트가 적용된 애니메이션 준비 모델을 생성합니다.</p>
        
        <h2>모델 업로드</h2>
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <input type="file" id="fileInput" name="file" accept=".obj,.ply,.off" style="display: none;" onchange="updateFileName()">
                <p>클릭하여 3D 모델 파일을 선택하세요</p>
                <p><small>지원 형식: .obj, .ply, .off</small></p>
                <p id="fileName"></p>
            </div>
            
            <h3>설정</h3>
            <label>
                출력 형식:
                <select name="output_format">
                    <option value="glb">GLB (추천)</option>
                    <option value="fbx">FBX</option>
                    <option value="obj">OBJ</option>
                </select>
            </label>
            <br><br>
            
            <label>
                <input type="checkbox" name="high_quality" value="true"> 고품질 모드 (처리 시간 증가)
            </label>
            <br><br>
            
            <button type="submit">리깅 시작</button>
        </form>
        
        <div class="progress" id="progress">
            <h3>처리 중...</h3>
            <p>AI가 모델을 분석하고 스켈레톤을 생성하고 있습니다. 잠시만 기다려주세요.</p>
        </div>
        
        <div class="result" id="result"></div>
        
        <h2>사용법</h2>
        <ol>
            <li>3D 모델 파일(.obj, .ply, .off)을 업로드합니다</li>
            <li>출력 형식과 품질을 선택합니다</li>
            <li>처리가 완료되면 리깅된 모델을 다운로드합니다</li>
        </ol>
        
        <h2>API 사용법</h2>
        <pre>
# curl을 사용한 예시
curl -X POST "http://localhost:8000/rig/" \\
     -F "file=@your_model.obj" \\
     -F "output_format=glb" \\
     --output rigged_model.glb
        </pre>
        
        <script>
            function updateFileName() {
                const input = document.getElementById('fileInput');
                const fileName = document.getElementById('fileName');
                if (input.files.length > 0) {
                    fileName.textContent = `선택된 파일: ${input.files[0].name}`;
                }
            }
            
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData();
                const fileInput = document.getElementById('fileInput');
                const outputFormat = document.querySelector('[name="output_format"]').value;
                const highQuality = document.querySelector('[name="high_quality"]').checked;
                
                if (!fileInput.files.length) {
                    alert('파일을 선택해주세요.');
                    return;
                }
                
                formData.append('file', fileInput.files[0]);
                formData.append('output_format', outputFormat);
                if (highQuality) formData.append('high_quality', 'true');
                
                document.getElementById('progress').style.display = 'block';
                document.getElementById('result').innerHTML = '';
                
                try {
                    const response = await fetch('/rig/', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `rigged_${fileInput.files[0].name.split('.')[0]}.${outputFormat}`;
                        a.click();
                        
                        document.getElementById('result').innerHTML = `
                            <h3>완료!</h3>
                            <p>리깅된 모델이 다운로드되었습니다.</p>
                        `;
                    } else {
                        const error = await response.json();
                        throw new Error(error.detail || '처리 중 오류가 발생했습니다.');
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `
                        <h3>오류</h3>
                        <p>${error.message}</p>
                    `;
                } finally {
                    document.getElementById('progress').style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/rig/")
async def rig_model(
    file: UploadFile = File(...),
    output_format: str = Form("glb"),
    high_quality: Optional[str] = Form(None),
    custom_model: Optional[UploadFile] = File(None)
):
    """
    3D 모델 자동 리깅 API
    
    Args:
        file: 리깅할 3D 모델 파일 (.obj, .ply, .off)
        output_format: 출력 형식 (glb, fbx, obj)
        high_quality: 고품질 모드 활성화 여부
        custom_model: 사용자 커스텀 UniRig 모델 가중치 (선택사항)
    
    Returns:
        리깅된 3D 모델 파일
    """
    
    # 입력 파일 형식 검증
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_INPUT_FORMATS:
        raise HTTPException(
            status_code=400, 
            detail=f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(SUPPORTED_INPUT_FORMATS)}"
        )
    
    # 출력 형식 검증
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        output_format = "glb"  # 기본값으로 설정
    
    # 고유한 작업 ID 생성
    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(parents=True)
    
    try:
        # 1. 입력 파일 저장
        input_path = job_dir / file.filename
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 커스텀 모델이 제공된 경우 처리
        model_path = DEFAULT_MODEL_PATH
        if custom_model and custom_model.filename:
            custom_model_path = job_dir / "custom_model.pth"
            with open(custom_model_path, "wb") as buffer:
                shutil.copyfileobj(custom_model.file, buffer)
            model_path = custom_model_path
        
        # 3. UniRig 명령어 구성
        command = [
            "python", str(INFERENCE_SCRIPT),
            "--mesh_path", str(input_path),
            "--ckpt_path", str(model_path),
            "--save_dir", str(job_dir),
            "--output_format", output_format
        ]
        
        # 고품질 모드 옵션 추가
        if high_quality:
            command.extend(["--high_quality", "true"])
        
        print(f"UniRig 실행: {' '.join(command)}")
        
        # 4. UniRig 실행
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        print(f"UniRig 실행 완료")
        if result.stdout:
            print(f"출력: {result.stdout}")
        
        # 5. 결과 파일 찾기
        output_filename = f"{Path(file.filename).stem}_rigged.{output_format}"
        output_path = job_dir / output_filename
        
        # 다양한 가능한 출력 파일명 시도
        possible_outputs = [
            job_dir / output_filename,
            job_dir / f"{Path(file.filename).stem}.{output_format}",
            job_dir / f"rigged.{output_format}",
            job_dir / f"output.{output_format}"
        ]
        
        actual_output_path = None
        for path in possible_outputs:
            if path.exists():
                actual_output_path = path
                break
        
        if not actual_output_path:
            # 디렉토리의 모든 파일 나열해서 디버깅
            files = list(job_dir.glob("*"))
            print(f"출력 파일을 찾을 수 없습니다. 디렉토리 내용: {files}")
            raise HTTPException(
                status_code=500, 
                detail="리깅 처리는 완료되었지만 출력 파일을 찾을 수 없습니다."
            )
        
        # 6. 결과 파일 반환
        media_type_map = {
            "glb": "model/gltf-binary",
            "fbx": "application/octet-stream", 
            "obj": "text/plain"
        }
        
        return FileResponse(
            path=str(actual_output_path),
            media_type=media_type_map.get(output_format, "application/octet-stream"),
            filename=output_filename
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="처리 시간이 초과되었습니다. 더 작은 모델을 시도해보세요.")
    except subprocess.CalledProcessError as e:
        print(f"UniRig 실행 오류: {e.stderr}")
        raise HTTPException(
            status_code=500, 
            detail=f"리깅 처리 중 오류가 발생했습니다: {e.stderr}"
        )
    except Exception as e:
        print(f"예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
    
    finally:
        # 임시 파일 정리 (선택적)
        # shutil.rmtree(job_dir, ignore_errors=True)
        pass

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "unirig_available": INFERENCE_SCRIPT.exists(),
        "default_model_available": DEFAULT_MODEL_PATH.exists()
    }

@app.get("/info")
async def service_info():
    """서비스 정보"""
    return {
        "service": "UniRig Automatic Rigging",
        "version": "1.0.0",
        "supported_input_formats": list(SUPPORTED_INPUT_FORMATS),
        "supported_output_formats": list(SUPPORTED_OUTPUT_FORMATS),
        "features": [
            "AI-powered automatic rigging",
            "Custom model upload support", 
            "Multiple output formats",
            "High quality mode",
            "Web interface"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)